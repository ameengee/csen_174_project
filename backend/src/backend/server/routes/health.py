import asyncio

import structlog
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from backend.clients import get_pool
from backend.configs.constants import (
    API_VERSION,
    EXTERNAL_SERVICE_TIMEOUT,
    RESTART_THRESHOLD,
    SERVICE_NAME,
)
from backend.server.rate_limit import RateLimit, limiter

router = APIRouter()
log = structlog.get_logger(__name__)


@router.get("/healthz")
@limiter.limit(RateLimit.HEALTH)
async def healthz(request: Request) -> dict[str, str]:
    """Return basic liveness check."""
    restart_counts = request.app.state.runtime_manager.get_health_snapshot()
    return {"status": "degraded" if restart_counts > RESTART_THRESHOLD else "ok"}


@router.get("/healthz/ready")
@limiter.limit(RateLimit.HEALTH)
async def readiness(request: Request) -> JSONResponse:
    """Check external dependencies and return readiness status."""
    checks = {"database": False}

    async def _check_database() -> None:
        try:
            pool = await asyncio.wait_for(get_pool(), timeout=EXTERNAL_SERVICE_TIMEOUT)
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            checks["database"] = True
        except Exception as e:
            log.error("health_check_db_failed", error=str(e))

    await asyncio.gather(_check_database())

    ready = all(checks.values())
    return JSONResponse(
        content={"status": "ready" if ready else "unhealthy", "checks": checks},
        status_code=200 if ready else 503,
    )


@router.get("/")
@limiter.limit(RateLimit.ROOT)
def root(request: Request) -> dict[str, str]:
    """Return service info and version."""
    return {"service": SERVICE_NAME, "status": "running", "version": API_VERSION}
