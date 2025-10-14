"""/api/disk_usage route implementation"""

from aiohttp.web import Request
from edf_fusion.helper.aiohttp import json_response
from edf_fusion.helper.datetime import utcnow
from edf_fusion.server.auth import get_fusion_auth_api
from edf_helium_core.concept import DiskUsage

from ..helper.aiohttp import prologue


async def api_disk_usage_get(request: Request):
    """Retrieve collection targets for given operating system"""
    identity, storage = await prologue(request, 'disk_usage', context={})
    fusion_auth_api = get_fusion_auth_api(request)
    cannot_access_cases = [
        case.guid
        async for case in storage.enumerate_cases()
        if not fusion_auth_api.can_access_case(identity, case)
    ]
    disk_usage = await storage.retrieve_disk_usage()
    if not disk_usage:
        disk_usage = DiskUsage(cases={}, updated=utcnow())
    for case_guid in cannot_access_cases:
        disk_usage.cases.pop(case_guid, None)
    return json_response(status=200, data=disk_usage.to_dict())
