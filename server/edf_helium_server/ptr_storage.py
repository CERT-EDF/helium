'''Profile Target Rule Storage (SQLite-backed)'''

from asyncio import Event
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from functools import cached_property
from uuid import UUID, uuid4

from aiohttp.web import Application, Request
from aiosqlite import Row
from edf_fusion.helper.logging import get_logger
from edf_fusion.helper.serializing import load_json
from edf_fusion.helper.sqlite import SQLiteDatabase, parameters_from_concept
from edf_fusion.server.storage import FusionStorage
from edf_helium_core.concept import DEFAULT_ACCESSOR, Profile, Rule, Target
from generaptor.concept import OperatingSystem

from .config import HeliumStorageConfig

_LOGGER = get_logger('server.ptr_storage', root='helium')
_PTR_STORAGE = 'helium_ptr_storage'
_MODEL_VERSION = 1


_CREATE_TABLE_PROFILE = f'''
CREATE TABLE IF NOT EXISTS profile_{_MODEL_VERSION} (
    guid TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    targets TEXT NOT NULL,
    opsystem TEXT NOT NULL,
    external INTEGER NOT NULL DEFAULT 0
)
'''
_CREATE_TABLE_TARGET = f'''
CREATE TABLE IF NOT EXISTS target_{_MODEL_VERSION} (
    guid TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    rules TEXT NOT NULL,
    opsystem TEXT NOT NULL,
    external INTEGER NOT NULL DEFAULT 0
)
'''
_CREATE_TABLE_RULE = f'''
CREATE TABLE IF NOT EXISTS rule_{_MODEL_VERSION} (
    guid TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    glob TEXT NOT NULL,
    accessor TEXT NOT NULL,
    comment TEXT NOT NULL,
    opsystem TEXT NOT NULL,
    external INTEGER NOT NULL DEFAULT 0
)
'''
_UPSERT_PROFILE = f'''
INSERT OR REPLACE INTO profile_{_MODEL_VERSION}
VALUES (:guid, :name, :targets, :opsystem, :external)
'''
_SELECT_PROFILE = f'''
SELECT guid, name, targets, opsystem, external
FROM profile_{_MODEL_VERSION}
WHERE opsystem = :opsystem AND guid = :guid
'''
_SELECT_TARGET_PROFILES = f'''
SELECT guid, name, targets, opsystem, external
FROM profile_{_MODEL_VERSION}
WHERE opsystem = :opsystem AND targets LIKE :pattern
'''
_SELECT_PROFILES = f'''
SELECT guid, name, targets, opsystem, external
FROM profile_{_MODEL_VERSION}
WHERE opsystem = :opsystem
'''
_DELETE_PROFILE = f'''
DELETE FROM profile_{_MODEL_VERSION}
WHERE opsystem = :opsystem AND guid = :guid AND external = 0
'''
_DELETE_EXTERNAL_PROFILES = f'''
DELETE FROM profile_{_MODEL_VERSION}
WHERE opsystem = :opsystem AND external = 1
'''
_UPSERT_TARGET = f'''
INSERT OR REPLACE INTO target_{_MODEL_VERSION}
VALUES (:guid, :name, :rules, :opsystem, :external)
'''
_SELECT_TARGET = f'''
SELECT guid, name, rules, opsystem, external
FROM target_{_MODEL_VERSION}
WHERE opsystem = :opsystem AND guid = :guid
'''
_SELECT_TARGETS = f'''
SELECT guid, name, rules, opsystem, external
FROM target_{_MODEL_VERSION}
WHERE opsystem = :opsystem
'''
_DELETE_TARGET = f'''
DELETE FROM target_{_MODEL_VERSION}
WHERE opsystem = :opsystem AND guid = :guid AND external = 0
'''
_DELETE_EXTERNAL_TARGETS = f'''
DELETE FROM target_{_MODEL_VERSION}
WHERE opsystem = :opsystem AND external = 1
'''
_UPSERT_RULE = f'''
INSERT OR REPLACE INTO rule_{_MODEL_VERSION}
VALUES (:guid, :name, :category, :glob, :accessor, :comment, :opsystem, :external)
'''
_SELECT_RULE = f'''
SELECT guid, name, category, glob, accessor, comment, opsystem, external
FROM rule_{_MODEL_VERSION}
WHERE opsystem = :opsystem AND guid = :guid
'''
_SELECT_RULES = f'''
SELECT guid, name, category, glob, accessor, comment, opsystem, external
FROM rule_{_MODEL_VERSION}
WHERE opsystem = :opsystem
'''
_DELETE_RULE = f'''
DELETE FROM rule_{_MODEL_VERSION}
WHERE opsystem = :opsystem AND guid = :guid AND external = 0
'''
_DELETE_EXTERNAL_RULES = f'''
DELETE FROM rule_{_MODEL_VERSION}
WHERE opsystem = :opsystem AND external = 1
'''


