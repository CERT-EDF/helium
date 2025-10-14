"""Helium Collection"""

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from edf_fusion.concept import Concept
from edf_fusion.helper.datetime import (
    datetime,
    from_iso,
    from_iso_or_none,
    to_iso,
    to_iso_or_none,
    utcnow,
)
from generaptor.concept import OperatingSystem


@dataclass(kw_only=True)
class Collection(Concept):
    """Helium Collection"""

    guid: UUID = field(default_factory=uuid4)
    created: datetime = field(default_factory=utcnow)
    tags: set[str] = field(default_factory=set)
    description: str = ''
    device: str | None = None
    version: str | None = None
    opsystem: OperatingSystem | None = None
    hostname: str | None = None
    collected: datetime | None = None
    fingerprint: str | None = None

    @classmethod
    def from_dict(cls, dct):
        opsystem = dct['opsystem']
        if opsystem:
            opsystem = OperatingSystem(dct['opsystem'])
        return cls(
            guid=UUID(dct['guid']),
            created=from_iso(dct['created']),
            tags=set(dct['tags']),
            device=dct['device'],
            version=dct['version'],
            opsystem=opsystem,
            hostname=dct['hostname'],
            collected=from_iso_or_none(dct['collected']),
            fingerprint=dct['fingerprint'],
            description=dct['description'],
        )

    def to_dict(self):
        opsystem = self.opsystem.value if self.opsystem else None
        return {
            'guid': str(self.guid),
            'created': to_iso(self.created),
            'tags': list(sorted(self.tags)),
            'device': self.device,
            'version': self.version,
            'opsystem': opsystem,
            'description': self.description,
            'hostname': self.hostname,
            'collected': to_iso_or_none(self.collected),
            'fingerprint': self.fingerprint,
        }

    def update(self, dct):
        # guid cannot be updated
        # created cannot be updated
        self.tags = set(dct.get('tags', self.tags))
        self.device = dct.get('device', self.device)
        # version cannot be updated
        opsystem = dct.get('opsystem')
        if opsystem:
            self.opsystem = OperatingSystem(opsystem)
        self.hostname = dct.get('hostname', self.hostname)
        self.collected = (
            from_iso_or_none(dct.get('collected')) or self.collected
        )
        self.description = dct.get('description', self.description)
        # fingerprint cannot be updated
