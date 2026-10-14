import asyncio

import structlog

from .llm import close_openai
from .postgres import close_db_connections, get_pool

log = structlog.get_logger(__name__)


async def init_clients() -> None:
    """Initialize all external service client singletons."""
    try:
        await get_pool()
    except Exception:
        log.warning("postgres_init_failed_continuing_without_postgres")


async def close_clients() -> None:
    """Close all external service clients concurrently."""
    await asyncio.gather(
        close_db_connections(),
        close_openai(),
        return_exceptions=True,
    )
