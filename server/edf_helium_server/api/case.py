"""/api/case* routes implementation"""

from aiohttp.web import Request, StreamResponse
from edf_fusion.helper.aiohttp import (
    get_guid,
    get_json_body,
    json_response,
    stream_multipart_part_content,
    stream_multipart_parts,
    stream_response,
)
from edf_fusion.helper.logging import get_logger
from edf_fusion.helper.streaming import stream_from_file
from edf_fusion.server.case import (
    AttachContext,
    CreateContext,
    DeleteContext,
    EnumerateContext,
    RetrieveContext,
    UpdateContext,
)
from edf_fusion.server.download import get_fusion_dl_api
from edf_fusion.server.event import get_fusion_evt_api
from edf_fusion.server.storage import get_fusion_storage
from edf_helium_core.concept import Case, Status

from ..helper.aiohttp import prologue

_LOGGER = get_logger('server.api.case', root='helium')


async def attach_case_impl(ctx: AttachContext) -> Case | None:
    """Attach case"""
    storage = get_fusion_storage(ctx.request)
    success = await storage.attach_case(ctx.case_guid, ctx.next_case_guid)
    if not success:
        return None
    case = await storage.retrieve_case(ctx.next_case_guid)
    return case


async def create_case_impl(ctx: CreateContext) -> Case | None:
    """Create case"""
    storage = get_fusion_storage(ctx.request)
    fusion_evt_api = get_fusion_evt_api(ctx.request)
    case = await storage.create_case(ctx.managed, ctx.body)
    if not case:
        return None
    await fusion_evt_api.notify(category='create_case', case=case)
    return case


async def update_case_impl(ctx: UpdateContext) -> Case | None:
    """Update case"""
    storage = get_fusion_storage(ctx.request)
    fusion_evt_api = get_fusion_evt_api(ctx.request)
    case = await storage.update_case(ctx.case_guid, ctx.body)
    await fusion_evt_api.notify(category='update_case', case=case)
    return case


async def delete_case_impl(ctx: DeleteContext) -> bool:
    """Delete case"""
    storage = get_fusion_storage(ctx.request)
    fusion_evt_api = get_fusion_evt_api(ctx.request)
    case = await storage.retrieve_case(ctx.case_guid)
    deleted = await storage.delete_case(ctx.case_guid)
    if deleted:
        await fusion_evt_api.notify(category='delete_case', case=case)
    return deleted


async def retrieve_case_impl(ctx: RetrieveContext) -> Case | None:
    """Retrieve case"""
    storage = get_fusion_storage(ctx.request)
    case = await storage.retrieve_case(ctx.case_guid)
    return case


async def enumerate_cases_impl(ctx: EnumerateContext) -> list[Case]:
    """Enumerate cases"""
    storage = get_fusion_storage(ctx.request)
    return [case async for case in storage.enumerate_cases()]


async def api_analyses_get(request: Request):
    """Enumerate case collection analyses"""
    case_guid = get_guid(request, 'case_guid')
    collection_guid = get_guid(request, 'collection_guid')
    _, storage = await prologue(
        request,
        'enumerate_analyses',
        context={'case_guid': case_guid, 'collection_guid': collection_guid},
    )
    return json_response(
        data=[
            analysis.to_dict()
            async for analysis in storage.enumerate_analyses(
                case_guid, collection_guid
            )
        ]
    )


async def api_analysis_delete(request: Request):
    """Delete analysis"""
    case_guid = get_guid(request, 'case_guid')
    collection_guid = get_guid(request, 'collection_guid')
    fusion_evt_api = get_fusion_evt_api(request)
    analyzer = request.match_info['analyzer']
    _, storage = await prologue(
        request,
        'delete_analysis',
        context={
            'case_guid': case_guid,
            'collection_guid': collection_guid,
            'analyzer': analyzer,
            'case_open_check': True,
            'is_delete_op': True,
        },
    )
    case = await storage.retrieve_case(case_guid)
    analysis = await storage.retrieve_analysis(
        case_guid, collection_guid, analyzer
    )
    if not analysis:
        return json_response(status=404, message="Analysis not found")
    deleted = await storage.delete_analysis(
        case_guid, collection_guid, analyzer
    )
    await fusion_evt_api.notify(
        category='delete_analysis',
        case=case,
        ext=analysis.to_dict(),
    )
    if not deleted:
        return json_response(status=400, message="Not deleted")
    return json_response(data={})


