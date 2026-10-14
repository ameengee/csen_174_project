from fastapi import APIRouter, File, Form, Request, UploadFile

from backend.configs.constants import MAX_UPLOAD_BYTES
from backend.configs.exceptions import InvalidRequestError
from backend.server.rate_limit import RateLimit, limiter
from backend.services.profile_analysis import ProfileAnalysis, analyze_profile
from backend.services.profile_input import build_profile_content

router = APIRouter(prefix="/profile", tags=["profile"])


@router.post("/analyze")
@limiter.limit(RateLimit.DEFAULT)
async def analyze(
    request: Request,
    file: UploadFile = File(...),
    notes: str | None = Form(None),
) -> ProfileAnalysis:
    """Read an uploaded LinkedIn profile and return the parsed profile plus job targets."""
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if not data:
        raise InvalidRequestError("The uploaded file is empty")
    if len(data) > MAX_UPLOAD_BYTES:
        raise InvalidRequestError("The uploaded file is too large")

    content = build_profile_content(data)
    return await analyze_profile(content, (notes or "").strip() or None)
