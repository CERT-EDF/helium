"""Helium housekeeper entrypoint"""

from argparse import ArgumentParser, Namespace
from asyncio import Event, gather, get_running_loop, run
from pathlib import Path
from signal import SIGINT, SIGTERM

from edf_fusion.helper.logging import get_logger
from edf_fusion.helper.redis import create_redis

from .__version__ import version
from .config import HeliumServerConfig
from .housekeeping import HousekeepingTask
from .housekeeping.du_update import du_update
from .housekeeping.ptr_update import ptr_update
from .ptr_storage import PTRStorage
from .storage import Storage

_LOGGER = get_logger('server.housekeeper', root='helium')
_STOP = Event()
_HOUSEKEEPING_TASKS = (
    HousekeepingTask(name='du_update', routine=du_update, frequency=180),
    HousekeepingTask(name='ptr_update', routine=ptr_update, frequency=1800),
)


def _shutdown():
    _LOGGER.warning("shutdown requested")
    _STOP.set()


def _parse_args() -> Namespace:
    parser = ArgumentParser(description="Helium Housekeeper")
    parser.add_argument(
        '--config',
        '-c',
        type=Path,
        default=Path('helium.yml'),
        help="Helium configuration file",
    )
    return parser.parse_args()


async def _do_housekeeping(storage: Storage, ptr_storage: PTRStorage):
    loop = get_running_loop()
    for sig in (SIGINT, SIGTERM):
        loop.add_signal_handler(sig, _shutdown)

    coros = [
        task.run(_STOP, storage, ptr_storage) for task in _HOUSEKEEPING_TASKS
    ]
    ctx = ptr_storage.database.context()
    await anext(ctx)
    await gather(*coros)
    try:
        await anext(ctx)
    except StopAsyncIteration:
        pass


def app():
    """Helium Housekeeper entrypoint"""
    _LOGGER.info("Helium Housekeeper %s", version)
    args = _parse_args()
    try:
        config = HeliumServerConfig.from_filepath(args.config)
    except Exception:
        _LOGGER.exception("invalid configuration file: %s", args.config)
        return
    redis = create_redis(config.server.redis_url)
    storage = Storage(redis=redis, config=config.storage)
    ptr_storage = PTRStorage(redis=redis, config=config.storage)
    run(_do_housekeeping(storage, ptr_storage))
