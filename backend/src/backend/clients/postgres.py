import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import asyncpg

from backend.configs.constants import POOL_RETRIES
from backend.configs.settings import get_settings
from backend.configs.types import EXTERNAL_OPERATION
from backend.utils import async_with_retries

_pool: asyncpg.Pool | None = None
_pool_lock = asyncio.Lock()


async def get_pool() -> asyncpg.Pool:
    """Get or create asyncpg connection pool singleton."""
    global _pool
    if _pool is not None:
        return _pool

    async def _create_pool() -> asyncpg.Pool:
        """Create and validate asyncpg connection pool."""
        settings = get_settings()
        pool = await asyncpg.create_pool(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_pass,
            database=settings.db_name,
            min_size=1,
            max_size=10,
            timeout=10,
            command_timeout=30,
        )
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return pool

    async with _pool_lock:
        if _pool is not None:
            return _pool

        _pool = await async_with_retries(
            _create_pool,
            operation=EXTERNAL_OPERATION.GET_POOL,
            max_attempts=POOL_RETRIES,
            base_delay=1.0,
        )
        return _pool


@asynccontextmanager
async def db_transaction(readonly: bool = False) -> AsyncIterator[asyncpg.Connection]:
    """Yield a connection within a transaction."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction(readonly=readonly):
            yield conn


async def close_db_connections() -> None:
    """Close database connection pool and release all connections."""
    global _pool
    if _pool is None:
        return

    async with _pool_lock:
        if _pool is None:
            return
        await _pool.close()
        _pool = None