async def api_analysis_log_get(request: Request) -> StreamResponse:
    """Retrieve analysis log"""
    case_guid = get_guid(request, 'case_guid')
    collection_guid = get_guid(request, 'collection_guid')
    analyzer = request.match_info['analyzer']
    _, storage = await prologue(
        request,
        'download_analysis_log',
        context={
            'case_guid': case_guid,
            'collection_guid': collection_guid,
            'analyzer': analyzer,
        },
    )
    analysis_storage = storage.analysis_storage(
        case_guid, collection_guid, analyzer
    )
    if not analysis_storage.log.is_file():
        return json_response(status=404, message="Analysis log not found")
    response = await stream_response(
        request,
        f'{collection_guid}_{analyzer}.log',
        stream_from_file(analysis_storage.log),
    )
    return response


async def api_analysis_download_get(request: Request):
    """Retrieve analysis pending download key"""
    case_guid = get_guid(request, 'case_guid')
    collection_guid = get_guid(request, 'collection_guid')
    fusion_dl_api = get_fusion_dl_api(request)
    analyzer = request.match_info['analyzer']
    _, storage = await prologue(
        request,
        'download_analysis_data',
        context={
            'case_guid': case_guid,
            'collection_guid': collection_guid,
            'analyzer': analyzer,
        },
    )
    filepath = await storage.retrieve_analysis_data(
        case_guid, collection_guid, analyzer
    )
    if not filepath:
        return json_response(status=404, message="Analysis not found")
    filename = f'{collection_guid}_{analyzer}.zip'
    pdk = await fusion_dl_api.prepare(filepath, filename)
    if not pdk:
        return json_response(
            status=503, message="Cannot process more download requests for now"
        )
    return json_response(data=pdk.to_dict())


async def api_analysis_get(request: Request):
    """Retrieve case collection analysis metadata"""
    case_guid = get_guid(request, 'case_guid')
    collection_guid = get_guid(request, 'collection_guid')
    analyzer = request.match_info['analyzer']
    _, storage = await prologue(
        request,
        'retrieve_analysis',
        context={
            'case_guid': case_guid,
            'collection_guid': collection_guid,
            'analyzer': analyzer,
        },
    )
    analysis = await storage.retrieve_analysis(
        case_guid, collection_guid, analyzer
    )
    if not analysis:
        return json_response(status=404, message="Analysis not found")
    return json_response(data=analysis.to_dict())


async def api_analysis_post(request: Request):
    """Create case collection analysis"""
    case_guid = get_guid(request, 'case_guid')
    collection_guid = get_guid(request, 'collection_guid')
    fusion_evt_api = get_fusion_evt_api(request)
    _, storage = await prologue(
        request,
        'create_analysis',
        context={
            'case_guid': case_guid,
            'collection_guid': collection_guid,
            'case_open_check': True,
        },
    )
    body = await get_json_body(request)
    try:
        analysis = await storage.create_analysis(
            case_guid, collection_guid, body
        )
    except ValueError as exc:
        return json_response(status=400, message=str(exc))
    case = await storage.retrieve_case(case_guid)
    collection = await storage.retrieve_collection(case_guid, collection_guid)
    await fusion_evt_api.notify(
        category='create_analysis',
        case=case,
        ext={
            'analysis': analysis.to_dict(),
            'collection': collection.to_dict(),
        },
    )
    return json_response(data=analysis.to_dict())


async def api_analysis_put(request: Request):
    """Update case collection analysis"""
    case_guid = get_guid(request, 'case_guid')
    collection_guid = get_guid(request, 'collection_guid')
    analyzer = request.match_info['analyzer']
    _, storage = await prologue(
        request,
        'update_analysis',
        context={
            'case_guid': case_guid,
            'collection_guid': collection_guid,
            'analyzer': analyzer,
            'case_open_check': True,
        },
    )
    body = await get_json_body(request)
    dct = {'status': Status.PENDING.value}
    priority = body.get('priority')
    if priority:
        dct['priority'] = priority
    try:
        analysis = await storage.update_analysis(
            case_guid, collection_guid, analyzer, dct
        )
    except ValueError as exc:
        return json_response(status=400, message=str(exc))
    return json_response(data=analysis.to_dict())


async def api_collection_cache_delete(request: Request):
    """Delete collection case directory"""
    case_guid = get_guid(request, 'case_guid')
    collection_guid = get_guid(request, 'collection_guid')
    _, storage = await prologue(
        request,
        'delete_collection_cache',
        context={
            'case_guid': case_guid,
            'collection_guid': collection_guid,
            'case_open_check': True,
            # is_delete_op is not expected to be set here
        },
    )
    deleted = await storage.delete_collection_cache(case_guid, collection_guid)
    if not deleted:
        return json_response(status=404, message="Collection cache is empty")
    return json_response(data={})


