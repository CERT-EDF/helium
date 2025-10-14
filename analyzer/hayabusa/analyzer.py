"""Helium Hayabusa Analyzer"""

from dataclasses import dataclass
from pathlib import Path

from edf_fusion.concept import AnalyzerInfo
from edf_fusion.helper.logging import get_logger
from edf_fusion.helper.subprocess import create_subprocess_and_wait
from edf_fusion.server.config import FusionAnalyzerConfig
from edf_helium_server.analyzer import Analyzer, AnalyzerTask
from edf_helium_server.storage import Storage

_HRULE = b"-----------------------------------------------------------------\n"
_LOGGER = get_logger('analyzer.hayabusa', root='helium')


@dataclass(kw_only=True)
class HayabusaAnalyzerConfig(FusionAnalyzerConfig):
    """Hayabusa Analyzer Config"""

    program: Path | None = None
    rules_dir: Path | None = None

    @classmethod
    def from_dict(cls, dct):
        config = super().from_dict(dct)
        config.program = Path(dct['program'])
        config.rules_dir = Path(dct['rules_dir'])
        return config


def _computer_metrics_argv_factory(
    config: HayabusaAnalyzerConfig,
    collection_data_dir: Path,
    analysis_data_dir: Path,
):
    output = analysis_data_dir / 'computer-metrics.csv'
    return [
        str(config.program),
        'computer-metrics',
        '-C',
        '-o',
        str(output),
        '-d',
        str(collection_data_dir),
    ]


def _eid_metrics_argv_factory(
    config: HayabusaAnalyzerConfig,
    collection_data_dir: Path,
    analysis_data_dir: Path,
):
    output = analysis_data_dir / 'eid-metrics.csv'
    return [
        str(config.program),
        'eid-metrics',
        '-C',
        '-O',
        '-U',
        '-o',
        str(output),
        '-d',
        str(collection_data_dir),
    ]


def _log_metrics_argv_factory(
    config: HayabusaAnalyzerConfig,
    collection_data_dir: Path,
    analysis_data_dir: Path,
):
    output = analysis_data_dir / 'log-metrics.csv'
    return [
        str(config.program),
        'log-metrics',
        '-C',
        '-O',
        '-U',
        '-o',
        str(output),
        '-d',
        str(collection_data_dir),
    ]


def _logon_summary_argv_factory(
    config: HayabusaAnalyzerConfig,
    collection_data_dir: Path,
    analysis_data_dir: Path,
):
    output = analysis_data_dir / 'logon-summary.csv'
    return [
        str(config.program),
        'logon-summary',
        '-C',
        '-O',
        '-U',
        '-o',
        str(output),
        '-d',
        str(collection_data_dir),
    ]


def _extract_base64_argv_factory(
    config: HayabusaAnalyzerConfig,
    collection_data_dir: Path,
    analysis_data_dir: Path,
):
    output = analysis_data_dir / 'extract-base64.csv'
    return [
        str(config.program),
        'extract-base64',
        '-C',
        '-O',
        '-U',
        '-o',
        str(output),
        '-d',
        str(collection_data_dir),
    ]


def _csv_timeline_argv_factory(
    config: HayabusaAnalyzerConfig,
    collection_data_dir: Path,
    analysis_data_dir: Path,
):
    summary = analysis_data_dir / 'summary.html'
    timeline = analysis_data_dir / 'timeline.csv'
    argv = [
        str(config.program),
        'csv-timeline',
        '-C',
        '-O',
        '-U',
        '-w',
        '-o',
        str(timeline),
        '-H',
        str(summary),
        '-d',
        str(collection_data_dir),
    ]
    if config.rules_dir:
        argv.extend(['-r', str(config.rules_dir)])
    return argv


_HAYABUSA_ARGV_FACTORIES = [
    _computer_metrics_argv_factory,
    _eid_metrics_argv_factory,
    _log_metrics_argv_factory,
    _logon_summary_argv_factory,
    _extract_base64_argv_factory,
    _csv_timeline_argv_factory,
]


async def _hayabusa_process_impl(
    info: AnalyzerInfo,
    config: HayabusaAnalyzerConfig,
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
    with analysis_storage.log.open('wb') as logf:
        for argv_factory in _HAYABUSA_ARGV_FACTORIES:
            argv = argv_factory(
                config,
                collection_storage.data_dir,
                analysis_storage.data_dir,
            )
            logf.write(_HRULE)
            logf.write(str(argv).encode('utf-8'))
            logf.write(_HRULE)
            success = await create_subprocess_and_wait(
                argv, stdout=logf, stderr=logf
            )
            if not success:
                break
    if success:
        analysis_storage.create_archive()
    analysis_storage.remove_data_dir()
    return success


def main():
    """Analyzer entrypoint"""
    analyzer = Analyzer(
        info=AnalyzerInfo(
            name='hayabusa',
            tags={'windows', 'evtx'},
            version='0.1.0',
        ),
        config_cls=HayabusaAnalyzerConfig,
        process_impl=_hayabusa_process_impl,
    )
    analyzer.run()


if __name__ == '__main__':
    main()
