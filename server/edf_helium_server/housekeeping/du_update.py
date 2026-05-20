"""Disk usage update"""

from edf_fusion.helper.datetime import utcnow
from edf_fusion.helper.logging import get_logger
from edf_fusion.helper.redis import create_redis
from edf_helium_core.concept import CaseDiskUsage, DiskUsage

from ..ptr_storage import PTRStorage
from ..storage import Storage

_LOGGER = get_logger('server.housekeeping.du_update', root='helium')


async def du_update(storage: Storage, _ptr_storage: PTRStorage):
    """Compute disk usage"""
    _LOGGER.info("computing disk usage...")
    start = utcnow()
    cases = {}
    async for case in storage.enumerate_cases():
        collectors = 0
        collections = 0
        analyses = 0
        async for collector in storage.enumerate_collectors(case.guid):
            collector_storage = storage.collector_storage(
                case.guid, collector.guid
            )
            collectors += collector_storage.size
        async for collection in storage.enumerate_collections(case.guid):
            collection_storage = storage.collection_storage(
                case.guid, collection.guid
            )
            collections += collection_storage.size
            async for analysis in storage.enumerate_analyses(
                case.guid, collection.guid
            ):
                analysis_storage = storage.analysis_storage(
                    case.guid, collection.guid, analysis.analyzer
                )
                analyses += analysis_storage.size
        cases[case.guid] = CaseDiskUsage(
            collectors=collectors,
            collections=collections,
            analyses=analyses,
        )
    disk_usage = DiskUsage(cases=cases, updated=utcnow())
    storage.disk_usage.parent.mkdir(parents=False, exist_ok=True)
    disk_usage.to_filepath(storage.disk_usage)
    _LOGGER.info("computing disk usage took %s", utcnow() - start)
