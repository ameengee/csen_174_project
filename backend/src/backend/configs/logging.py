import json
import logging
import sys

import structlog
from structlog.typing import EventDict, Processor, WrappedLogger

from .settings import get_settings


def _console_exception_to_str(
    logger: WrappedLogger, method: str, event_dict: EventDict
) -> EventDict:
    """Flatten dict_tracebacks' exception list to a string so ConsoleRenderer can't crash on it."""
    exc = event_dict.get("exception")
    if isinstance(exc, list):
        event_dict["exception"] = json.dumps(exc, default=str)
    return event_dict


def configure_logging() -> None:
    """Configure structlog with environment-based formatting (JSON or console)."""
    settings = get_settings()
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.dict_tracebacks,
    ]

    processors: list[Processor]
    if settings.json_logs:
        processors = shared_processors + [structlog.processors.JSONRenderer()]
    else:
        processors = shared_processors + [
            _console_exception_to_str,
            structlog.dev.ConsoleRenderer(),
        ]

    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=log_level)

    for noisy in ["uvicorn.access", "httpx", "httpcore"]:
        logging.getLogger(noisy).propagate = False
        logging.getLogger(noisy).setLevel(logging.WARNING)

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
