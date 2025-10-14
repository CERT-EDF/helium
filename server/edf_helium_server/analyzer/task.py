"""Analyzer Task"""

from dataclasses import dataclass, field
from datetime import datetime

from edf_helium_core.concept import Analysis, Case, Collection


@dataclass(kw_only=True, order=True)
class AnalyzerTask:
    """Analyzer Task"""

    priority: int
    created: datetime
    case: Case = field(compare=False)
    collection: Collection = field(compare=False)
    analysis: Analysis = field(compare=False)
