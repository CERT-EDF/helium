"""Helium Disk Usage"""

from dataclasses import dataclass
from uuid import UUID

from edf_fusion.concept import Concept
from edf_fusion.helper.datetime import datetime, from_iso, to_iso, utcnow


@dataclass(kw_only=True)
class CaseDiskUsage(Concept):
    """Helium Case Disk Usage"""

    collectors: int
    collections: int
    analyses: int

    @classmethod
    def from_dict(cls, dct):
        return cls(
            collectors=dct['collectors'],
            collections=dct['collections'],
            analyses=dct['analyses'],
        )

    def to_dict(self):
        return {
            'collectors': self.collectors,
            'collections': self.collections,
            'analyses': self.analyses,
        }

    def update(self, dct):
        raise NotImplementedError("CaseDiskUsage.update shall not be called!")


@dataclass(kw_only=True)
class DiskUsage(Concept):
    """Helium Disk Usage"""

    cases: dict[UUID, CaseDiskUsage]
    updated: datetime

    @classmethod
    def from_dict(cls, dct):
        cases = {}
        for item in dct['cases']:
            case_guid = item.pop('guid')
            case_data_usage = CaseDiskUsage.from_dict(item)
            cases[case_guid] = case_data_usage
        return cls(
            cases=cases,
            updated=from_iso(dct['updated']),
        )

    def to_dict(self):
        cases = []
        for case_guid, case_data_usage in self.cases.items():
            item = {'guid': str(case_guid)}
            item.update(case_data_usage.to_dict())
            cases.append(item)
        return {
            'cases': cases,
            'updated': to_iso(self.updated),
        }

    def update(self, dct):
        cases = {}
        for item in dct['cases']:
            case_guid = item.pop('guid')
            case_data_usage = CaseDiskUsage.from_dict(item)
            cases[case_guid] = case_data_usage
        self.cases = cases
        self.updated = utcnow()
