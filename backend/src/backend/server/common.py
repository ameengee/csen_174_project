from collections.abc import Callable
from typing import TypeVar

from .rate_limit import RateLimit, limiter

F = TypeVar("F", bound=Callable)


def limit(rate: RateLimit) -> Callable[[F], F]:
    """Apply a rate limit to a route."""

    def decorator(func: F) -> F:
        return limiter.limit(rate)(func)

    return decorator
