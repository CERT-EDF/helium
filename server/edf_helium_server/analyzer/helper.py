"""Analyzer Helper"""

from collections.abc import AsyncIterator
from re import compile as regexp
from uuid import UUID

from edf_fusion.concept import AnalyzerInfo
from edf_fusion.helper.logging import get_logger
from edf_fusion.helper.redis import Redis, create_redis_lock
from edf_fusion.helper.zip import extract_zip
from edf_helium_core.concept import Analysis, Case, Collection, Status
from generaptor.concept import Outcome

from ..storage import CollectionStorage, Storage

_LOGGER = get_logger('server.analyzer.helper', root='helium')
_NAME_PATTERN = regexp(r'([a-z]+_)*[a-z]+')
_VERSION_PATTERN = regexp(r'\d+(\.\d+){2}')


def check_analyzer_info(info: AnalyzerInfo) -> bool:
    """Determine if name and version are valid"""
    if not _NAME_PATTERN.fullmatch(info.name):
        _LOGGER.critical("invalid analyzer name: '%s'", info.name)
        return False
    if not _VERSION_PATTERN.fullmatch(info.version):
        _LOGGER.critical("invalid analyzer version: '%s'", info.version)
        return False
    return True


async def find_analyses(
    storage: Storage, analyzer: str
) -> AsyncIterator[Case, Collection, Analysis]:
    """Find all analyzer analyses in storage"""
    async for case in storage.enumerate_cases():
        if case.closed:
            continue
        async for collection in storage.enumerate_collections(case.guid):
            a_storage = storage.analysis_storage(
                case.guid, collection.guid, analyzer
            )
            if not a_storage.metadata.is_file():
                continue
            analysis = await storage.retrieve_analysis(
                case.guid, collection.guid, analyzer
            )
            yield case, collection, analysis


async def find_pending_analyses(
    storage: Storage, analyzer: str
) -> AsyncIterator[Case, Collection, Analysis]:
    """Find pending analyzer analyses in storage"""
    async for case, collection, analysis in find_analyses(storage, analyzer):
        if analysis.status != Status.PENDING:
            continue
        yield case, collection, analysis


async def perform_analyses_recovery(storage: Storage, analyzer: str) -> int:
    """Perform analysis recovery when service was stopped while ananyzing"""
    recovered = 0
    async for case, collection, analysis in find_analyses(storage, analyzer):
        if analysis.completed:
            continue
        if analysis.status == Status.PENDING:
            continue
        await storage.update_analysis(
            case.guid,
            collection.guid,
            analysis.analyzer,
            {'status': Status.PENDING.value},
        )
        recovered += 1
    return recovered


async def _extract_simple_zip(
    collection_storage: CollectionStorage,
) -> Outcome:
    extract_zip(collection_storage.data, collection_storage.data_dir)
    try:
        next(collection_storage.data_dir.iterdir())
    except (StopIteration, OSError):
        _LOGGER.error("empty simple zip or extraction failure")
        return Outcome.FAILURE
    return Outcome.SUCCESS


async def _extract_generaptor_zip(
    storage: Storage,
    case_guid: UUID,
    collection: Collection,
    collection_storage: CollectionStorage,
) -> Outcome:
    # find matching collector
    collector_guid = None
    async for collector in storage.enumerate_collectors(case_guid):
        if collector.fingerprint != collection.fingerprint:
            continue
        collector_guid = collector.guid
    if not collector_guid:
        _LOGGER.error(
            "cannot find a collector matching collection fingerprint %s",
            collection.fingerprint,
        )
        return Outcome.FAILURE
    # retrieve collector secrets
    collector_secrets = await storage.retrieve_collector_secrets(
        case_guid, collector_guid
    )
    if not collector_secrets:
        _LOGGER.error(
            "failed to retrieve collector (%s) secrets", collector_guid
        )
        return Outcome.FAILURE
    # extract collection
    return storage.generaptor.extract_collection(
        collector_secrets,
        collection_storage.data,
        collection_storage.data_dir,
    )


async def _extract_collection(
    storage: Storage, case_guid: UUID, collection_guid: UUID
) -> Outcome:
    _LOGGER.info("extracting collection %s", collection_guid)
    # retrieve collection metadata
    collection = await storage.retrieve_collection(case_guid, collection_guid)
    if not collection:
        _LOGGER.error("failed to retrieve collection")
        return Outcome.FAILURE
    # retrieve collection storage
    collection_storage = storage.collection_storage(case_guid, collection_guid)
    if not collection_storage.data.is_file():
        _LOGGER.error("file not found: %s", collection_storage.data)
        return Outcome.FAILURE
    # create extraction directory if needed
    collection_storage.data_dir.mkdir(parents=True, exist_ok=True)
    # collection fingerprint is not set (not an generaptor collection)
    if not collection.fingerprint:
        _LOGGER.info("extracting collection using 'simple zip' strategy")
        return await _extract_simple_zip(collection_storage)
    # collection fingerprint is set (generaptor collection)
    _LOGGER.info("extracting collection using 'generaptor zip' strategy")
    return await _extract_generaptor_zip(
        storage, case_guid, collection, collection_storage
    )


async def extract_collection(
    redis: Redis, storage: Storage, case_guid: UUID, collection_guid: UUID
) -> bool:
    """Extract collection (with system-wide mutex)"""
    collection_storage = storage.collection_storage(case_guid, collection_guid)
    extracted_flag = collection_storage.data_dir / '__extracted__'
    lock_name = f'collection-extract-lock-{collection_guid}'
    lock = create_redis_lock(redis, lock_name)
    _LOGGER.info("waiting for %s", lock_name)
    async with lock:
        if extracted_flag.is_dir():
            _LOGGER.info(
                "extraction skipped for collection %s", collection_guid
            )
            return True
        outcome = await _extract_collection(
            storage, case_guid, collection_guid
        )
        if outcome != Outcome.SUCCESS:
            _LOGGER.error(
                "extraction failure for collection %s", collection_guid
            )
            return False
        try:
            extracted_flag.mkdir(parents=False, exist_ok=False)
        except FileExistsError:
            _LOGGER.error(
                "extracted flag found in collection %s", collection_guid
            )
            return False
        _LOGGER.info("extraction complete for collection %s", collection_guid)
        return True
