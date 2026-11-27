from datetime import UTC, datetime, timedelta

import jwt
import structlog
from fastapi import APIRouter, HTTPException, Request
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

from backend.configs.settings import get_settings
from backend.database import users
from backend.server.rate_limit import RateLimit, limiter

log = structlog.get_logger(__name__)
router = APIRouter()

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
ALGORITHM = "HS256"


class UserAuth(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordUpdate(BaseModel):
    token: str
    new_password: str


def create_jwt_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    to_encode.update({"exp": datetime.now(UTC) + expires_delta})
    return jwt.encode(to_encode, get_settings().jwt_secret, algorithm=ALGORITHM)


def decode_jwt_token(token: str) -> dict:
    """Decoded token payload; raises HTTPException(400) if invalid or expired."""
    try:
        return jwt.decode(token, get_settings().jwt_secret, algorithms=[ALGORITHM])
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=400, detail="Invalid or expired token") from e


@router.post("/register")
@limiter.limit(RateLimit.AUTH)
async def register_user(request: Request, user: UserAuth):
    settings = get_settings()
    needs_verify = settings.require_email_verification
    created = await users.create_user(
        user.email, pwd_context.hash(user.password), user.full_name, verified=not needs_verify
    )
    if not created:
        raise HTTPException(status_code=400, detail="Email already registered")

    if not needs_verify:
        return {"message": "Account created! You can now log in."}

    token = create_jwt_token({"sub": user.email.lower(), "type": "verify"}, timedelta(hours=24))
    verify_link = f"{settings.public_api_url}/api/auth/verify?token={token}"

    log.info("========== 📧 NEW EMAIL INTERCEPTED ==========")
    log.info(f"To: {user.email}")
    log.info(f"Subject: Welcome {user.full_name}! Verify your account")
    log.info(f"Click here to verify: {verify_link}")
    log.info("==============================================")

    return {"message": "Verification link sent! (Check your backend terminal)"}


@router.get("/verify")
@limiter.limit(RateLimit.AUTH)
async def verify_email(request: Request, token: str):
    payload = decode_jwt_token(token)
    if payload.get("type") == "verify" and await users.mark_verified(payload.get("sub", "")):
        return {"message": "Email verified successfully! You can now close this tab and log in."}
    raise HTTPException(status_code=400, detail="Invalid or expired token")


@router.post("/login")
@limiter.limit(RateLimit.AUTH)
async def login_user(request: Request, user: UserAuth):
    db_user = await users.get_user(user.email)

    if not db_user or not pwd_context.verify(user.password, db_user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not db_user["verified"]:
        raise HTTPException(
            status_code=403, detail="Please verify your email first! (Check terminal)"
        )

    access_token = create_jwt_token({"sub": db_user["email"]}, timedelta(hours=1))
    return {"access_token": access_token}


@router.post("/forgot-password")
@limiter.limit(RateLimit.AUTH)
async def forgot_password(request: Request, req: PasswordReset):
    if await users.get_user(req.email):
        reset_token = create_jwt_token(
            {"sub": req.email.lower(), "type": "reset"}, timedelta(minutes=15)
        )
        reset_link = f"{get_settings().frontend_url}/login?reset_token={reset_token}"

        log.info("========== 🔒 PASSWORD RESET REQUEST ==========")
        log.info(f"To: {req.email}")
        log.info(f"Click here to reset your password: {reset_link}")
        log.info("===============================================")

    return {"message": "If an account exists, a reset link has been sent."}


@router.post("/reset-password")
@limiter.limit(RateLimit.AUTH)
async def reset_password(request: Request, req: PasswordUpdate):
    payload = decode_jwt_token(req.token)
    if payload.get("type") == "reset" and await users.set_password(
        payload.get("sub", ""), pwd_context.hash(req.new_password)
    ):
        return {"message": "Password successfully reset! You can now log in."}
    raise HTTPException(status_code=400, detail="Invalid or expired reset link.")