async def _prepare_db(database: SQLiteDatabase):
    _LOGGER.info("initialize database...")
    async with database.connection.cursor() as cursor:
        for statement in (
            _CREATE_TABLE_RULE,
            _CREATE_TABLE_TARGET,
            _CREATE_TABLE_PROFILE,
        ):
            await cursor.execute(statement)
    _LOGGER.info("database initialized.")


def _profile_from_row(row: Row) -> Profile:
    return Profile(
        guid=UUID(row['guid']),
        name=row['name'],
        targets=set(load_json(row['targets'])),
        opsystem=OperatingSystem(row['opsystem']),
        external=bool(row['external']),
    )


def _target_from_row(row: Row) -> Target:
    return Target(
        guid=UUID(row['guid']),
        name=row['name'],
        rules=set(load_json(row['rules'])),
        opsystem=OperatingSystem(row['opsystem']),
        external=bool(row['external']),
    )


def _rule_from_row(row: Row) -> Rule:
    return Rule(
        guid=UUID(row['guid']),
        name=row['name'],
        category=row['category'],
        glob=row['glob'],
        accessor=row['accessor'],
        comment=row['comment'],
        opsystem=OperatingSystem(row['opsystem']),
        external=bool(row['external']),
    )


@dataclass(kw_only=True)
class PTRStorage(FusionStorage):
    '''SQLite-backed storage for Profile and Target'''

    config: HeliumStorageConfig
    changed: Event = field(default_factory=Event)

    @cached_property
    def database(self) -> SQLiteDatabase:
        '''Underlying SQLite database'''
        filepath = self.config.directory / 'ptr.db'
        return SQLiteDatabase(filepath=filepath, prepare_db=_prepare_db)

    def setup(self, webapp: Application):
        '''Register PTRStorage in the web application'''
        _LOGGER.info("install ptr storage...")
        webapp[_PTR_STORAGE] = self
        webapp.cleanup_ctx.append(self.database.context)
        _LOGGER.info("ptr storage installed.")

    async def create_profile(
        self, opsystem: OperatingSystem, dct
    ) -> Profile | None:
        '''Create a profile'''
        profile = Profile(
            guid=UUID(dct.get('guid', str(uuid4()))),
            name=dct['name'],
            targets=set(map(UUID, dct.get('targets', []))),
            opsystem=opsystem,
            external=dct.get('external', False),
        )
        parameters = parameters_from_concept(profile)
        await self.database.execute(_UPSERT_PROFILE, parameters)
        self.changed.set()
        return profile

    async def retrieve_profile(
        self, opsystem: OperatingSystem, guid: UUID
    ) -> Profile | None:
        '''Retrieve a profile'''
        row = await self.database.fetchone(
            _SELECT_PROFILE, {'opsystem': opsystem.value, 'guid': str(guid)}
        )
        if not row:
            return None
        return _profile_from_row(row)

    async def update_profile(
        self, opsystem: OperatingSystem, guid: UUID, dct
    ) -> Profile | None:
        '''Update a profile'''
        profile = await self.retrieve_profile(opsystem, guid)
        if not profile:
            return None
        if profile.external:
            return None
        profile.update(dct)
        parameters = parameters_from_concept(profile)
        await self.database.execute(_UPSERT_PROFILE, parameters)
        self.changed.set()
        return profile

    async def delete_profile(
        self, opsystem: OperatingSystem, guid: UUID
    ) -> bool:
        '''Delete a profile'''
        count = await self.database.execute(
            _DELETE_PROFILE, {'opsystem': opsystem.value, 'guid': str(guid)}
        )
        self.changed.set()
        return count > 0

    async def enumerate_profiles(
        self, opsystem: OperatingSystem
    ) -> AsyncIterator[Profile]:
        '''Enumerate profiles'''
        async for row in self.database.fetchmany(
            _SELECT_PROFILES, {'opsystem': opsystem.value}
        ):
            yield _profile_from_row(row)

    async def create_target(
        self, opsystem: OperatingSystem, dct
    ) -> Target | None:
        '''Create a target'''
        target = Target(
            guid=UUID(dct.get('guid', str(uuid4()))),
            name=dct['name'],
            rules=set(map(UUID, dct.get('rules', []))),
            opsystem=opsystem,
            external=dct.get('external', False),
        )
        parameters = parameters_from_concept(target)
        await self.database.execute(_UPSERT_TARGET, parameters)
        self.changed.set()
        return target

    async def retrieve_target(
        self, opsystem: OperatingSystem, guid: UUID
    ) -> Target | None:
        '''Retrieve a target'''
        row = await self.database.fetchone(
            _SELECT_TARGET, {'opsystem': opsystem.value, 'guid': str(guid)}
        )
        if not row:
            return None
        return _target_from_row(row)

    async def update_target(
        self, opsystem: OperatingSystem, guid: UUID, dct
    ) -> Target | None:
        '''Update a target'''
        target = await self.retrieve_target(opsystem, guid)
        if not target:
            return None
        if target.external:
            return None
        target.update(dct)
        parameters = parameters_from_concept(target)
        await self.database.execute(_UPSERT_TARGET, parameters)
        self.changed.set()
        return target

    async def delete_target(
        self, opsystem: OperatingSystem, guid: UUID
    ) -> bool:
        '''Delete a target'''
        count = await self.database.execute(
            _DELETE_TARGET, {'opsystem': opsystem.value, 'guid': str(guid)}
        )
        self.changed.set()
        return count > 0

    async def enumerate_targets(
        self, opsystem: OperatingSystem
    ) -> AsyncIterator[Target]:
        '''Enumerate targets'''
        async for row in self.database.fetchmany(
            _SELECT_TARGETS, {'opsystem': opsystem.value}
        ):
            yield _target_from_row(row)

    async def create_rule(self, opsystem: OperatingSystem, dct) -> Rule | None:
        '''Create a rule'''
        rule = Rule(
            guid=UUID(dct.get('guid', str(uuid4()))),
            name=dct.get('name', ''),
            category=dct.get('category', ''),
            glob=dct['glob'],
            accessor=dct.get('accessor', DEFAULT_ACCESSOR[opsystem]),
            comment=dct.get('comment', ''),
            opsystem=opsystem,
            external=dct.get('external', False),
        )
        parameters = parameters_from_concept(rule)
        await self.database.execute(_UPSERT_RULE, parameters)
        self.changed.set()
        return rule

    async def retrieve_rule(
        self, opsystem: OperatingSystem, guid: UUID
    ) -> Rule | None:
        '''Retrieve a rule'''
        row = await self.database.fetchone(
            _SELECT_RULE, {'opsystem': opsystem.value, 'guid': str(guid)}
        )
        if not row:
            return None
        return _rule_from_row(row)

    async def update_rule(
        self, opsystem: OperatingSystem, guid: UUID, dct
    ) -> Rule | None:
        '''Update a rule'''
        rule = await self.retrieve_rule(opsystem, guid)
        if not rule:
            return None
        if rule.external:
            return None
        rule.update(dct)
        parameters = parameters_from_concept(rule)
        await self.database.execute(_UPSERT_RULE, parameters)
        self.changed.set()
        return rule

    async def delete_rule(self, opsystem: OperatingSystem, guid: UUID) -> bool:
        '''Delete a rule'''
        count = await self.database.execute(
            _DELETE_RULE, {'opsystem': opsystem.value, 'guid': str(guid)}
        )
        self.changed.set()
        return count > 0

    async def enumerate_rules(
        self, opsystem: OperatingSystem
    ) -> AsyncIterator[Rule]:
        '''Enumerate rules'''
        async for row in self.database.fetchmany(
            _SELECT_RULES, {'opsystem': opsystem.value}
        ):
            yield _rule_from_row(row)

    async def delete_external_ptr(self, opsystem: OperatingSystem):
        """Delete external PTR"""
        parameters = {'opsystem': opsystem.value}
        await self.database.execute(_DELETE_EXTERNAL_PROFILES, parameters)
        await self.database.execute(_DELETE_EXTERNAL_TARGETS, parameters)
        await self.database.execute(_DELETE_EXTERNAL_RULES, parameters)


def get_ptr_storage(app_or_req: Application | Request) -> PTRStorage:
    '''Retrieve PTRStorage instance from request or application'''
    if isinstance(app_or_req, Request):
        app_or_req = app_or_req.app
    return app_or_req[_PTR_STORAGE]
