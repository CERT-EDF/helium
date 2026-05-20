"""Helium Profile"""

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from edf_fusion.concept import Concept
from generaptor.concept import OperatingSystem


@dataclass(kw_only=True)
class Profile(Concept):
    """Helium Profile"""

    guid: UUID = field(default_factory=uuid4)
    name: str
    targets: set[UUID] = field(default_factory=set)
    opsystem: OperatingSystem
    external: bool = False

    @classmethod
    def from_dict(cls, dct):
        return cls(
            guid=UUID(dct['guid']),
            name=dct['name'],
            targets=set(map(UUID, dct.get('targets', []))),
            opsystem=OperatingSystem(dct['opsystem']),
            external=dct['external'],
        )

    def to_dict(self):
        return {
            'guid': str(self.guid),
            'name': self.name,
            'targets': list(map(str, self.targets)),
            'opsystem': self.opsystem.value,
            'external': self.external,
        }

    def update(self, dct):
        # guid cannot be updated
        self.name = dct.get('name', self.name)
        if 'targets' in dct:
            self.targets = set(map(UUID, dct.get('targets', [])))
        self.opsystem = OperatingSystem(dct.get('opsystem', self.opsystem))
        # external cannot be updated
