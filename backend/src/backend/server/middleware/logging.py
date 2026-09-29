import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request, Response

log = structlog.get_logger(__name__)


async def logging_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Log request details with request ID tracking and context propagation."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start = time.perf_counter()

    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    )

    response = None
    try:
        response = await call_next(request)
        return response

    except Exception:
        log.exception("unhandled_exception")
        raise

    finally:
        duration_ms = (time.perf_counter() - start) * 1000

        if request.url.path != "/healthz":
            log.info(
                "request_completed",
                status_code=response.status_code if response else 500,
                duration_ms=round(duration_ms, 2),
            )

        structlog.contextvars.clear_contextvars()
