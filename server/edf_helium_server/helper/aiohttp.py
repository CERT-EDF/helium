"""Helium aiohttp Helper"""

from aiohttp.web import Request
from edf_fusion.concept import Identity
from edf_fusion.server.auth import Action, get_fusion_auth_api
from edf_fusion.server.storage import get_fusion_storage
from generaptor.concept import Architecture, OperatingSystem

from ..ptr_storage import PTRStorage, get_ptr_storage
from ..storage import Storage


def get_arch(request: Request) -> Architecture | None:
    """Extract architecture from request path"""
    try:
        return Architecture(request.match_info['arch'])
    except ValueError:
        return None


def get_opsystem(request: Request) -> OperatingSystem | None:
    """Extract operating system from request path"""
    try:
        return OperatingSystem(request.match_info['opsystem'])
    except ValueError:
        return None


async def prologue(
    request: Request, action: Action
) -> tuple[Identity, Storage]:
    """Determine if authorized and retrieve storage"""
    fusion_auth_api = get_fusion_auth_api(request)
    identity = await fusion_auth_api.authorize(request, action)
    storage = get_fusion_storage(request)
    return identity, storage


async def prologue_ptr(
    request: Request, action: Action
) -> tuple[Identity, PTRStorage]:
    """Determine if authorized and retrieve PTR storage"""
    fusion_auth_api = get_fusion_auth_api(request)
    identity = await fusion_auth_api.authorize(request, action)
    ptr_storage = get_ptr_storage(request)
    return identity, ptr_storage
