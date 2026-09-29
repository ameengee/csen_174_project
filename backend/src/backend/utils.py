import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import Any, ParamSpec, TypeVar

import structlog

log = structlog.get_logger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


async def async_with_retries(
    func: Callable[P, Awaitable[R]],
    *args: Any,
    operation: str,
    max_attempts: int = 3,
    base_delay: float = 0.2,
    retry_on: tuple[type[BaseException], ...] = (Exception,),
    **kwargs: Any,
) -> R:
    """Retry async function with exponential backoff on specified exceptions."""
    for attempt in range(1, max_attempts + 1):
        try:
            return await func(*args, **kwargs)
        except retry_on as e:
            if attempt == max_attempts:
                raise
            sleep_time = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.1)
            log.debug(
                "retry_attempt",
                function=func.__name__,
                operation=operation,
                attempt=attempt,
                max_attempts=max_attempts,
                error_type=type(e).__name__,
                error=str(e),
                sleep_seconds=sleep_time,
            )
            await asyncio.sleep(sleep_time)

    # Defensive: should never be reached
    raise RuntimeError("Retry loop completed without returning")


# asyncio only holds a WEAK reference to a running task, so a bare `asyncio.create_task(...)`
# whose result nobody keeps can be collected mid-flight. Anchor fire-and-forget tasks here.
_inflight: set[asyncio.Task[Any]] = set()


def fire_and_forget(coro: Awaitable[Any], *, name: str | None = None) -> None:
    """Run `coro` in the background, holding a reference until it completes."""
    task = asyncio.ensure_future(coro)
    if name is not None:
        task.set_name(name)
    _inflight.add(task)
    task.add_done_callback(_inflight.discard)
