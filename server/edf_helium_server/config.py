"""Configuration"""

from dataclasses import dataclass
from pathlib import Path
from typing import Self

from aiohttp.web import Application, Request
from edf_fusion.helper.logging import get_logger
from edf_fusion.helper.serializing import Loadable
from edf_fusion.server.auth import FusionAuthAPIConfig
from edf_fusion.server.case import FusionCaseAPIConfig
from edf_fusion.server.config import (
    FusionAnalyzerMapping,
    FusionServerConfig,
    FusionStorageConfig,
    FusionSynchronizerConfig,
)
from edf_fusion.server.constant import FusionConstantAPIConfig
from edf_fusion.server.download import FusionDownloadAPIConfig
from edf_fusion.server.event import FusionEventAPIConfig
from edf_fusion.server.info import FusionInfoAPIConfig

_LOGGER = get_logger('server.config', root='helium')
_HELIUM_CONFIG = '__helium_config'


@dataclass(kw_only=True)
class GeneraptorConfig(Loadable):
    """Generaptor configuration"""

    cache: Path
    config: Path

    @classmethod
    def from_dict(cls, dct: dict) -> Self:
        return cls(
            cache=Path(dct['cache']),
            config=Path(dct['config']),
        )


@dataclass(kw_only=True)
class HeliumStorageConfig(FusionStorageConfig):
    """Storage configuration"""

    generaptor: GeneraptorConfig | None = None

    @classmethod
    def from_dict(cls, dct: dict) -> Self:
        config = super().from_dict(dct)
        config.generaptor = GeneraptorConfig.from_dict(dct['generaptor'])
        return config


@dataclass(kw_only=True)
class HeliumServerConfig(Loadable):
    """Helium Server configuration"""

    server: FusionServerConfig
    storage: HeliumStorageConfig
    auth_api: FusionAuthAPIConfig
    case_api: FusionCaseAPIConfig
    info_api: FusionInfoAPIConfig
    event_api: FusionEventAPIConfig
    constant_api: FusionConstantAPIConfig
    download_api: FusionDownloadAPIConfig
    synchronizer: FusionSynchronizerConfig
    analyzer: FusionAnalyzerMapping

    @classmethod
    def from_dict(cls, dct: dict) -> Self:
        return cls(
            server=FusionServerConfig.from_dict(dct['server']),
            storage=HeliumStorageConfig.from_dict(dct['storage']),
            auth_api=FusionAuthAPIConfig.from_dict(dct['auth_api']),
            case_api=FusionCaseAPIConfig.from_dict(dct['case_api']),
            info_api=FusionInfoAPIConfig.from_dict(dct['info_api']),
            event_api=FusionEventAPIConfig.from_dict(dct['event_api']),
            constant_api=FusionConstantAPIConfig.from_dict(
                dct['constant_api']
            ),
            download_api=FusionDownloadAPIConfig.from_dict(
                dct['download_api']
            ),
            synchronizer=FusionSynchronizerConfig.from_dict(
                dct['synchronizer']
            ),
            analyzer=FusionAnalyzerMapping.from_dict(dct['analyzer']),
        )

    def setup(self, webapp: Application):
        """Register config in webapp context"""
        webapp[_HELIUM_CONFIG] = self


def get_helium_config(app_or_req: Application | Request) -> HeliumServerConfig:
    """Retrieve config from webapp context"""
    if isinstance(app_or_req, Request):
        app_or_req = app_or_req.app
    return app_or_req[_HELIUM_CONFIG]
