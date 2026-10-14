from fastapi import APIRouter

from backend.server.routes import health, profile

router = APIRouter()
router.include_router(health.router)
router.include_router(profile.router)

__all__ = ["router"]
