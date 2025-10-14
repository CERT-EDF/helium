"""Helium server entrypoint"""

from argparse import ArgumentParser, Namespace
from asyncio import Event, get_running_loop, run, wait_for
from pathlib import Path
from signal import SIGINT, SIGTERM

from edf_fusion.helper.datetime import utcnow
from edf_fusion.helper.logging import get_logger
from edf_helium_core.concept import CaseDiskUsage, DiskUsage

from .__version__ import version
from .config import HeliumServerConfig
from .storage import Storage

_LOGGER = get_logger('server.disk_usage', root='helium')
_SHUTDOWN = Event()


def _shutdown():
    _LOGGER.warning("shutdown requested")
    _SHUTDOWN.set()


def _parse_args() -> Namespace:
    parser = ArgumentParser(description="Helium Disk Usage")
    parser.add_argument(
        '--config',
        '-c',
        type=Path,
        default=Path('helium.yml'),
        help="Helium configuration file",
    )
    return parser.parse_args()


async def _compute_du(storage: Storage):
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


async def _compute_du_loop(storage: Storage):
    loop = get_running_loop()
    for sig in (SIGINT, SIGTERM):
        loop.add_signal_handler(sig, _shutdown)
    while not _SHUTDOWN.is_set():
        await _compute_du(storage)
        try:
            await wait_for(_SHUTDOWN.wait(), 180)
        except TimeoutError:
            continue


def app():
    """Helium server entrypoint"""
    _LOGGER.info("Helium Disk Usage %s", version)
    args = _parse_args()
    try:
        config = HeliumServerConfig.from_filepath(args.config)
    except:
        _LOGGER.exception("invalid configuration file: %s", args.config)
        return
    storage = Storage(config=config.storage)
    run(_compute_du_loop(storage))
