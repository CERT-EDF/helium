"""Helium API module"""

from aiohttp.web import Application, delete, get, post, put
from edf_fusion.helper.logging import get_logger

from .case import (
    api_analyses_get,
    api_analysis_delete,
    api_analysis_download_get,
    api_analysis_get,
    api_analysis_log_get,
    api_analysis_post,
    api_analysis_put,
    api_collection_cache_delete,
    api_collection_delete,
    api_collection_download_get,
    api_collection_get,
    api_collection_post,
    api_collection_put,
    api_collections_get,
    api_collector_delete,
    api_collector_download_get,
    api_collector_get,
    api_collector_import_post,
    api_collector_post,
    api_collector_secrets_get,
    api_collectors_get,
    attach_case_impl,
    create_case_impl,
    delete_case_impl,
    enumerate_cases_impl,
    retrieve_case_impl,
    update_case_impl,
)
from .config import (
    api_analyzers_get,
    api_profiles_get,
    api_rules_get,
    api_targets_get,
)
from .disk_usage import api_disk_usage_get

_LOGGER = get_logger('server.api', root='helium')


def setup_api(webapp: Application):
    """Setup webapp routes"""
    _LOGGER.info("install helium api...")
    webapp.add_routes(
        [
            get('/api/case/{case_guid}/collectors', api_collectors_get),
            post('/api/case/{case_guid}/collector', api_collector_post),
            post(
                '/api/case/{case_guid}/collector/import',
                api_collector_import_post,
            ),
            get(
                '/api/case/{case_guid}/collector/{collector_guid}',
                api_collector_get,
            ),
            delete(
                '/api/case/{case_guid}/collector/{collector_guid}',
                api_collector_delete,
            ),
            get(
                '/api/case/{case_guid}/collector/{collector_guid}/secrets',
                api_collector_secrets_get,
            ),
            get(
                '/api/case/{case_guid}/collector/{collector_guid}/download',
                api_collector_download_get,
            ),
            get('/api/case/{case_guid}/collections', api_collections_get),
            post('/api/case/{case_guid}/collection', api_collection_post),
            delete(
                '/api/case/{case_guid}/collection/{collection_guid}',
                api_collection_delete,
            ),
            get(
                '/api/case/{case_guid}/collection/{collection_guid}',
                api_collection_get,
            ),
            put(
                '/api/case/{case_guid}/collection/{collection_guid}',
                api_collection_put,
            ),
            delete(
                '/api/case/{case_guid}/collection/{collection_guid}/cache',
                api_collection_cache_delete,
            ),
            get(
                '/api/case/{case_guid}/collection/{collection_guid}/download',
                api_collection_download_get,
            ),
            get(
                '/api/case/{case_guid}/collection/{collection_guid}/analyses',
                api_analyses_get,
            ),
            post(
                '/api/case/{case_guid}/collection/{collection_guid}/analysis',
                api_analysis_post,
            ),
            get(
                '/api/case/{case_guid}/collection/{collection_guid}/analysis/{analyzer}',
                api_analysis_get,
            ),
            delete(
                '/api/case/{case_guid}/collection/{collection_guid}/analysis/{analyzer}',
                api_analysis_delete,
            ),
            get(
                '/api/case/{case_guid}/collection/{collection_guid}/analysis/{analyzer}/log',
                api_analysis_log_get,
            ),
            put(
                '/api/case/{case_guid}/collection/{collection_guid}/analysis/{analyzer}',
                api_analysis_put,
            ),
            get(
                '/api/case/{case_guid}/collection/{collection_guid}/analysis/{analyzer}/download',
                api_analysis_download_get,
            ),
            get('/api/config/analyzers', api_analyzers_get),
            get('/api/config/{opsystem}/profiles', api_profiles_get),
            get('/api/config/{opsystem}/targets', api_targets_get),
            get('/api/config/{opsystem}/rules', api_rules_get),
            get('/api/disk_usage', api_disk_usage_get),
        ]
    )
    _LOGGER.info("helium api installed...")
