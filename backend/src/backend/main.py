from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from backend.clients import close_clients, init_clients
from backend.configs.constants import API_VERSION
from backend.configs.exceptions import (
    InvalidRequestError,
    NotFoundError,
    UnauthorizedError,
    UpstreamError,
)
from backend.configs.logging import configure_logging
from backend.configs.settings import get_settings
from backend.managers import RuntimeManager
from backend.server import limiter, router
from backend.server.middleware import logging_middleware

# Setup logging
configure_logging()
log = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage FastAPI startup and shutdown lifecycle."""
    await init_clients()
    runtime_manager = RuntimeManager()
    app.state.runtime_manager = runtime_manager
    await runtime_manager.start()
    log.info("client_startup_successful")
    yield

    log.info("shutdown_begin")
    await runtime_manager.stop()
    await close_clients()
    log.info("shutdown_complete")


# Create FastAPI application
app = FastAPI(
    title="CSEN 174 API",
    description="Backend API for the CSEN 174 project",
    version=API_VERSION,
    lifespan=lifespan,
)


@app.middleware("http")
async def _auto_fail_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Refuse everything except health probes while AUTO_FAIL_ALL is set."""
    if get_settings().auto_fail_all and not request.url.path.startswith("/healthz"):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return await call_next(request)


@app.middleware("http")
async def _logging_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """FastAPI middleware that adds request details to logs."""
    return await logging_middleware(request, call_next)


app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Added last so it is outermost: preflight and error responses still carry CORS headers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return 429 response."""
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})


@app.exception_handler(InvalidRequestError)
async def invalid_request_handler(request: Request, exc: InvalidRequestError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc) or "Invalid request"})


@app.exception_handler(UnauthorizedError)
async def unauthorized_handler(request: Request, exc: UnauthorizedError) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": "Unauthorized"})


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc) or "Not found"})


@app.exception_handler(UpstreamError)
async def upstream_handler(request: Request, exc: UpstreamError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": str(exc) or "Upstream service failed"})


# Include router
app.include_router(router)
