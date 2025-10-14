"""Helium Generaptor Helper"""

from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from secrets import token_urlsafe

from edf_fusion.helper.logging import get_logger
from edf_fusion.helper.zip import create_zip
from edf_helium_core.concept import Collection, Collector, CollectorSecrets
from generaptor.concept import Cache as GCache
from generaptor.concept import Collection as GCollection
from generaptor.concept import Collector as GCollector
from generaptor.concept import CollectorConfig as GCollectorConfig
from generaptor.concept import Config as GConfig
from generaptor.concept import (
    Outcome,
    get_profile_mapping,
    get_ruleset_from_targets,
)
from generaptor.helper.crypto import (
    certificate_from_pem_bytes,
    certificate_to_pem_bytes,
    fingerprint,
    generate_private_key_and_certificate,
    private_key_from_pem_bytes,
    private_key_to_pem_bytes,
)

_LOGGER = get_logger('server.helper.generaptor', root='helium')


@dataclass(kw_only=True)
class Generaptor:
    """Generaptor Helper"""

    cache: GCache
    config: GConfig

    def generate_collector_secrets(self) -> CollectorSecrets:
        """Generate collector secrets"""
        secret = token_urlsafe(32).encode('utf-8')
        private_key, certificate = generate_private_key_and_certificate()
        return CollectorSecrets(
            secret=secret,
            key_pem=private_key_to_pem_bytes(private_key, secret),
            crt_pem=certificate_to_pem_bytes(certificate),
        )

    def generate_collector(
        self,
        collector: Collector,
        collector_secrets: CollectorSecrets,
        output_dir: Path,
    ) -> str | None:
        """Generate collector"""
        _LOGGER.info("generating collector %s", collector.guid)
        # load profile
        profile_mapping = get_profile_mapping(
            self.cache, self.config, collector.distrib.opsystem
        )
        profile = profile_mapping.get(collector.profile)
        if not profile:
            _LOGGER.error("unknown profile: %s", collector.profile)
            return None
        # prepare collector config
        certificate = certificate_from_pem_bytes(collector_secrets.crt_pem)
        collector_config = GCollectorConfig(
            device=collector.device,
            rule_set=get_ruleset_from_targets(
                self.cache,
                self.config,
                profile.targets,
                collector.distrib.opsystem,
            ),
            certificate=certificate,
            distribution=collector.distrib,
            memdump=collector.memdump,
            dont_be_lazy=collector.dont_be_lazy,
            vss_analysis_age=collector.vss_analysis_age,
            use_auto_accessor=collector.use_auto_accessor,
        )
        gcollector = GCollector(collector_config)
        # generate collector
        info = gcollector.generate(self.cache, self.config, output_dir)
        if not info:
            _LOGGER.error("collector generation failed, cleaning up")
            for item in output_dir.iterdir():
                item.unlink()
            return None
        # compress collector
        try:
            collector = next(output_dir.glob('collector-*-*-*'))
            create_zip(
                output_dir / f'{collector.name}.zip',
                output_dir,
                files=[collector],
            )
            collector.unlink()
        except StopIteration:
            _LOGGER.error("collector not found")
            return None
        return fingerprint(certificate)

    def copy_zip_metadata(self, collection: Collection, collection_path: Path):
        """Set collection properties from metadata.json if available"""
        gcollection = GCollection(collection_path)
        try:
            collection.device = gcollection.device
            collection.version = gcollection.version
            collection.opsystem = gcollection.opsystem
            collection.hostname = gcollection.hostname
            collection.collected = gcollection.created
            collection.fingerprint = gcollection.fingerprint
        except KeyError:
            _LOGGER.info(
                "collection %s does not have a metadata.json", collection.guid
            )
        except JSONDecodeError:
            _LOGGER.warning(
                "collection %s has a malformed metadata.json", collection.guid
            )

    def extract_collection(
        self,
        collector_secrets: CollectorSecrets,
        collection_path: Path,
        output_dir: Path,
    ) -> Outcome:
        """Extract collection"""
        gcollection = GCollection(collection_path)
        private_key = private_key_from_pem_bytes(
            collector_secrets.key_pem, collector_secrets.secret
        )
        secret = gcollection.secret(private_key)
        if not secret:
            return Outcome.FAILURE
        return gcollection.extract_to(output_dir, secret)
