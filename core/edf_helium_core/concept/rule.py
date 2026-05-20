"""Helium Rule"""

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from edf_fusion.concept import Concept
from generaptor.concept import OperatingSystem

DEFAULT_ACCESSOR = {
    OperatingSystem.WINDOWS: 'lazy_ntfs',
    OperatingSystem.DARWIN: 'file',
    OperatingSystem.LINUX: 'file',
}


@dataclass(kw_only=True)
class Rule(Concept):
    """Helium Rule"""

    guid: UUID = field(default_factory=uuid4)
    name: str
    category: str
    glob: str
    accessor: str
    comment: str
    opsystem: OperatingSystem
    external: bool = False

    @classmethod
    def from_dict(cls, dct):
        opsystem = OperatingSystem(dct['opsystem'])
        return cls(
            guid=UUID(dct['guid']),
            name=dct.get('name', ''),
            category=dct.get('category', ''),
            glob=dct['glob'],
            accessor=dct.get('accessor', DEFAULT_ACCESSOR[opsystem]),
            comment=dct.get('comment', ''),
            opsystem=opsystem,
            external=dct['external'],
        )

    def to_dict(self):
        return {
            'guid': str(self.guid),
            'name': self.name,
            'category': self.category,
            'glob': self.glob,
            'accessor': self.accessor,
            'comment': self.comment,
            'opsystem': self.opsystem.value,
            'external': self.external,
        }

    def update(self, dct):
        # guid cannot be updated
        self.name = dct.get('name', self.name)
        self.category = dct.get('category', self.category)
        self.glob = dct.get('glob', self.glob)
        self.accessor = dct.get('accessor', self.accessor)
        self.comment = dct.get('comment', self.comment)
        self.opsystem = OperatingSystem(dct.get('opsystem', self.opsystem))
        # external cannot be updated
