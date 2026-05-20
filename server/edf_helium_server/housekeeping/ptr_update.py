"""PTR database update"""

from edf_fusion.helper.datetime import utcnow
from edf_fusion.helper.logging import get_logger
from generaptor.concept import OperatingSystem

from ..helper.ptr import load_external_ptr
from ..ptr_storage import PTRStorage
from ..storage import Storage

_LOGGER = get_logger('server.housekeeping.ptr_update', root='helium')


async def ptr_update(storage: Storage, ptr_storage: PTRStorage):
    """Update external PTR database"""
    _LOGGER.info("updating ptr database...")
    start = utcnow()
    for opsystem in OperatingSystem:
        _LOGGER.info("loading external ptr for %s", opsystem.value)
        await load_external_ptr(storage, ptr_storage, opsystem)
    _LOGGER.info("updating ptr database took %s", utcnow() - start)
