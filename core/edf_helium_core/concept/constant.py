"""Helium Constant"""

from dataclasses import dataclass, field

from edf_fusion.concept import Constant as FusionConstant
from edf_fusion.concept import Priority, Status
from generaptor.concept import Architecture, OperatingSystem


def _enums() -> dict[str, list[str]]:
    return {
        'status': [status.value for status in Status],
        'opsystem': [opsystem.value for opsystem in OperatingSystem],
        'priority': [priority.value for priority in Priority],
        'architecture': [arch.value for arch in Architecture],
    }


def _extra_fields() -> dict[OperatingSystem, list[str]]:
    return {
        OperatingSystem.WINDOWS: [
            'memdump',
            'dont_be_lazy',
            'vss_analysis_age',
            'use_auto_accessor',
        ]
    }


@dataclass(kw_only=True)
class Constant(FusionConstant):
    """Helium Constant"""

    enums: dict[str, list[str]] = field(default_factory=dict)
    quota: int | None = None
    extra_fields: dict[OperatingSystem, list[str]] = field(
        default_factory=dict
    )

    @classmethod
    def from_dict(cls, dct):
        constant = super().from_dict(dct)
        constant.enums = _enums()
        constant.quota = dct.get('quota')
        constant.extra_fields = _extra_fields()
        return constant

    def to_dict(self):
        dct = super().to_dict()
        dct.update(
            {
                'enums': self.enums,
                'quota': self.quota,
                'extra_fields': {
                    opsystem.value: extra_fields
                    for opsystem, extra_fields in self.extra_fields.items()
                },
            }
        )
        return dct
