from fastapi import APIRouter, Request

from backend.server.rate_limit import RateLimit, limiter
from backend.services.job_search import JobSearchRequest, JobSearchResponse, search_jobs

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/search")
@limiter.limit(RateLimit.DEFAULT)
async def search(request: Request, body: JobSearchRequest) -> JobSearchResponse:
    """Find listed jobs at the chosen level, grouped by the roles they fit."""
    return await search_jobs(body)
