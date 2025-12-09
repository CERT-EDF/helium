"""Helium Extractor Analyzer"""

from dataclasses import dataclass
from shutil import Error, copytree

from edf_fusion.concept import AnalyzerInfo
from edf_fusion.helper.logging import get_logger
from edf_fusion.server.config import FusionAnalyzerConfig
from edf_helium_server.analyzer import Analyzer, AnalyzerTask
from edf_helium_server.storage import Storage

_LOGGER = get_logger('analyzer.extractor', root='helium')


async def _extractor_process_impl(
    info: AnalyzerInfo,
    config: FusionAnalyzerConfig,
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
    src = collection_storage.data_dir.resolve()
    dst = analysis_storage.data_dir.resolve()
    try:
        copytree(src, dst)
    except Error:
        analysis_storage.remove_data_dir()
        return False
    analysis_storage.create_archive()
    analysis_storage.remove_data_dir()
    return True


def main():
    """Analyzer entrypoint"""
    analyzer = Analyzer(
        info=AnalyzerInfo(
            name='extractor',
            tags=set(),
            version='0.1.0',
        ),
        config_cls=FusionAnalyzerConfig,
        process_impl=_extractor_process_impl,
    )
    analyzer.run()


if __name__ == '__main__':
    main()
