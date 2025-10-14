"""Helium Collector"""

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from edf_fusion.concept import Concept
from edf_fusion.helper.datetime import datetime, from_iso, to_iso, utcnow
from generaptor.concept import Architecture, Distribution, OperatingSystem


@dataclass(kw_only=True)
class Collector(Concept):
    """Helium Collector"""

    guid: UUID = field(default_factory=uuid4)
    created: datetime = field(default_factory=utcnow)
    profile: str | None
    distrib: Distribution
    fingerprint: str | None = None
    device: str = ''
    description: str = ''
    memdump: bool = False
    dont_be_lazy: bool | None = None
    vss_analysis_age: int | None = None
    use_auto_accessor: bool | None = None

    @classmethod
    def from_dict(cls, dct):
        return cls(
            guid=UUID(dct['guid']),
            created=from_iso(dct['created']),
            profile=dct['profile'],
            distrib=Distribution(
                arch=Architecture(dct['arch']),
                opsystem=OperatingSystem(dct['opsystem']),
            ),
            fingerprint=dct['fingerprint'],
            device=dct['device'],
            description=dct['description'],
            memdump=dct['memdump'],
            dont_be_lazy=dct['dont_be_lazy'],
            vss_analysis_age=dct['vss_analysis_age'],
            use_auto_accessor=dct['use_auto_accessor'],
        )

    def to_dict(self):
        return {
            'guid': str(self.guid),
            'created': to_iso(self.created),
            'profile': self.profile,
            'arch': self.distrib.arch.value,
            'opsystem': self.distrib.opsystem.value,
            'fingerprint': self.fingerprint,
            'device': self.device,
            'description': self.description,
            'memdump': self.memdump,
            'dont_be_lazy': self.dont_be_lazy,
            'vss_analysis_age': self.vss_analysis_age,
            'use_auto_accessor': self.use_auto_accessor,
        }

    def update(self, dct):
        raise NotImplementedError("Collector.update shall not be used")


@dataclass(kw_only=True)
class CollectorSecrets(Concept):
    """Collector secrets"""

    secret: bytes
    key_pem: bytes
    crt_pem: bytes | None = None

    @classmethod
    def from_dict(cls, dct):
        crt_pem = dct.get('crt_pem')
        return cls(
            secret=dct['secret'].encode('utf-8'),
            key_pem=dct['key_pem'].encode('utf-8'),
            crt_pem=crt_pem.encode('utf-8') if crt_pem else None,
        )

    def to_dict(self):
        return {
            'secret': self.secret.decode('utf-8'),
            'key_pem': self.key_pem.decode('utf-8'),
            'crt_pem': self.crt_pem.decode('utf-8') if self.crt_pem else None,
        }

    def update(self, dct):
        raise NotImplementedError("CollectorSecrets.update shall not be used")
