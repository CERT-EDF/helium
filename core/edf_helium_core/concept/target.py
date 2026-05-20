"""Helium Target"""

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from edf_fusion.concept import Concept
from generaptor.concept import OperatingSystem


@dataclass(kw_only=True)
class Target(Concept):
    """Helium Target"""

    guid: UUID = field(default_factory=uuid4)
    name: str
    rules: set[UUID] = field(default_factory=set)
    opsystem: OperatingSystem
    external: bool = False

    @classmethod
    def from_dict(cls, dct):
        return cls(
            guid=UUID(dct['guid']),
            name=dct['name'],
            rules=set(map(UUID, dct.get('rules', []))),
            opsystem=OperatingSystem(dct['opsystem']),
            external=dct['external'],
        )

    def to_dict(self):
        return {
            'guid': str(self.guid),
            'name': self.name,
            'rules': list(map(str, self.rules)),
            'opsystem': self.opsystem.value,
            'external': self.external,
        }

    def update(self, dct):
        # guid cannot be updated
        self.name = dct.get('name', self.name)
        if 'rules' in dct:
            self.rules = set(map(UUID, dct.get('rules', [])))
        self.opsystem = OperatingSystem(dct.get('opsystem', self.opsystem))
        # external cannot be updated
