from fastapi import APIRouter

from backend.server.routes import health

router = APIRouter()
router.include_router(health.router)

__all__ = ["router"]
