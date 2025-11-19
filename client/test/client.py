#!/usr/bin/env python3
"""Helium Test Client"""

from argparse import ArgumentParser
from asyncio import run, sleep
from pathlib import Path

from edf_fusion.client import (
    FusionAuthAPIClient,
    FusionCaseAPIClient,
    FusionClient,
    FusionClientConfig,
    FusionConstantAPIClient,
    FusionDownloadAPIClient,
    FusionInfoAPIClient,
    create_session,
)
from edf_fusion.helper.datetime import from_iso
from edf_fusion.helper.logging import get_logger
from edf_helium_core.concept import (
    Analysis,
    Case,
    Collection,
    Collector,
    Constant,
    Priority,
)
from generaptor.concept import Architecture, Distribution, OperatingSystem
from yarl import URL

from edf_helium_client import HeliumClient

_LOGGER = get_logger('client', root='test')
_TEST_FILE = Path(__file__).parent / 'auth.log.zip'
_TEST_OUTPUT_DIR = Path('/tmp')


async def _test_retrieve_info(fusion_client: FusionClient):
    fusion_info_api_client = FusionInfoAPIClient(fusion_client=fusion_client)
    info = await fusion_info_api_client.info()
    _LOGGER.info("retrieved info: %s", info)


async def _test_retrieve_constant(fusion_client: FusionClient):
    fusion_constant_api_client = FusionConstantAPIClient(
        constant_cls=Constant, fusion_client=fusion_client
    )
    constant = await fusion_constant_api_client.constant()
    _LOGGER.info("retrieved constant: %s", constant)


async def _test_case_lifecycle(fusion_case_api_client: FusionCaseAPIClient):
    # create case
    case = await fusion_case_api_client.create_case(
        Case(tsid=None, name='T', description='D', acs={'test'})
    )
    _LOGGER.info("created case: %s", case)
    # update case
    case.report = 'test case report'
    case = await fusion_case_api_client.update_case(case)
    _LOGGER.info("updated case: %s", case)
    # retrieve case
    case = await fusion_case_api_client.retrieve_case(case.guid)
    _LOGGER.info("retrieved case: %s", case)
    # enumerate cases
    cases = await fusion_case_api_client.enumerate_cases()
    _LOGGER.info("enumerated cases: %s", cases)
    # delete case
    deleted = await fusion_case_api_client.delete_case(case.guid)
    _LOGGER.info("case deleted: %s", deleted)
    # enumerate cases
    cases = await fusion_case_api_client.enumerate_cases()
    _LOGGER.info("enumerated cases: %s", cases)


async def _test_retrieve_disk_usage(helium_client: HeliumClient):
    disk_usage = await helium_client.retrieve_disk_usage()
    _LOGGER.info("disk usage: %s", disk_usage)


async def _test_collector_lifecycle(
    helium_client: HeliumClient,
    fusion_download_api_client: FusionDownloadAPIClient,
    case: Case,
):
    # retrieve profiles
    profiles = await helium_client.retrieve_profiles(OperatingSystem.LINUX)
    _LOGGER.info("retrieved profiles: %s", profiles)
    profile = profiles[0]
    # retrieve targets
    targets = await helium_client.retrieve_targets(OperatingSystem.LINUX)
    _LOGGER.info("retrieved targets: %s", targets)
    # retrieve rules
    rules = await helium_client.retrieve_rules(OperatingSystem.LINUX)
    _LOGGER.info("retrieved rules: %s", rules)
    # create collector
    collector = Collector(
        profile=profile.name,
        distrib=Distribution(
            arch=Architecture.AMD64,
            opsystem=OperatingSystem.LINUX,
        ),
    )
    collector = await helium_client.create_collector(case.guid, collector)
    _LOGGER.info("created collector: %s", collector)
    # download collector
    pdk = await helium_client.download_collector(case.guid, collector.guid)
    output = await fusion_download_api_client.download(pdk, _TEST_OUTPUT_DIR)
    _LOGGER.info("downloaded collector: %s", output)
    # retrieve collector
    collector = await helium_client.retrieve_collector(
        case.guid, collector.guid
    )
    _LOGGER.info("retrieved collector: %s", collector)
    # retrieve collector secrets
    collector_secrets = await helium_client.retrieve_collector_secrets(
        case.guid, collector.guid
    )
    _LOGGER.info("retrieved collector secrets: %s", collector_secrets)
    # retrieve collectors
    collectors = await helium_client.retrieve_collectors(case.guid)
    _LOGGER.info("retrieved collectors: %s", collectors)
    # delete collector
    deleted = await helium_client.delete_collector(case.guid, collector.guid)
    _LOGGER.info("collector deleted: %s", deleted)


async def _test_collection_lifecycle(
    helium_client: HeliumClient,
    fusion_download_api_client: FusionDownloadAPIClient,
    case: Case,
):
    # create collection
    collection = await helium_client.create_collection(case.guid, _TEST_FILE)
    _LOGGER.info("created collection: %s", collection)
    # update collection
    collection.tags.add(OperatingSystem.LINUX.value)
    collection.opsystem = OperatingSystem.LINUX
    collection.hostname = 'HOSTNAME'
    collection.collected = from_iso('2025-01-31T10:30:00Z')
    collection = await helium_client.update_collection(case.guid, collection)
    _LOGGER.info("updated collection: %s", collection)
    # download collection
    pdk = await helium_client.download_collection(case.guid, collection.guid)
    output = await fusion_download_api_client.download(pdk, _TEST_OUTPUT_DIR)
    _LOGGER.info("downloaded collection: %s", output)
    # retrieve collection
    collection = await helium_client.retrieve_collection(
        case.guid, collection.guid
    )
    _LOGGER.info("retrieved collection: %s", collection)
    # retrieve collections
    collections = await helium_client.retrieve_collections(case.guid)
    _LOGGER.info("retrieved collections: %s", collections)
    # delete collection
    deleted = await helium_client.delete_collection(case.guid, collection.guid)
    _LOGGER.info("collection deleted: %s", deleted)


