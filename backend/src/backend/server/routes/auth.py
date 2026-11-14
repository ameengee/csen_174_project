from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
import jwt
import structlog

log = structlog.get_logger(__name__)
router = APIRouter()

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
SECRET_KEY = "csen174-super-secret-jwt-key"
ALGORITHM = "HS256"

# Strict, empty database for resilience testing
FAKE_DB = {}

class UserAuth(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordUpdate(BaseModel):
    token: str
    new_password: str

def create_jwt_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    to_encode.update({"exp": datetime.now(timezone.utc) + expires_delta})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/register")
async def register_user(user: UserAuth):
    if user.email in FAKE_DB:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    FAKE_DB[user.email] = {
        "password": pwd_context.hash(user.password),
        "name": user.full_name,
        "verified": False
    }
    
    token = create_jwt_token({"sub": user.email}, timedelta(hours=24))
    verify_link = f"http://localhost:8001/api/auth/verify?token={token}"
    
    log.info("========== 📧 NEW EMAIL INTERCEPTED ==========")
    log.info(f"To: {user.email}")
    log.info(f"Subject: Welcome {user.full_name}! Verify your account")
    log.info(f"Click here to verify: {verify_link}")
    log.info("==============================================")
    
    return {"message": "Verification link sent! (Check your backend terminal)"}

@router.get("/verify")
async def verify_email(token: str):
    try:
        email = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]).get("sub")
        if email in FAKE_DB:
            FAKE_DB[email]["verified"] = True
            return {"message": "Email verified successfully! You can now close this tab and log in."}
    except:
        pass
    raise HTTPException(status_code=400, detail="Invalid or expired token")

@router.post("/login")
async def login_user(user: UserAuth):
    db_user = FAKE_DB.get(user.email)
    
    if not db_user or not pwd_context.verify(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    if not db_user["verified"]:
        raise HTTPException(status_code=403, detail="Please verify your email first! (Check terminal)")

    access_token = create_jwt_token({"sub": user.email}, timedelta(hours=1))
    return {"access_token": access_token}

@router.post("/forgot-password")
async def forgot_password(req: PasswordReset):
    if req.email in FAKE_DB:
        reset_token = create_jwt_token({"sub": req.email, "type": "reset"}, timedelta(minutes=15))
        reset_link = f"http://localhost:3000/login?reset_token={reset_token}"
        
        log.info("========== 🔒 PASSWORD RESET REQUEST ==========")
        log.info(f"To: {req.email}")
        log.info(f"Click here to reset your password: {reset_link}")
        log.info("===============================================")
        
    return {"message": "If an account exists, a reset link has been sent."}

@router.post("/reset-password")
async def reset_password(req: PasswordUpdate):
    try:
        payload = jwt.decode(req.token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        
        if email in FAKE_DB and payload.get("type") == "reset":
            FAKE_DB[email]["password"] = pwd_context.hash(req.new_password)
            return {"message": "Password successfully reset! You can now log in."}
    except:
        pass
    raise HTTPException(status_code=400, detail="Invalid or expired reset link.")
