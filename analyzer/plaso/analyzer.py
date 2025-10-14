"""Helium Plaso Analyzer"""

from dataclasses import dataclass
from pathlib import Path

from edf_fusion.concept import AnalyzerInfo
from edf_fusion.helper.logging import get_logger
from edf_fusion.helper.subprocess import create_subprocess_and_wait
from edf_fusion.server.config import FusionAnalyzerConfig
from edf_helium_server.analyzer import Analyzer, AnalyzerTask
from edf_helium_server.storage import Storage

_LOGGER = get_logger('analyzer.plaso', root='helium')
_WORKER_LIMIT = 2
_WORKER_MEMORY_LIMIT = 2147483648
_PROCESS_MEMORY_LIMIT = 4294967296


@dataclass(kw_only=True)
class PlasoAnalyzerConfig(FusionAnalyzerConfig):
    """Plaso Analyzer Config"""

    program: Path | None = None

    @classmethod
    def from_dict(cls, dct):
        config = super().from_dict(dct)
        config.program = Path(dct['program'])
        return config


async def _plaso_process_impl(
    info: AnalyzerInfo,
    config: PlasoAnalyzerConfig,
    storage: Storage,
    a_task: AnalyzerTask,
) -> bool:
    collection_storage = storage.collection_storage(
        a_task.case.guid, a_task.collection.guid
    )
    analysis_storage = storage.analysis_storage(
        a_task.case.guid, a_task.collection.guid, a_task.analysis.analyzer
    )
    analysis_storage.data_dir.mkdir(parents=True, exist_ok=True)
    argv = [
        str(config.program),
        '-u',
        '--status-view',
        'none',
        '--workers',
        str(_WORKER_LIMIT),
        '--worker-memory-limit',
        str(_WORKER_MEMORY_LIMIT),
        '--process-memory-limit',
        str(_PROCESS_MEMORY_LIMIT),
        '--log-file',
        str(analysis_storage.log),
        '--storage-format',
        'sqlite',
        '--storage-file',
        str(analysis_storage.data_dir / 'output.plaso'),
        str(collection_storage.data_dir),
    ]
    success = await create_subprocess_and_wait(argv)
    if success:
        analysis_storage.create_archive()
    analysis_storage.remove_data_dir()
    return success


def main():
    """Analyzer entrypoint"""
    analyzer = Analyzer(
        info=AnalyzerInfo(
            name='plaso',
            tags={},
            version='0.1.0',
        ),
        config_cls=PlasoAnalyzerConfig,
        process_impl=_plaso_process_impl,
    )
    analyzer.run()


if __name__ == '__main__':
    main()
