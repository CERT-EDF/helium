"""Helium PTR Helper"""

from dataclasses import dataclass
from hashlib import file_digest
from pathlib import Path

from edf_fusion.helper.logging import get_logger
from edf_fusion.helper.redis import create_redis_lock
from edf_fusion.helper.serializing import Dumpable, Loadable
from generaptor.concept import OperatingSystem
from generaptor.helper.json import dump_jsonl, load_jsonl

from ..ptr_storage import PTRStorage
from ..storage import Storage

_LOGGER = get_logger('server.helper.ptr', root='helium')
_PROFILES_JSONL = 'profiles.jsonl'
_TARGETS_JSONL = 'targets.jsonl'
_RULES_JSONL = 'rules.jsonl'


async def _load_external_profiles(
    ptr_storage: PTRStorage, opsystem: OperatingSystem, directory: Path
):
    filepath = directory / opsystem.value / _PROFILES_JSONL
    if not filepath.is_file():
        _LOGGER.warning('loading error: file %s does not exist', filepath)
        return
    for dct in load_jsonl(filepath):
        dct['external'] = True
        await ptr_storage.create_profile(opsystem, dct)


async def _load_external_targets(
    ptr_storage: PTRStorage, opsystem: OperatingSystem, directory: Path
):
    filepath = directory / opsystem.value / _TARGETS_JSONL
    if not filepath.is_file():
        _LOGGER.warning('loading error: file %s does not exist', filepath)
        return
    for dct in load_jsonl(filepath):
        dct['external'] = True
        await ptr_storage.create_target(opsystem, dct)


async def _load_external_rules(
    ptr_storage: PTRStorage, opsystem: OperatingSystem, directory: Path
):
    filepath = directory / opsystem.value / _RULES_JSONL
    if not filepath.is_file():
        _LOGGER.warning('loading error: file %s does not exist', filepath)
        return
    for dct in load_jsonl(filepath):
        dct['external'] = True
        await ptr_storage.create_rule(opsystem, dct)


async def _dump_internal_profiles(
    ptr_storage: PTRStorage, opsystem: OperatingSystem, directory: Path
):
    filepath = directory / opsystem.value / _PROFILES_JSONL
    profiles = [
        profile.to_dict()
        async for profile in ptr_storage.enumerate_profiles(opsystem)
        if not profile.external
    ]
    dump_jsonl(filepath, profiles)


async def _dump_internal_targets(
    ptr_storage: PTRStorage, opsystem: OperatingSystem, directory: Path
):
    filepath = directory / opsystem.value / _TARGETS_JSONL
    targets = [
        target.to_dict()
        async for target in ptr_storage.enumerate_targets(opsystem)
        if not target.external
    ]
    dump_jsonl(filepath, targets)


async def _dump_internal_rules(
    ptr_storage: PTRStorage, opsystem: OperatingSystem, directory: Path
):
    filepath = directory / opsystem.value / _RULES_JSONL
    rules = [
        rule.to_dict()
        async for rule in ptr_storage.enumerate_rules(opsystem)
        if not rule.external
    ]
    dump_jsonl(filepath, rules)


@dataclass(kw_only=True)
class PTRState(Dumpable, Loadable):
    """PTR State"""

    rules_digest: str
    targets_digest: str
    profiles_digest: str

    @classmethod
    def from_dict(cls, dct):
        return cls(
            rules_digest=dct['rules_digest'],
            targets_digest=dct['targets_digest'],
            profiles_digest=dct['profiles_digest'],
        )

    @classmethod
    def from_directory(cls, directory: Path):
        """Create instance from"""
        dct = {}
        with (directory / _PROFILES_JSONL).open('rb') as fobj:
            dct['profiles_digest'] = file_digest(fobj, 'sha256').hexdigest()
        with (directory / _TARGETS_JSONL).open('rb') as fobj:
            dct['targets_digest'] = file_digest(fobj, 'sha256').hexdigest()
        with (directory / _RULES_JSONL).open('rb') as fobj:
            dct['rules_digest'] = file_digest(fobj, 'sha256').hexdigest()
        return cls.from_dict(dct)

    def to_dict(self):
        return {
            'rules_digest': self.rules_digest,
            'targets_digest': self.targets_digest,
            'profiles_digest': self.profiles_digest,
        }


def _need_external_ptr_update(
    storage: Storage, opsystem: OperatingSystem
) -> bool:
    """Determine if external data changed"""
    ptr_state_path = storage.cache_dir / f'ptr_state_{opsystem.value}.json'
    if not ptr_state_path.is_file():
        _LOGGER.info("ptr state file is missing")
        return True
    ptr_state_prev = PTRState.from_filepath(ptr_state_path)
    ptr_state_next = PTRState.from_directory(
        storage.generaptor.cache.config.directory / opsystem.value
    )
    return ptr_state_next != ptr_state_prev


def _update_external_ptr_state(storage: Storage, opsystem: OperatingSystem):
    """Update ptr state"""
    ptr_state_path = storage.cache_dir / f'ptr_state_{opsystem.value}.json'
    ptr_state_next = PTRState.from_directory(
        storage.generaptor.cache.config.directory / opsystem.value
    )
    ptr_state_next.to_filepath(ptr_state_path)


async def load_external_ptr(
    storage: Storage, ptr_storage: PTRStorage, opsystem: OperatingSystem
):
    """Load external PTR items"""
    lock = create_redis_lock(storage.redis, 'load-external-ptr')
    async with lock:
        if not _need_external_ptr_update(storage, opsystem):
            _LOGGER.info("skipped loading external ptr data")
            return
        directory = storage.generaptor.cache.config.directory
        await _load_external_rules(ptr_storage, opsystem, directory)
        await _load_external_targets(ptr_storage, opsystem, directory)
        await _load_external_profiles(ptr_storage, opsystem, directory)
        _update_external_ptr_state(storage, opsystem)


async def dump_internal_ptr(
    storage: Storage, ptr_storage: PTRStorage, opsystem: OperatingSystem
):
    """Dump internal PTR items"""
    lock = create_redis_lock(storage.redis, 'dump-internal-ptr')
    directory = storage.generaptor.config.directory
    (directory / opsystem.value).mkdir(parents=True, exist_ok=True)
    async with lock:
        if not ptr_storage.changed.is_set():
            _LOGGER.info("skipped dumping internal ptr data")
            return
        await _dump_internal_rules(ptr_storage, opsystem, directory)
        await _dump_internal_targets(ptr_storage, opsystem, directory)
        await _dump_internal_profiles(ptr_storage, opsystem, directory)
        ptr_storage.changed.clear()
