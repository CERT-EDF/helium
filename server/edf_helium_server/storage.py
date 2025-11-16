"""Helium Storage"""

from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Type
from uuid import UUID
from zipfile import BadZipFile

from edf_fusion.concept import AnalyzerInfo
from edf_fusion.helper.filesystem import GUID_GLOB, iter_guid_items
from edf_fusion.helper.logging import get_logger
from edf_fusion.helper.streaming import stream_to_file
from edf_fusion.helper.zip import create_zip
from edf_fusion.server.storage import ConceptStorage, FusionStorage
from edf_helium_core.concept import (
    Analysis,
    Architecture,
    Case,
    Collection,
    Collector,
    CollectorSecrets,
    DiskUsage,
    OperatingSystem,
)
from generaptor.concept import Distribution

from .config import HeliumStorageConfig
from .helper.generaptor import GCache, GConfig, Generaptor

_LOGGER = get_logger('server.storage', root='helium')
_CHUNK_SIZE = 64 * 1024


def _storage_instances(
    directory: Path,
    storage_cls: Type[ConceptStorage],
    pattern: str,
) -> Iterator[ConceptStorage]:
    if not directory:
        return
    for item in directory.glob(pattern):
        if not item.is_dir():
            continue
        yield storage_cls(directory=item)


@dataclass(kw_only=True)
class AnalysisStorage(ConceptStorage):
    """Analysis Storage"""

    @cached_property
    def log(self) -> Path:
        """Analyzer log file"""
        return self.directory / 'analysis.log'

    def create_archive(self):
        """Create analyzer output archive"""
        create_zip(
            self.data,
            self.directory,
            files=[self.log],
            directories=[self.data_dir],
        )


@dataclass(kw_only=True)
class CollectionStorage(ConceptStorage):
    """Case Storage"""

    @cached_property
    def analysis_dir(self) -> Path:
        """Collection analysis directory"""
        return self.directory / 'analysis'

    def analyses(self) -> Iterator[AnalysisStorage]:
        """Collection analyses"""
        yield from _storage_instances(self.analysis_dir, AnalysisStorage, '*')


@dataclass(kw_only=True)
class CollectorStorage(ConceptStorage):
    """Collector Storage"""

    @cached_property
    def config(self) -> Path | None:
        """Collector config"""
        if not self.data_dir.is_dir():
            return None
        try:
            return next(self.data_dir.glob('collector-*.yml'))
        except StopIteration:
            return None

    @cached_property
    def secrets(self) -> Path:
        """Collector secrets file"""
        return self.directory / 'secrets.json'

    @cached_property
    def executable(self) -> Path | None:
        """Collector executable file"""
        if not self.data_dir.is_dir():
            return None
        try:
            return next(self.data_dir.glob('collector-*-*-*.zip'))
        except StopIteration:
            return None


@dataclass(kw_only=True)
class CaseStorage(ConceptStorage):
    """Case Storage"""

    @cached_property
    def collector_dir(self) -> Path:
        """Case Collector Directory"""
        return self.directory / 'collector'

    @cached_property
    def collection_dir(self) -> Path:
        """Case Collection Directory"""
        return self.directory / 'collection'

    def collectors(self) -> Iterator[CollectorStorage]:
        """Case Collectors"""
        yield from _storage_instances(
            self.collector_dir, CollectorStorage, GUID_GLOB
        )

    def collections(self) -> Iterator[CollectionStorage]:
        """Case Collections"""
        yield from _storage_instances(
            self.collection_dir, CollectionStorage, GUID_GLOB
        )


