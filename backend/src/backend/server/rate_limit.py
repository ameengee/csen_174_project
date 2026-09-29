from enum import StrEnum

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.configs.settings import get_settings

_is_local = get_settings().app_env.lower() == "local"


def ip_address_rate_limit_key(request: Request) -> str:
    """Extract rate limit key from the remote address."""
    return get_remote_address(request)


# In-memory counters. Swap storage_uri to a Redis URL once there is more than one instance.
limiter = Limiter(key_func=ip_address_rate_limit_key)


class RateLimit(StrEnum):
    """Per-endpoint limits; relaxed to effectively-unlimited in local dev."""

    HEALTH = "10000/minute" if _is_local else "60/minute"  # health check endpoint
    ROOT = "10000/minute" if _is_local else "30/minute"  # root endpoint
    DEFAULT = "10000/minute" if _is_local else "120/minute"  # everything else
