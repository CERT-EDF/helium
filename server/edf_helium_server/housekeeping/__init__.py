"""Housekeeping module"""

from asyncio import Event, wait_for
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from ..ptr_storage import PTRStorage
from ..storage import Storage


@dataclass(kw_only=True)
class HousekeepingTask:
    """Housekeeping Task"""

    name: str
    routine: Callable[[Storage, PTRStorage], Awaitable[bool]]
    frequency: int

    async def run(
        self, stop: Event, storage: Storage, ptr_storage: PTRStorage
    ):
        """Housekeeping Task Loop"""
        while not stop.is_set():
            await self.routine(storage, ptr_storage)
            try:
                await wait_for(stop.wait(), self.frequency)
            except TimeoutError:
                continue