async def api_collection_delete(request: Request):
    """Delete collection"""
    case_guid = get_guid(request, 'case_guid')
    collection_guid = get_guid(request, 'collection_guid')
    fusion_evt_api = get_fusion_evt_api(request)
    _, storage = await prologue(
        request,
        'delete_collection',
        context={
            'case_guid': case_guid,
            'collection_guid': collection_guid,
            'case_open_check': True,
            'is_delete_op': True,
        },
    )
    case = await storage.retrieve_case(case_guid)
    collection = await storage.retrieve_collection(case_guid, collection_guid)
    deleted = await storage.delete_collection(case_guid, collection_guid)
    await fusion_evt_api.notify(
        category='delete_collection',
        case=case,
        ext=collection.to_dict(),
    )
    if not deleted:
        return json_response(status=400, message="Not deleted")
    return json_response(data={})


async def api_collection_download_get(request: Request):
    """Retrieve collection pending download key"""
    case_guid = get_guid(request, 'case_guid')
    collection_guid = get_guid(request, 'collection_guid')
    fusion_dl_api = get_fusion_dl_api(request)
    _, storage = await prologue(
        request,
        'collection_download',
        context={'case_guid': case_guid, 'collection_guid': collection_guid},
    )
    filepath = await storage.retrieve_collection_data(
        case_guid, collection_guid
    )
    if not filepath:
        return json_response(status=404, message="Collection not found")
    pdk = await fusion_dl_api.prepare(filepath, f"{collection_guid}.zip")
    if not pdk:
        return json_response(
            status=503, message="Cannot process more download requests for now"
        )
    return json_response(data=pdk.to_dict())


async def api_collection_get(request: Request):
    """Retrieve case collection metadata"""
    case_guid = get_guid(request, 'case_guid')
    collection_guid = get_guid(request, 'collection_guid')
    _, storage = await prologue(
        request,
        'retrieve_collection',
        context={'case_guid': case_guid, 'collection_guid': collection_guid},
    )
    collection = await storage.retrieve_collection(case_guid, collection_guid)
    if not collection:
        return json_response(status=404, message="Collection not found")
    return json_response(data=collection.to_dict())


async def api_collection_post(request: Request):
    """Create case collection"""
    case_guid = get_guid(request, 'case_guid')
    fusion_evt_api = get_fusion_evt_api(request)
    _, storage = await prologue(
        request,
        'create_collection',
        context={'case_guid': case_guid, 'case_open_check': True},
    )
    collection = None
    async for part in stream_multipart_parts(request, {'file'}):
        if collection:
            _LOGGER.warning(
                "processing first file only (expected only one 'file' part)"
            )
            await part.release()
            continue
        collection = await storage.create_collection(
            case_guid, stream_multipart_part_content(part)
        )
    if not collection:
        return json_response(status=400, message="Invalid collection")
    case = await storage.retrieve_case(case_guid)
    collection_dct = collection.to_dict()
    await fusion_evt_api.notify(
        category='create_collection',
        case=case,
        ext=collection_dct,
    )
    return json_response(data=collection_dct)


async def api_collection_put(request: Request):
    """Update case collection"""
    case_guid = get_guid(request, 'case_guid')
    collection_guid = get_guid(request, 'collection_guid')
    fusion_evt_api = get_fusion_evt_api(request)
    _, storage = await prologue(
        request,
        'update_collection',
        context={
            'case_guid': case_guid,
            'collection_guid': collection_guid,
            'case_open_check': True,
        },
    )
    body = await get_json_body(request)
    collection = await storage.update_collection(
        case_guid, collection_guid, body
    )
    if not collection:
        return json_response(
            status=400, message="Analysis status inconsistent with request"
        )
    case = await storage.retrieve_case(case_guid)
    collection_dct = collection.to_dict()
    await fusion_evt_api.notify(
        category='update_collection',
        case=case,
        ext=collection_dct,
    )
    return json_response(data=collection_dct)


async def api_collections_get(request: Request):
    """Enumerate case collections"""
    case_guid = get_guid(request, 'case_guid')
    _, storage = await prologue(
        request, 'enumerate_collections', context={'case_guid': case_guid}
    )
    return json_response(
        data=[
            collection.to_dict()
            async for collection in storage.enumerate_collections(case_guid)
        ]
    )


