import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import structlog

from backend.configs.types import WorkerSpec

log = structlog.get_logger(__name__)


class RuntimeManager:
    def __init__(self) -> None:
        self.workers: list[WorkerSpec] = []
        self.shutdown_event = asyncio.Event()
        self.total_restarts: int = 0

    async def start(self) -> None:
        """Launch background workers. Register new ones here with _spawn_worker."""
        log.info("runtime_manager_started")

    async def stop(self) -> None:
        """Cancel all workers and await clean shutdown."""
        self.shutdown_event.set()

        tasks = [worker.task for worker in self.workers if worker.task is not None]
        for task in tasks:
            task.cancel()

        await asyncio.gather(*tasks, return_exceptions=True)

    def get_health_snapshot(self) -> int:
        """Return restart counts for health reporting."""
        return self.total_restarts

    # ============================================================
    # Core Worker Logic
    # ============================================================
    def _spawn_worker(self, name: str, factory: Callable[[], Awaitable[Any]]) -> None:
        """Create a worker task with automatic restart on crash."""
        worker = WorkerSpec(name=name, factory=factory, task=None)

        def _restart(task: asyncio.Task, *, worker: WorkerSpec = worker) -> None:
            """Restart a crashed worker task."""
            if self.shutdown_event.is_set() or task.cancelled():
                return
            exc = task.exception()
            log.warning("worker_crashed", worker=worker.name, error=str(exc) if exc else None)

            self.total_restarts += 1
            new_task = asyncio.ensure_future(worker.factory())
            new_task.set_name(worker.name)
            worker.task = new_task
            new_task.add_done_callback(_restart)

        task = asyncio.ensure_future(factory())
        task.set_name(name)
        worker.task = task
        task.add_done_callback(_restart)

        self.workers.append(worker)
