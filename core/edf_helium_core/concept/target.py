"""Helium Target"""

from dataclasses import dataclass

from edf_fusion.concept import Concept


@dataclass(kw_only=True)
class Target(Concept):
    """Helium Target"""

    name: str
    rule_uids: set[int]

    @classmethod
    def from_dict(cls, dct):
        return cls(
            name=dct['name'],
            rule_uids=set(dct['rule_uids']),
        )

    def to_dict(self):
        return {
            'name': self.name,
            'rule_uids': list(self.rule_uids),
        }

    def update(self, dct):
        raise NotImplementedError("Target.update shall not be called!")
