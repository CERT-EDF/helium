"""Helium Client"""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from aiohttp import FormData
from edf_fusion.client import FusionClient
from edf_fusion.concept import AnalyzerInfo, Identity, PendingDownloadKey
from edf_fusion.helper.logging import get_logger
from edf_helium_core.concept import (
    Analysis,
    Collection,
    Collector,
    CollectorSecrets,
    DiskUsage,
    Profile,
    Rule,
    Target,
)
from generaptor.concept import Architecture, OperatingSystem

_LOGGER = get_logger('client', root='carbon')


@dataclass(kw_only=True)
class HeliumClient:
    """Helium Client"""

    fusion_client: FusionClient

    async def create_collector(
        self, case_guid: UUID, collector: Collector
    ) -> Collector:
        """Create collector"""
        _LOGGER.info("creating collector in case %s", case_guid)
        endpoint = f'/api/case/{case_guid}/collector'
        return await self.fusion_client.post(endpoint, collector, Collector)

    async def import_collector(
        self,
        case_guid: UUID,
        collector: Collector,
        secrets: CollectorSecrets,
    ) -> Collector:
        """Import collector information for collection processing"""
        _LOGGER.info("importing collector in case %s", case_guid)
        endpoint = f'/api/case/{case_guid}/collector/import'
        dct = collector.to_dict()
        dct.update(secrets.to_dict())
        return await self.fusion_client.post(
            endpoint, json=dct, concept_cls=Collector
        )

    async def download_collector(
        self, case_guid: UUID, collector_guid: UUID
    ) -> PendingDownloadKey | None:
        """Download collector"""
        _LOGGER.info(
            "downloading collector %s in case %s", collector_guid, case_guid
        )
        endpoint = f'/api/case/{case_guid}/collector/{collector_guid}/download'
        return await self.fusion_client.get(
            endpoint, concept_cls=PendingDownloadKey
        )

    async def delete_collector(
        self, case_guid: UUID, collector_guid: UUID
    ) -> bool:
        """Delete collector"""
        _LOGGER.info(
            "deleting collector %s in case %s", collector_guid, case_guid
        )
        endpoint = f'/api/case/{case_guid}/collector/{collector_guid}'
        return await self.fusion_client.delete(endpoint)

    async def retrieve_collector(
        self, case_guid: UUID, collector_guid: UUID
    ) -> Collector | None:
        """Retrieve collector"""
        endpoint = f'/api/case/{case_guid}/collector/{collector_guid}'
        return await self.fusion_client.get(endpoint, concept_cls=Collector)

    async def retrieve_collector_secrets(
        self, case_guid: UUID, collector_guid: UUID
    ) -> CollectorSecrets:
        """Retrieve collector secrets"""
        _LOGGER.info(
            "retrieving secrets for collector %s in case %s",
            collector_guid,
            case_guid,
        )
        endpoint = f'/api/case/{case_guid}/collector/{collector_guid}/secrets'
        return await self.fusion_client.get(
            endpoint, concept_cls=CollectorSecrets
        )

    async def retrieve_collectors(
        self, case_guid: UUID
    ) -> list[Collector] | None:
        """Retrieve collectors"""
        endpoint = f'/api/case/{case_guid}/collectors'
        return await self.fusion_client.get(endpoint, concept_cls=Collector)

    async def create_collection(
        self, case_guid: UUID, filepath: Path
    ) -> Collection | None:
        """Create collection"""
        _LOGGER.info("uploading collection %s in case %s", filepath, case_guid)
        data = FormData()
        data.add_field('file', filepath.open('rb'), filename=filepath.name)
        endpoint = f'/api/case/{case_guid}/collection'
        return await self.fusion_client.post(
            endpoint, data=data, concept_cls=Collection
        )

    async def update_collection(
        self, case_guid: UUID, collection: Collection
    ) -> Collection | None:
        """Update collection"""
        _LOGGER.info(
            "updating collection %s in case %s", collection.guid, case_guid
        )
        endpoint = f'/api/case/{case_guid}/collection/{collection.guid}'
        return await self.fusion_client.put(endpoint, collection, Collection)

    async def download_collection(
        self, case_guid: UUID, collection_guid: UUID
    ) -> PendingDownloadKey | None:
        """Download collection"""
        _LOGGER.info(
            "downloading collection %s in case %s", collection_guid, case_guid
        )
        endpoint = (
            f'/api/case/{case_guid}/collection/{collection_guid}/download'
        )
        return await self.fusion_client.get(
            endpoint, concept_cls=PendingDownloadKey
        )

    async def delete_collection_cache(
        self, case_guid: UUID, collection_guid: UUID
    ) -> bool:
        """Delete collection cache"""
        _LOGGER.info(
            "deleting cache for collection %s in case %s",
            collection_guid,
            case_guid,
        )
        endpoint = f'/api/case/{case_guid}/collection/{collection_guid}/cache'
        return await self.fusion_client.delete(endpoint)

    async def delete_collection(
        self, case_guid: UUID, collection_guid: UUID
    ) -> bool:
        """Delete collection"""
        _LOGGER.info(
            "deleting collection %s in case %s", collection_guid, case_guid
        )
        endpoint = f'/api/case/{case_guid}/collection/{collection_guid}'
        return await self.fusion_client.delete(endpoint)

    async def retrieve_collection(
        self, case_guid: UUID, collection_guid: UUID
    ) -> Collection | None:
        """Retrieve collection"""
        endpoint = f'/api/case/{case_guid}/collection/{collection_guid}'
        return await self.fusion_client.get(endpoint, concept_cls=Collection)

    async def retrieve_collections(
        self, case_guid: UUID
    ) -> list[Collection] | None:
        """Retrieve collections"""
        endpoint = f'/api/case/{case_guid}/collections'
        return await self.fusion_client.get(endpoint, concept_cls=Collection)

    async def create_analysis(
        self, case_guid: UUID, collection_guid: UUID, analysis: Analysis
    ) -> Analysis | None:
        """Create analysis"""
        _LOGGER.info(
            "creating analysis %s for collection %s in case %s",
            analysis.analyzer,
            collection_guid,
            case_guid,
        )
        endpoint = (
            f'/api/case/{case_guid}/collection/{collection_guid}/analysis'
        )
        return await self.fusion_client.post(
            endpoint, analysis, concept_cls=Analysis
        )

    async def update_analysis(
        self, case_guid: UUID, collection_guid: UUID, analysis: Analysis
    ) -> Analysis | None:
        """Update analysis"""
        _LOGGER.info(
            "updating analysis %s for collection %s in case %s",
            analysis.analyzer,
            collection_guid,
            case_guid,
        )
        analyzer = analysis.analyzer
        endpoint = f'/api/case/{case_guid}/collection/{collection_guid}/analysis/{analyzer}'
        return await self.fusion_client.put(
            endpoint, analysis, concept_cls=Analysis
        )

    async def download_analysis(
        self, case_guid: UUID, collection_guid: UUID, analyzer: str
    ) -> PendingDownloadKey | None:
        """Download analysis"""
        _LOGGER.info(
            "downloading analysis %s for collection %s in case %s",
            analyzer,
            collection_guid,
            case_guid,
        )
        endpoint = f'/api/case/{case_guid}/collection/{collection_guid}/analysis/{analyzer}/download'
        return await self.fusion_client.get(
            endpoint, concept_cls=PendingDownloadKey
        )

    async def delete_analysis(
        self, case_guid: UUID, collection_guid: UUID, analyzer: str
    ) -> bool:
        """Delete analysis"""
        _LOGGER.info(
            "deleting analysis %s for collection %s in case %s",
            analyzer,
            collection_guid,
            case_guid,
        )
        endpoint = f'/api/case/{case_guid}/collection/{collection_guid}/analysis/{analyzer}'
        return await self.fusion_client.delete(endpoint)

    async def retrieve_analysis(
        self, case_guid: UUID, collection_guid: UUID, analyzer: str
    ) -> Analysis | None:
        """Retrieve analysis"""
        endpoint = f'/api/case/{case_guid}/collection/{collection_guid}/analysis/{analyzer}'
        return await self.fusion_client.get(endpoint, concept_cls=Analysis)

    async def retrieve_analysis_log(
        self,
        case_guid: UUID,
        collection_guid: UUID,
        analyzer: str,
        output: Path,
    ) -> Path | None:
        """Retrieve analysis log"""
        endpoint = f'/api/case/{case_guid}/collection/{collection_guid}/analysis/{analyzer}/log'
        return await self.fusion_client.download(endpoint, output)

    async def retrieve_analyses(
        self, case_guid: UUID, collection_guid: UUID
    ) -> list[Analysis] | None:
        """Retrieve analyses"""
        endpoint = (
            f'/api/case/{case_guid}/collection/{collection_guid}/analyses'
        )
        return await self.fusion_client.get(endpoint, concept_cls=Analysis)

    async def retrieve_analyzers(self) -> list[AnalyzerInfo]:
        """Retrieve analyzers"""
        endpoint = '/api/config/analyzers'
        return await self.fusion_client.get(endpoint, concept_cls=AnalyzerInfo)

    async def retrieve_profiles(
        self, opsystem: OperatingSystem
    ) -> list[Profile] | None:
        """Retrieve profiles"""
        endpoint = f'/api/config/{opsystem.value}/profiles'
        return await self.fusion_client.get(endpoint, concept_cls=Profile)

    async def retrieve_targets(
        self, opsystem: OperatingSystem
    ) -> list[Target] | None:
        """Retrieve targets"""
        endpoint = f'/api/config/{opsystem.value}/targets'
        return await self.fusion_client.get(endpoint, concept_cls=Target)

    async def retrieve_rules(
        self, opsystem: OperatingSystem
    ) -> list[Rule] | None:
        """Retrieve rules"""
        endpoint = f'/api/config/{opsystem.value}/rules'
        return await self.fusion_client.get(endpoint, concept_cls=Rule)

    async def retrieve_disk_usage(self) -> DiskUsage | None:
        """Retrieve disk usage"""
        endpoint = '/api/disk_usage'
        return await self.fusion_client.get(endpoint, concept_cls=DiskUsage)