async def api_collector_delete(request: Request):
    """Delete collector"""
    case_guid = get_guid(request, 'case_guid')
    collector_guid = get_guid(request, 'collector_guid')
    fusion_evt_api = get_fusion_evt_api(request)
    _, storage = await prologue(
        request,
        'delete_collector',
        context={
            'case_guid': case_guid,
            'collector_guid': collector_guid,
            'case_open_check': True,
            'is_delete_op': True,
        },
    )
    case = await storage.retrieve_case(case_guid)
    collector = await storage.retrieve_collector(case_guid, collector_guid)
    deleted = await storage.delete_collector(case_guid, collector_guid)
    await fusion_evt_api.notify(
        category='delete_collector',
        case=case,
        ext=collector.to_dict(),
    )
    if not deleted:
        return json_response(status=400, message="Not deleted")
    return json_response(data={})


async def api_collector_download_get(request: Request):
    """Retrieve collector pending download key"""
    case_guid = get_guid(request, 'case_guid')
    collector_guid = get_guid(request, 'collector_guid')
    fusion_dl_api = get_fusion_dl_api(request)
    _, storage = await prologue(
        request,
        'download_collector',
        context={'case_guid': case_guid, 'collector_guid': collector_guid},
    )
    executable = await storage.retrieve_collector_executable(
        case_guid, collector_guid
    )
    if not executable:
        return json_response(status=404, message="Collector not found")
    pdk = await fusion_dl_api.prepare(executable, executable.name)
    if not pdk:
        return json_response(
            status=503, message="Cannot process more download requests for now"
        )
    return json_response(data=pdk.to_dict())


async def api_collector_get(request: Request):
    """Retrieve case collector metadata"""
    case_guid = get_guid(request, 'case_guid')
    collector_guid = get_guid(request, 'collector_guid')
    _, storage = await prologue(
        request,
        'retrieve_collector',
        context={'case_guid': case_guid, 'collector_guid': collector_guid},
    )
    collector = await storage.retrieve_collector(case_guid, collector_guid)
    if not collector:
        return json_response(status=404, message="Collector not found")
    return json_response(data=collector.to_dict())


async def api_collector_post(request: Request):
    """Create case collector"""
    case_guid = get_guid(request, 'case_guid')
    fusion_evt_api = get_fusion_evt_api(request)
    _, storage = await prologue(
        request,
        'create_collector',
        context={'case_guid': case_guid, 'case_open_check': True},
    )
    body = await get_json_body(request)
    collector = await storage.create_collector(case_guid, body)
    if not collector:
        return json_response(status=400, message="Invalid collector")
    case = await storage.retrieve_case(case_guid)
    collector_dct = collector.to_dict()
    await fusion_evt_api.notify(
        category='create_collector',
        case=case,
        ext=collector_dct,
    )
    return json_response(data=collector_dct)


async def api_collector_import_post(request: Request):
    """Import case collector (without binary)"""
    case_guid = get_guid(request, 'case_guid')
    fusion_evt_api = get_fusion_evt_api(request)
    _, storage = await prologue(
        request,
        'import_collector',
        context={'case_guid': case_guid, 'case_open_check': True},
    )
    body = await get_json_body(request)
    collector = await storage.import_collector(case_guid, body)
    if not collector:
        return json_response(status=400, message="Invalid collector")
    case = await storage.retrieve_case(case_guid)
    collector_dct = collector.to_dict()
    await fusion_evt_api.notify(
        category='import_collector',
        case=case,
        ext=collector_dct,
    )
    return json_response(data=collector_dct)


async def api_collector_secrets_get(request: Request):
    """Retrieve case collector secrets"""
    case_guid = get_guid(request, 'case_guid')
    collector_guid = get_guid(request, 'collector_guid')
    _, storage = await prologue(
        request,
        'retrieve_collector_secrets',
        context={'case_guid': case_guid, 'collector_guid': collector_guid},
    )
    collector_secrets = await storage.retrieve_collector_secrets(
        case_guid, collector_guid
    )
    if not collector_secrets:
        return json_response(status=404, message="Collector secrets not found")
    return json_response(data=collector_secrets.to_dict())


async def api_collectors_get(request: Request):
    """Enumerate case collectors"""
    case_guid = get_guid(request, 'case_guid')
    _, storage = await prologue(
        request, 'enumerate_collectors', context={'case_guid': case_guid}
    )
    return json_response(
        data=[
            collector.to_dict()
            async for collector in storage.enumerate_collectors(case_guid)
        ]
    )