@dataclass(kw_only=True)
class Storage(FusionStorage):
    """File System Storage"""

    config: HeliumStorageConfig

    @cached_property
    def generaptor(self) -> Generaptor:
        """Generaptor helper"""
        return Generaptor(
            cache=GCache(self.config.generaptor.cache),
            config=GConfig(self.config.generaptor.config),
        )

    @cached_property
    def disk_usage(self) -> Path:
        """Disk usage file"""
        return self.cache_dir / 'disk_usage.json'

    def case_storage(self, case_guid: UUID) -> CaseStorage:
        """Retrieve case storage"""
        directory = self.config.directory / str(case_guid)
        return CaseStorage(directory=directory)

    def collector_storage(
        self, case_guid: UUID, collector_guid: UUID
    ) -> CollectorStorage:
        """Retrieve collector storage"""
        case_storage = self.case_storage(case_guid)
        directory = case_storage.collector_dir / str(collector_guid)
        return CollectorStorage(directory=directory)

    def collection_storage(
        self, case_guid: UUID, collection_guid: UUID
    ) -> CollectionStorage:
        """Retrieve collection storage"""
        case_storage = self.case_storage(case_guid)
        directory = case_storage.collection_dir / str(collection_guid)
        return CollectionStorage(directory=directory)

    def analysis_storage(
        self, case_guid: UUID, collection_guid: UUID, analyzer: str
    ) -> AnalysisStorage:
        """Retrieve analysis storage"""
        collection_storage = self.collection_storage(
            case_guid, collection_guid
        )
        directory = collection_storage.analysis_dir / analyzer
        return AnalysisStorage(directory=directory)

    async def attach_case(self, case_guid: UUID, next_case_guid: UUID) -> bool:
        case = await self.retrieve_case(case_guid)
        if case.managed:
            _LOGGER.warning(
                "prevented an attempt to attach a managed case: %s => %s",
                case_guid,
                next_case_guid,
            )
            return False
        case_storage = self.case_storage(case_guid)
        # rename case directory
        next_directory = case_storage.directory.parent / str(next_case_guid)
        try:
            case_storage.directory.rename(next_directory)
        except FileExistsError:
            _LOGGER.warning(
                "prevented attach logic to replace an existing case: %s => %s",
                case_guid,
                next_case_guid,
            )
            return False
        # update case metadata
        case_storage = self.case_storage(next_case_guid)
        case.guid = next_case_guid
        case.managed = True
        case.to_filepath(case_storage.metadata)
        return True

    async def create_case(self, managed: bool, dct) -> Case | None:
        if managed:
            case = Case.from_dict(dct)
        else:
            case = Case(
                tsid=dct.get('tsid'),
                name=dct['name'],
                description=dct['description'],
                acs=set(dct.get('acs', [])),
                report=dct.get('report'),
            )
        case_storage = self.case_storage(case.guid)
        case_storage.create()
        case.to_filepath(case_storage.metadata)
        return case

    async def update_case(self, case_guid: UUID, dct) -> Case | None:
        case_storage = self.case_storage(case_guid)
        metadata = case_storage.metadata
        if not metadata.is_file():
            _LOGGER.error("case metadata not found: %s", metadata)
            return None
        case = Case.from_filepath(metadata)
        case.update(dct)
        case.to_filepath(metadata)
        return case

    async def delete_case(self, case_guid: UUID) -> bool:
        case_storage = self.case_storage(case_guid)
        case_storage.remove()
        return True

    async def retrieve_case(self, case_guid: UUID) -> Case | None:
        case_storage = self.case_storage(case_guid)
        metadata = case_storage.metadata
        if not metadata.is_file():
            _LOGGER.error("case metadata not found: %s", metadata)
            return None
        return Case.from_filepath(metadata)

    async def enumerate_cases(self) -> AsyncIterator[Case]:
        for directory in iter_guid_items(self.config.directory):
            if not directory.is_dir():
                continue
            metadata = CaseStorage(directory=directory).metadata
            if not metadata.is_file():
                continue
            yield Case.from_filepath(metadata)

    async def create_collector(self, case_guid: UUID, dct) -> Collector | None:
        """Create case collector"""
        collector = Collector(
            profile=dct['profile'],
            distrib=Distribution(
                arch=Architecture(dct.get('arch', Architecture.AMD64)),
                opsystem=OperatingSystem(dct['opsystem']),
            ),
            device=dct.get('device', ''),
            memdump=dct.get('memdump', False),
            dont_be_lazy=dct.get('dont_be_lazy'),
            vss_analysis_age=dct.get('vss_analysis_age'),
            use_auto_accessor=dct.get('use_auto_accessor'),
            description=dct.get('description'),
        )
        collector_storage = self.collector_storage(case_guid, collector.guid)
        collector_storage.create()
        collector_storage.data_dir.mkdir()
        collector_secrets = self.generaptor.generate_collector_secrets()
        fingerprint = self.generaptor.generate_collector(
            collector, collector_secrets, collector_storage.data_dir
        )
        if not fingerprint:
            _LOGGER.error("collector generation failed")
            collector_storage.remove()
            return None
        collector.fingerprint = fingerprint
        collector_secrets.to_filepath(collector_storage.secrets)
        collector.to_filepath(collector_storage.metadata)
        return collector

    async def delete_collector(
        self, case_guid: UUID, collector_guid: UUID
    ) -> bool:
        """Delete collector"""
        collector_storage = self.collector_storage(case_guid, collector_guid)
        collector_storage.remove()
        return True

    async def import_collector(self, case_guid: UUID, dct) -> Collector | None:
        """Import case collector"""
        try:
            collector = Collector(
                profile=None,
                distrib=Distribution(
                    arch=Architecture(dct['arch']),
                    opsystem=OperatingSystem(dct['opsystem']),
                ),
                fingerprint=dct['fingerprint'],
                description=dct['description'],
            )
            collector_secrets = CollectorSecrets.from_dict(dct)
        except KeyError:
            _LOGGER.error("missing keys in imported collector metadata")
            return None
        collector_storage = self.collector_storage(case_guid, collector.guid)
        collector_storage.create()
        collector_secrets.to_filepath(collector_storage.secrets)
        collector.to_filepath(collector_storage.metadata)
        return collector

    async def retrieve_collector(
        self, case_guid: UUID, collector_guid: UUID
    ) -> Collector | None:
        """Retrieve case collector"""
        collector_storage = self.collector_storage(case_guid, collector_guid)
        metadata = collector_storage.metadata
        if not metadata.is_file():
            _LOGGER.error("collection metadata not found: %s", metadata)
            return None
        return Collector.from_filepath(metadata)

    async def retrieve_collector_secrets(
        self, case_guid: UUID, collector_guid: UUID
    ) -> CollectorSecrets | None:
        """Retrieve case collector secrets"""
        collector_storage = self.collector_storage(case_guid, collector_guid)
        secrets = collector_storage.secrets
        if not secrets.is_file():
            _LOGGER.error("collector secrets not found: %s", secrets)
            return None
        return CollectorSecrets.from_filepath(secrets)

    async def retrieve_collector_executable(
        self, case_guid: UUID, collector_guid: UUID
    ) -> Path | None:
        """Retrieve case collector content"""
        collector_storage = self.collector_storage(case_guid, collector_guid)
        return collector_storage.executable

    async def enumerate_collectors(
        self, case_guid: UUID
    ) -> AsyncIterator[Collector]:
        """Enumerate case collectors"""
        case_storage = self.case_storage(case_guid)
        for collector_storage in case_storage.collectors():
            metadata = collector_storage.metadata
            if not metadata.is_file():
                continue
            yield Collector.from_filepath(metadata)

    async def create_collection(
        self, case_guid: UUID, content: AsyncIterator[bytes]
    ) -> Collection | None:
        """Create case collection"""
        collection = Collection()
        collection_storage = self.collection_storage(
            case_guid, collection.guid
        )
        collection_storage.create()
        data = collection_storage.data
        size = await stream_to_file(data, content)
        if size is None:
            _LOGGER.error("file upload failed")
            return None
        try:
            self.generaptor.copy_zip_metadata(collection, data)
        except BadZipFile:
            _LOGGER.error("collection shall be a zip archive")
            collection_storage.remove()
            return None
        collection.to_filepath(collection_storage.metadata)
        return collection

    async def update_collection(
        self, case_guid: UUID, collection_guid: UUID, dct
    ) -> Collection | None:
        """Update case collection"""
        collection_storage = self.collection_storage(
            case_guid, collection_guid
        )
        metadata = collection_storage.metadata
        if not metadata.is_file():
            _LOGGER.error("collection metadata not found: %s", metadata)
            return None
        collection = Collection.from_filepath(metadata)
        collection.update(dct)
        collection.to_filepath(metadata)
        return collection

    async def delete_collection(
        self, case_guid: UUID, collection_guid: UUID
    ) -> bool:
        """Delete collection"""
        collection_storage = self.collection_storage(
            case_guid, collection_guid
        )
        collection_storage.remove()
        return True

    async def retrieve_collection(
        self, case_guid: UUID, collection_guid: UUID
    ) -> Collection | None:
        """Retrieve case collection"""
        collection_storage = self.collection_storage(
            case_guid, collection_guid
        )
        metadata = collection_storage.metadata
        if not metadata.is_file():
            _LOGGER.error("collection metadata not found: %s", metadata)
            return None
        return Collection.from_filepath(metadata)

    async def retrieve_collection_data(
        self, case_guid: UUID, collection_guid: UUID
    ) -> Path | None:
        """Retrieve case collection content"""
        collection_storage = self.collection_storage(
            case_guid, collection_guid
        )
        data = collection_storage.data
        if not data.is_file():
            _LOGGER.error("collection data not found: %s", data)
            return None
        return data

    async def delete_collection_cache(
        self, case_guid: UUID, collection_guid: UUID
    ) -> bool:
        """Delete case collection cache"""
        collection_storage = self.collection_storage(
            case_guid, collection_guid
        )
        if not collection_storage.data_dir.is_dir():
            return False
        collection_storage.remove_data_dir()
        return True

    async def enumerate_collections(
        self, case_guid: UUID
    ) -> AsyncIterator[Collection]:
        """Retrieve case collections"""
        case_storage = self.case_storage(case_guid)
        for collection_storage in case_storage.collections():
            metadata = collection_storage.metadata
            if not metadata.is_file():
                continue
            yield Collection.from_filepath(metadata)

    async def create_analysis(
        self, case_guid: UUID, collection_guid: UUID, dct
    ) -> Analysis | None:
        """Create case collection analysis"""
        analysis = Analysis(analyzer=dct['analyzer'])
        analysis_storage = self.analysis_storage(
            case_guid, collection_guid, analysis.analyzer
        )
        metadata = analysis_storage.metadata
        if metadata.is_file():
            _LOGGER.error("analysis metadata found: %s", metadata)
            return None
        analysis_storage.create()
        analysis.to_filepath(analysis_storage.metadata)
        return analysis

    async def update_analysis(
        self,
        case_guid: UUID,
        collection_guid: UUID,
        analyzer: str,
        dct,
    ) -> Analysis | None:
        """Restart case collection analysis"""
        analysis_storage = self.analysis_storage(
            case_guid, collection_guid, analyzer
        )
        metadata = analysis_storage.metadata
        if not metadata.is_file():
            _LOGGER.error("analysis metadata not found: %s", metadata)
            return None
        analysis = Analysis.from_filepath(metadata)
        analysis.update(dct)
        analysis.to_filepath(metadata)
        return analysis

    async def delete_analysis(
        self, case_guid: UUID, collection_guid: UUID, analyzer: str
    ) -> bool:
        """Delete analysis"""
        analysis_storage = self.analysis_storage(
            case_guid, collection_guid, analyzer
        )
        analysis_storage.remove()
        return True

    async def retrieve_analysis(
        self, case_guid: UUID, collection_guid: UUID, analyzer: str
    ) -> Analysis | None:
        """Retrieve case collection analysis"""
        analysis_storage = self.analysis_storage(
            case_guid, collection_guid, analyzer
        )
        metadata = analysis_storage.metadata
        if not metadata.is_file():
            _LOGGER.error("analysis metadata not found: %s", metadata)
            return None
        return Analysis.from_filepath(metadata)

    async def retrieve_analysis_data(
        self, case_guid: UUID, collection_guid: UUID, analyzer: str
    ) -> Path | None:
        """Retrieve case collection analysis"""
        analysis_storage = self.analysis_storage(
            case_guid, collection_guid, analyzer
        )
        data = analysis_storage.data
        if not data.is_file():
            _LOGGER.error("analysis data not found: %s", data)
            return None
        return data

    async def enumerate_analyses(
        self, case_guid: UUID, collection_guid: UUID
    ) -> AsyncIterator[Analysis]:
        """Retrieve case collection analysis"""
        collection_storage = self.collection_storage(
            case_guid, collection_guid
        )
        for analysis_storage in collection_storage.analyses():
            metadata = analysis_storage.metadata
            if not metadata.is_file():
                continue
            yield Analysis.from_filepath(metadata)

    async def register_analyzer(self, info: AnalyzerInfo):
        """Register an analyzer"""
        self.cache_dir.mkdir(parents=False, exist_ok=True)
        metadata = self.cache_dir / f'analyzer_{info.name}.json'
        info.to_filepath(metadata)

    async def enumerate_analyzers(self) -> AsyncIterator[AnalyzerInfo]:
        """Enumerate registered analyzers"""
        for metadata in self.cache_dir.glob('analyzer_*.json'):
            yield AnalyzerInfo.from_filepath(metadata)

    async def retrieve_disk_usage(self) -> DiskUsage | None:
        """Retrieve disk usage"""
        if self.disk_usage.is_file():
            return DiskUsage.from_filepath(self.disk_usage)
