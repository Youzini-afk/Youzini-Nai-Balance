from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_db
from app.models import User
from app.services.auth_hardening import enforce_auth_rate_limits, record_auth_attempt
from app.services.request_meta import get_client_ip
from app.services.auth import (
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr | None = None
    password: str
    confirm_password: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/register")
async def register(request: Request, data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Registration can be disabled by admin config and is also rate-limited by IP.
    if not settings.allow_registration:
        raise HTTPException(status_code=403, detail="Registration disabled")

    ip_address = get_client_ip(request)
    await enforce_auth_rate_limits(db, ip_address=ip_address, username=data.username, action="register")

    if data.confirm_password is not None and data.password != data.confirm_password:
        await record_auth_attempt(db, ip_address=ip_address, username=data.username, action="register", success=False)
        raise HTTPException(status_code=400, detail="Passwords do not match")
    if len(data.password or "") < max(1, int(settings.auth_password_min_length)):
        await record_auth_attempt(db, ip_address=ip_address, username=data.username, action="register", success=False)
        raise HTTPException(status_code=400, detail="Password too short")

    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalar_one_or_none():
        await record_auth_attempt(db, ip_address=ip_address, username=data.username, action="register", success=False)
        raise HTTPException(status_code=409, detail="Username exists")
    if data.email:
        result = await db.execute(select(User).where(User.email == data.email))
        if result.scalar_one_or_none():
            await record_auth_attempt(db, ip_address=ip_address, username=data.username, action="register", success=False)
            raise HTTPException(status_code=409, detail="Email exists")
    user = User(
        username=data.username,
        email=data.email,
        hashed_password=get_password_hash(data.password),
    )
    db.add(user)
    await db.commit()
    await record_auth_attempt(db, ip_address=ip_address, username=data.username, action="register", success=True)
    return {"message": "registered"}


@router.post("/login")
async def login(request: Request, data: LoginRequest, db: AsyncSession = Depends(get_db)):
    ip_address = get_client_ip(request)
    await enforce_auth_rate_limits(db, ip_address=ip_address, username=data.username, action="login")
    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        await record_auth_attempt(db, ip_address=ip_address, username=data.username, action="login", success=False)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    await record_auth_attempt(db, ip_address=ip_address, username=data.username, action="login", success=True)
    token = create_access_token(user.username, settings.access_token_expire_minutes)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "manual_rpm": user.manual_rpm,
        "is_active": user.is_active,
    }
