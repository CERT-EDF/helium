"""Helium Profile"""

from dataclasses import dataclass

from edf_fusion.concept import Concept


@dataclass(kw_only=True)
class Profile(Concept):
    """Helium Profile"""

    name: str
    targets: set[str]

    @classmethod
    def from_dict(cls, dct):
        return cls(
            name=dct['name'],
            targets=set(dct['targets']),
        )

    def to_dict(self):
        return {
            'name': self.name,
            'targets': list(self.targets),
        }

    def update(self, dct):
        raise NotImplementedError("Profile.update shall not be called!")
