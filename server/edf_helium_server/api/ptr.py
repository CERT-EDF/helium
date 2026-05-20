"""/api/ptr* routes implementation"""

from aiohttp.web import Request
from edf_fusion.helper.aiohttp import get_guid, get_json_body, json_response
from edf_fusion.server.auth import Action

from ..helper.aiohttp import get_opsystem, prologue_ptr


async def api_profiles_get(request: Request):
    """Enumerate profiles"""
    opsystem = get_opsystem(request)
    if not opsystem:
        return json_response(status=400, message="Invalid operating system")
    action = Action(name='enumerate_profiles', context={'opsystem': opsystem})
    _, ptr_storage = await prologue_ptr(request, action)
    profiles = [
        p.to_dict() async for p in ptr_storage.enumerate_profiles(opsystem)
    ]
    return json_response(data=profiles)


async def api_profile_post(request: Request):
    """Create a profile"""
    opsystem = get_opsystem(request)
    if not opsystem:
        return json_response(status=400, message="Invalid operating system")
    action = Action(
        name='create_profile', change=True, context={'opsystem': opsystem}
    )
    _, ptr_storage = await prologue_ptr(request, action)
    body = await get_json_body(request)
    body.pop('guid', None)
    profile = await ptr_storage.create_profile(opsystem, body)
    if not profile:
        return json_response(status=400, message="Cannot create profile")
    return json_response(data=profile.to_dict())


async def api_profile_get(request: Request):
    """Retrieve a profile"""
    opsystem = get_opsystem(request)
    if not opsystem:
        return json_response(status=400, message="Invalid operating system")
    profile_guid = get_guid(request, 'profile_guid')
    action = Action(
        name='retrieve_profile',
        context={'opsystem': opsystem, 'profile_guid': profile_guid},
    )
    _, ptr_storage = await prologue_ptr(request, action)
    profile = await ptr_storage.retrieve_profile(opsystem, profile_guid)
    if not profile:
        return json_response(status=404, message="Profile not found")
    return json_response(data=profile.to_dict())


async def api_profile_put(request: Request):
    """Update a profile"""
    opsystem = get_opsystem(request)
    if not opsystem:
        return json_response(status=400, message="Invalid operating system")
    profile_guid = get_guid(request, 'profile_guid')
    action = Action(
        name='update_profile',
        change=True,
        context={'opsystem': opsystem, 'profile_guid': profile_guid},
    )
    _, ptr_storage = await prologue_ptr(request, action)
    body = await get_json_body(request)
    profile = await ptr_storage.update_profile(opsystem, profile_guid, body)
    if not profile:
        return json_response(status=404, message="Profile not found")
    return json_response(data=profile.to_dict())


async def api_profile_delete(request: Request):
    """Delete a profile"""
    opsystem = get_opsystem(request)
    if not opsystem:
        return json_response(status=400, message="Invalid operating system")
    profile_guid = get_guid(request, 'profile_guid')
    action = Action(
        name='delete_profile',
        change=True,
        delete=True,
        context={'opsystem': opsystem, 'profile_guid': profile_guid},
    )
    _, ptr_storage = await prologue_ptr(request, action)
    deleted = await ptr_storage.delete_profile(opsystem, profile_guid)
    if not deleted:
        return json_response(status=404, message="Profile not found")
    return json_response(data=None)


async def api_targets_get(request: Request):
    """Enumerate targets"""
    opsystem = get_opsystem(request)
    if not opsystem:
        return json_response(status=400, message="Invalid operating system")
    action = Action(name='enumerate_targets', context={'opsystem': opsystem})
    _, ptr_storage = await prologue_ptr(request, action)
    targets = [
        t.to_dict() async for t in ptr_storage.enumerate_targets(opsystem)
    ]
    return json_response(data=targets)


async def api_target_post(request: Request):
    """Create a target"""
    opsystem = get_opsystem(request)
    if not opsystem:
        return json_response(status=400, message="Invalid operating system")
    action = Action(
        name='create_target', change=True, context={'opsystem': opsystem}
    )
    _, ptr_storage = await prologue_ptr(request, action)
    body = await get_json_body(request)
    body.pop('guid', None)
    target = await ptr_storage.create_target(opsystem, body)
    if not target:
        return json_response(status=400, message="Cannot create target")
    return json_response(data=target.to_dict())


