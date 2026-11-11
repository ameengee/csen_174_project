from fastapi import APIRouter

from backend.server.routes import health, jobs, profile

router = APIRouter()
router.include_router(health.router)
router.include_router(profile.router)
router.include_router(jobs.router)

__all__ = ["router"]
