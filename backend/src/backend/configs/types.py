import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class EXTERNAL_OPERATION(StrEnum):
    """Names for calls to external dependencies, used in retry logs."""

    GET_POOL = "get_pool"


@dataclass
class WorkerSpec:
    """A background worker owned by the RuntimeManager."""

    name: str
    factory: Callable[[], Awaitable[Any]]
    task: asyncio.Task | None
