"""Helium Plasma Analyzer"""

from dataclasses import dataclass
from pathlib import Path

from edf_fusion.concept import AnalyzerInfo
from edf_fusion.helper.logging import get_logger
from edf_fusion.helper.subprocess import create_subprocess_and_wait
from edf_fusion.server.config import FusionAnalyzerConfig
from edf_helium_server.analyzer import Analyzer, AnalyzerError, AnalyzerTask
from edf_helium_server.storage import Storage
from edf_plasma_core.concept import Tag

_LOGGER = get_logger('analyzer.plasma', root='helium')


@dataclass(kw_only=True)
class PlasmaAnalyzerConfig(FusionAnalyzerConfig):
    """Plasma Analyzer Config"""

    program: Path | None = None
    parallel_surgeons: int = 1
    parallel_dissectors: int = 1

    @classmethod
    def from_dict(cls, dct):
        config = super().from_dict(dct)
        config.program = Path(dct['program'])
        config.parallel_surgeons = max(1, int(dct.get('parallel_surgeons', 1)))
        config.parallel_dissectors = max(
            1, int(dct.get('parallel_dissectors', 1))
        )
        return config


async def _plasma_process_impl(
    info: AnalyzerInfo,
    config: PlasmaAnalyzerConfig,
    storage: Storage,
    a_task: AnalyzerTask,
) -> bool:
    if not a_task.collection.hostname:
        raise AnalyzerError("collection.hostname is empty!")
    if not a_task.collection.tags:
        raise AnalyzerError("collection.tags is empty!")
    collection_storage = storage.collection_storage(
        a_task.case.guid, a_task.collection.guid
    )
    analysis_storage = storage.analysis_storage(
        a_task.case.guid, a_task.collection.guid, a_task.analysis.analyzer
    )
    analysis_storage.data_dir.mkdir(parents=True, exist_ok=True)
    tags = info.tags.intersection(a_task.collection.tags)
    if a_task.collection.opsystem:
        tags.add(a_task.collection.opsystem.value)
    if not tags:
        raise AnalyzerError("plasma cannot process collection without tags!")
    tags = ','.join(sorted(tags))
    argv = [
        str(config.program),
        'dissect',
        '--file-format',
        'csv',
        '--prefix',
        '--hostname',
        a_task.collection.hostname,
        '--filter',
        f'tags:{tags}',
        '--parallel-surgeons',
        str(config.parallel_surgeons),
        '--parallel-dissectors',
        str(config.parallel_dissectors),
        '.',
        str(analysis_storage.data_dir.resolve()),
    ]
    cwd = collection_storage.data_dir.resolve()
    env = {'PLASMA_LOGFILE': str(analysis_storage.log)}
    success = await create_subprocess_and_wait(argv, cwd=cwd, env=env)
    if success:
        analysis_storage.create_archive()
    analysis_storage.remove_data_dir()
    return success


def main():
    """Analyzer entrypoint"""
    analyzer = Analyzer(
        info=AnalyzerInfo(
            name='plasma',
            tags={tag.value for tag in Tag},
            version='0.1.0',
        ),
        config_cls=PlasmaAnalyzerConfig,
        process_impl=_plasma_process_impl,
    )
    analyzer.run()


if __name__ == '__main__':
    main()
