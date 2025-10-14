"""Helium Rule"""

from dataclasses import dataclass

from edf_fusion.concept import Concept


@dataclass(kw_only=True)
class Rule(Concept):
    """Helium Rule"""

    uid: int
    name: str
    category: str
    glob: str
    accessor: str
    comment: str

    @classmethod
    def from_dict(cls, dct):
        return cls(
            uid=dct['uid'],
            name=dct['name'],
            category=dct['category'],
            glob=dct['glob'],
            accessor=dct['accessor'],
            comment=dct['comment'],
        )

    def to_dict(self):
        return {
            'uid': self.uid,
            'name': self.name,
            'category': self.category,
            'glob': self.glob,
            'accessor': self.accessor,
            'comment': self.comment,
        }

    def update(self, dct):
        raise NotImplementedError("Rule.update shall not be called!")
