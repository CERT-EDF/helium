"""/api/config* routes implementation"""

from aiohttp.web import Request
from edf_fusion.helper.aiohttp import json_response
from edf_fusion.server.config import FusionAnalyzerConfig
from edf_fusion.server.download import get_fusion_dl_api
from edf_helium_core.concept import Profile, Rule, Target
from generaptor.concept import (
    Architecture,
    OperatingSystem,
    get_profile_mapping,
    get_rule_set,
    get_target_set,
)

from ..config import get_helium_config
from ..helper.aiohttp import prologue


def _get_arch(request: Request) -> Architecture | None:
    try:
        return Architecture(request.match_info['arch'])
    except ValueError:
        return None


def _get_opsystem(request: Request) -> OperatingSystem | None:
    try:
        return OperatingSystem(request.match_info['opsystem'])
    except ValueError:
        return None


async def api_profiles_get(request: Request):
    """Retrieve collection profiles for given operating system"""
    opsystem = _get_opsystem(request)
    _, storage = await prologue(
        request, 'enumerate_profiles', context={'opsystem': opsystem.value}
    )
    profile_mapping = get_profile_mapping(
        storage.generaptor.cache,
        storage.generaptor.config,
        opsystem,
    )
    if not profile_mapping:
        return json_response(data=[])
    return json_response(
        data=[
            Profile(name=name, targets=set(profile.targets)).to_dict()
            for name, profile in profile_mapping.items()
        ]
    )


async def api_rules_get(request: Request):
    """Retrieve collection rules for given operating system"""
    opsystem = _get_opsystem(request)
    _, storage = await prologue(
        request, 'enumerate_rules', context={'opsystem': opsystem.value}
    )
    _, rule_set = get_rule_set(
        storage.generaptor.cache,
        storage.generaptor.config,
        opsystem,
    )
    if not rule_set:
        return json_response(status=404, message="RuleSet not found")
    return json_response(
        data=[
            Rule(
                uid=rule.uid,
                name=rule.name,
                category=rule.category,
                glob=rule.glob,
                accessor=rule.accessor,
                comment=rule.comment,
            ).to_dict()
            for rule in rule_set.rules.values()
        ]
    )


async def api_targets_get(request: Request):
    """Retrieve collection targets for given operating system"""
    opsystem = _get_opsystem(request)
    _, storage = await prologue(
        request, 'enumerate_targets', context={'opsystem': opsystem.value}
    )
    max_uid, _ = get_rule_set(
        storage.generaptor.cache,
        storage.generaptor.config,
        opsystem,
    )
    target_set = get_target_set(
        storage.generaptor.cache,
        storage.generaptor.config,
        opsystem,
        max_uid,
    )
    return json_response(
        data=[
            Target(name=target.name, rule_uids=target.rule_uids).to_dict()
            for target in target_set.targets.values()
        ]
    )


async def api_analyzers_get(request: Request):
    """Retrieve analyzers config"""
    _, storage = await prologue(request, 'enumerate_analyzers')
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
    arch = _get_arch(request)
    opsystem = _get_opsystem(request)
    fusion_dl_api = get_fusion_dl_api(request)
    _, storage = await prologue(
        request,
        'download_collector_template',
        context={'opsystem': opsystem, 'arch': arch},
    )
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