async def _wait_for_analysis(
    helium_client: HeliumClient,
    case: Case,
    collection: Collection,
    analysis: Analysis,
):
    while True:
        analysis = await helium_client.retrieve_analysis(
            case.guid, collection.guid, analysis.analyzer
        )
        if analysis.completed:
            _LOGGER.info("analysis completed (%s)", analysis.status)
            break
        _LOGGER.info("waiting for analysis to complete (%s)", analysis.status)
        await sleep(5)


async def _test_analyzer_lifecyle(
    helium_client: HeliumClient,
    fusion_download_api_client: FusionDownloadAPIClient,
    case: Case,
    collection: Collection,
):
    # retrieve analyzers
    analyzers = await helium_client.retrieve_analyzers()
    _LOGGER.info("retrieved analyzers: %s", analyzers)
    # create analysis
    assert 'plasma' in {analyzer.name for analyzer in analyzers}
    analysis = Analysis(analyzer='plasma', priority=Priority.HIGH)
    analysis = await helium_client.create_analysis(
        case.guid, collection.guid, analysis
    )
    _LOGGER.info("created analysis: %s", analysis)
    # retrieve analyses
    analyses = await helium_client.retrieve_analyses(
        case.guid, collection.guid
    )
    _LOGGER.info("retrieved analyses: %s", analyses)
    # wait for analysis to complete
    await _wait_for_analysis(helium_client, case, collection, analysis)
    # retrieve analysis log
    output = await helium_client.retrieve_analysis_log(
        case.guid, collection.guid, analysis.analyzer, _TEST_OUTPUT_DIR
    )
    _LOGGER.info("retrieved analysis log: %s", output)
    # download analysis data
    pdk = await helium_client.download_analysis(
        case.guid, collection.guid, analysis.analyzer
    )
    output = await fusion_download_api_client.download(pdk, _TEST_OUTPUT_DIR)
    _LOGGER.info("downloaded analysis: %s", output)
    # delete collection cache
    deleted = await helium_client.delete_collection_cache(
        case.guid, collection.guid
    )
    _LOGGER.info("collection cache deleted: %s", deleted)
    # update analysis
    analysis.priority = Priority.MEDIUM
    analysis = await helium_client.update_analysis(
        case.guid, collection.guid, analysis
    )
    _LOGGER.info("updated analysis: %s", analysis)
    # wait for analysis to complete
    await _wait_for_analysis(helium_client, case, collection, analysis)
    # delete analysis
    deleted = await helium_client.delete_analysis(
        case.guid, collection.guid, analysis.analyzer
    )
    _LOGGER.info("analysis deleted: %s", deleted)


async def _playbook(fusion_client: FusionClient):
    fusion_case_api_client = FusionCaseAPIClient(
        case_cls=Case, fusion_client=fusion_client
    )
    fusion_download_api_client = FusionDownloadAPIClient(
        fusion_client=fusion_client
    )
    helium_client = HeliumClient(fusion_client=fusion_client)
    await _test_retrieve_info(fusion_client)
    await _test_retrieve_constant(fusion_client)
    await _test_retrieve_disk_usage(helium_client)
    await _test_case_lifecycle(fusion_case_api_client)
    case = await fusion_case_api_client.create_case(
        Case(tsid=None, name='T', description='D', acs={'test'})
    )
    _LOGGER.info("created case: %s", case)
    input("execution paused, press enter to continue!")
    await _test_collector_lifecycle(
        helium_client, fusion_download_api_client, case
    )
    await _test_collection_lifecycle(
        helium_client, fusion_download_api_client, case
    )
    collection = await helium_client.create_collection(case.guid, _TEST_FILE)
    _LOGGER.info("created collection: %s", collection)
    collection.tags.add(OperatingSystem.LINUX.value)
    collection.hostname = 'HOSTNAME'
    collection = await helium_client.update_collection(case.guid, collection)
    _LOGGER.info("updated collection: %s", collection)
    await _test_analyzer_lifecyle(
        helium_client, fusion_download_api_client, case, collection
    )
    await helium_client.delete_collection(case.guid, collection.guid)
    await fusion_case_api_client.delete_case(case.guid)


def _parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        '--api-url',
        type=URL,
        default=URL('http://helium.domain.lan/'),
        help="API URL",
    )
    return parser.parse_args()


async def app():
    """Application entrypoint"""
    args = _parse_args()
    config = FusionClientConfig(api_url=args.api_url)
    session = create_session(config, unsafe=True)
    async with session:
        fusion_client = FusionClient(config=config, session=session)
        fusion_auth_api_client = FusionAuthAPIClient(
            fusion_client=fusion_client
        )
        identity = await fusion_auth_api_client.login('test', 'test')
        if not identity:
            return
        _LOGGER.info("logged as: %s", identity)
        try:
            await _playbook(fusion_client)
        finally:
            await fusion_auth_api_client.logout()


if __name__ == '__main__':
    run(app())
