"""/api/config* routes implementation"""

from aiohttp.web import Request
from edf_fusion.helper.aiohttp import json_response
from edf_fusion.server.auth import Action
from edf_fusion.server.config import FusionAnalyzerConfig
from edf_fusion.server.download import get_fusion_dl_api

from ..config import get_helium_config
from ..helper.aiohttp import get_arch, get_opsystem, prologue


async def api_analyzers_get(request: Request):
    """Retrieve analyzers config"""
    action = Action(name='enumerate_analyzers')
    _, storage = await prologue(request, action)
    config = get_helium_config(request)
    analyzers = []
    async for analyzer in storage.enumerate_analyzers():
        analyzer_config = config.analyzer.get(
            analyzer.name, FusionAnalyzerConfig
        )
        if not analyzer_config.enabled:
            continue
        analyzers.append(analyzer.to_dict())
    return json_response(data=analyzers)


async def api_collector_template_download_get(request: Request):
    """Retrieve collector template pending download key"""
    arch = get_arch(request)
    opsystem = get_opsystem(request)
    fusion_dl_api = get_fusion_dl_api(request)
    action = Action(
        name='download_collector_template',
        context={'opsystem': opsystem, 'arch': arch},
    )
    _, storage = await prologue(request, action)
    template = await storage.retrieve_collector_template(opsystem, arch)
    if not template:
        return json_response(
            status=404, message="Collector template not found"
        )
    pdk = await fusion_dl_api.prepare(template, template.name)
    if not pdk:
        return json_response(
            status=503, message="Cannot process more download requests for now"
        )
    return json_response(data=pdk.to_dict())