async def api_target_get(request: Request):
    """Retrieve a target"""
    opsystem = get_opsystem(request)
    if not opsystem:
        return json_response(status=400, message="Invalid operating system")
    target_guid = get_guid(request, 'target_guid')
    action = Action(
        name='retrieve_target',
        context={'opsystem': opsystem, 'target_guid': target_guid},
    )
    _, ptr_storage = await prologue_ptr(request, action)
    target = await ptr_storage.retrieve_target(opsystem, target_guid)
    if not target:
        return json_response(status=404, message="Target not found")
    return json_response(data=target.to_dict())


async def api_target_put(request: Request):
    """Update a target"""
    opsystem = get_opsystem(request)
    if not opsystem:
        return json_response(status=400, message="Invalid operating system")
    target_guid = get_guid(request, 'target_guid')
    action = Action(
        name='update_target',
        change=True,
        context={'opsystem': opsystem, 'target_guid': target_guid},
    )
    _, ptr_storage = await prologue_ptr(request, action)
    body = await get_json_body(request)
    target = await ptr_storage.update_target(opsystem, target_guid, body)
    if not target:
        return json_response(status=404, message="Target not found")
    return json_response(data=target.to_dict())


async def api_target_delete(request: Request):
    """Delete a target"""
    opsystem = get_opsystem(request)
    if not opsystem:
        return json_response(status=400, message="Invalid operating system")
    target_guid = get_guid(request, 'target_guid')
    action = Action(
        name='delete_target',
        change=True,
        delete=True,
        context={'opsystem': opsystem, 'target_guid': target_guid},
    )
    _, ptr_storage = await prologue_ptr(request, action)
    deleted = await ptr_storage.delete_target(opsystem, target_guid)
    if not deleted:
        return json_response(status=404, message="Target not found")
    return json_response(data=None)


async def api_rules_get(request: Request):
    """Enumerate rules"""
    opsystem = get_opsystem(request)
    if not opsystem:
        return json_response(status=400, message="Invalid operating system")
    action = Action(name='enumerate_rules', context={'opsystem': opsystem})
    _, ptr_storage = await prologue_ptr(request, action)
    rules = [r.to_dict() async for r in ptr_storage.enumerate_rules(opsystem)]
    return json_response(data=rules)


async def api_rule_post(request: Request):
    """Create a rule"""
    opsystem = get_opsystem(request)
    if not opsystem:
        return json_response(status=400, message="Invalid operating system")
    action = Action(
        name='create_rule', change=True, context={'opsystem': opsystem}
    )
    _, ptr_storage = await prologue_ptr(request, action)
    body = await get_json_body(request)
    body.pop('guid', None)
    body.pop('opsystem', None)
    rule = await ptr_storage.create_rule(opsystem, body)
    if not rule:
        return json_response(status=400, message="Cannot create rule")
    return json_response(data=rule.to_dict())


async def api_rule_get(request: Request):
    """Retrieve a rule"""
    opsystem = get_opsystem(request)
    if not opsystem:
        return json_response(status=400, message="Invalid operating system")
    rule_guid = get_guid(request, 'rule_guid')
    action = Action(
        name='retrieve_rule',
        context={'opsystem': opsystem, 'rule_guid': rule_guid},
    )
    _, ptr_storage = await prologue_ptr(request, action)
    rule = await ptr_storage.retrieve_rule(opsystem, rule_guid)
    if not rule:
        return json_response(status=404, message="Rule not found")
    return json_response(data=rule.to_dict())


async def api_rule_put(request: Request):
    """Update a rule"""
    opsystem = get_opsystem(request)
    if not opsystem:
        return json_response(status=400, message="Invalid operating system")
    rule_guid = get_guid(request, 'rule_guid')
    action = Action(
        name='update_rule',
        change=True,
        context={'opsystem': opsystem, 'rule_guid': rule_guid},
    )
    _, ptr_storage = await prologue_ptr(request, action)
    body = await get_json_body(request)
    rule = await ptr_storage.update_rule(opsystem, rule_guid, body)
    if not rule:
        return json_response(status=404, message="Rule not found")
    return json_response(data=rule.to_dict())
