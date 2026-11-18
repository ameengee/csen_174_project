from fastapi import APIRouter

from backend.server.routes import health, jobs, profile, auth, tailor

router = APIRouter()
router.include_router(health.router)
router.include_router(profile.router)
router.include_router(jobs.router)
router.include_router(auth.router, prefix="/api/auth", tags=["auth"])
router.include_router(tailor.router, prefix="/api/tailor", tags=["tailor"])
__all__ = ["router"]
