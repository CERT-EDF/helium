"""Helium Analysis"""

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from edf_fusion.concept import Concept, Priority, Status
from edf_fusion.helper.datetime import (
    datetime,
    from_iso,
    from_iso_or_none,
    to_iso,
    to_iso_or_none,
    utcnow,
)

_STATUS_TRANSITIONS: dict[Status, set[Status]] = {
    Status.PENDING: {Status.QUEUED},
    Status.QUEUED: {Status.EXTRACTING, Status.PENDING},
    Status.EXTRACTING: {Status.PROCESSING, Status.FAILURE, Status.PENDING},
    Status.PROCESSING: {Status.SUCCESS, Status.FAILURE, Status.PENDING},
    Status.SUCCESS: {Status.PENDING},
    Status.FAILURE: {Status.PENDING},
}
PRIORITY_INT: dict[Priority, int] = {
    Priority.LOW: 2,
    Priority.MEDIUM: 1,
    Priority.HIGH: 0,
}


@dataclass(kw_only=True)
class Analysis(Concept):
    """Helium Analysis"""

    guid: UUID = field(default_factory=uuid4)
    created: datetime = field(default_factory=utcnow)
    updated: datetime | None = None
    status: Status = Status.PENDING
    analyzer: str
    priority: Priority = Priority.MEDIUM

    @property
    def completed(self) -> bool:
        """Determine if analysis was performed"""
        return self.status in (Status.SUCCESS, Status.FAILURE)

    @classmethod
    def from_dict(cls, dct):
        return cls(
            guid=UUID(dct['guid']),
            created=from_iso(dct['created']),
            updated=from_iso_or_none(dct['updated']),
            status=Status(dct['status']),
            analyzer=dct['analyzer'],
            priority=Priority(dct['priority']),
        )

    def to_dict(self):
        return {
            'guid': str(self.guid),
            'created': to_iso(self.created),
            'updated': to_iso_or_none(self.updated),
            'status': self.status.value,
            'analyzer': self.analyzer,
            'priority': self.priority.value,
        }

    def update(self, dct):
        # guid cannot be updated
        # created cannot be updated
        self.updated = utcnow()
        status = dct.get('status')
        if status:
            status = Status(status)
            if status not in _STATUS_TRANSITIONS[self.status]:
                raise ValueError(
                    f"invalid transition: {self.status} -> {status}"
                )
            self.status = status
        # analyzer cannot be updated
        self.priority = Priority(dct.get('priority', self.priority))
