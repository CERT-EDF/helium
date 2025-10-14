"""Helium Case Synchronizer"""

from argparse import ArgumentParser
from pathlib import Path
from re import compile as regexp
from shutil import copy

from edf_fusion.concept import Case
from edf_fusion.helper.logging import get_logger
from edf_fusion.server.storage import SyncStorage
from edf_fusion.server.synchronizer import FusionSynchronizer

from .__version__ import version
from .config import HeliumServerConfig
from .storage import Storage

_LOGGER = get_logger('synchronizer', root='helium')
_HOSTNAME_PATTERN = regexp(r'[^\w\-\.]+')


async def _sync_case_impl(storage: Storage, case: Case, directory: Path):
    sync_storage = SyncStorage(case=case, directory=directory)
    # sync collectors
    async for collector in storage.enumerate_collectors(case.guid):
        collector_storage = storage.collector_storage(
            case.guid, collector.guid
        )
        sync_dir = sync_storage.collectors / collector_storage.config.stem
        sync_dir.mkdir(parents=True, exist_ok=True)
        collector.to_filepath(sync_dir / 'metadata.json')
        copy(
            collector_storage.config,
            sync_dir / collector_storage.config.name,
        )
        copy(
            collector_storage.secrets,
            sync_dir / collector_storage.secrets.name,
        )
        copy(
            collector_storage.executable,
            sync_dir / collector_storage.executable.name,
        )
    # sync collections
    async for collection in storage.enumerate_collections(case.guid):
        collection_storage = storage.collection_storage(
            case.guid, collection.guid
        )
        created = collection.created.strftime('%Y%m%d%H%M%S')
        hostname = _HOSTNAME_PATTERN.sub(
            '', collection.hostname or 'MISSING_HOSTNAME'
        )
        sync_dir = sync_storage.collections / hostname
        sync_dir.mkdir(parents=True, exist_ok=True)
        collection.to_filepath(sync_dir / f'{hostname}_{created}.json')
        copy(collection_storage.data, sync_dir / f'{hostname}_{created}.zip')


def _parse_args():
    parser = ArgumentParser(description="Helium Synchronizer")
    parser.add_argument(
        '--config',
        '-c',
        type=Path,
        default=Path('helium.yml'),
        help="Configuration file",
    )
    return parser.parse_args()


def app():
    """Application entrypoint"""
    _LOGGER.info("Helium Synchronizer %s", version)
    args = _parse_args()
    config = HeliumServerConfig.from_filepath(args.config)
    synchronizer = FusionSynchronizer(
        config=config.synchronizer,
        storage=Storage(config=config.storage),
        sync_case_impl=_sync_case_impl,
    )
    synchronizer.run()


if __name__ == '__main__':
    app()
