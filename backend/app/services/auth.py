from datetime import datetime, timedelta
from typing import Optional

import hashlib
import secrets
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_db
from app.models import ClientAPIKey, User

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, expires_minutes: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def generate_client_api_key() -> str:
    return f"np-{secrets.token_urlsafe(32)}"


def hash_client_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def mask_api_key(api_key: str) -> str:
    if len(api_key) <= 10:
        return "***"
    return f"{api_key[:6]}...{api_key[-4:]}"


async def get_user_by_client_api_key(db: AsyncSession, api_key: str) -> User | None:
    key_hash = hash_client_api_key(api_key)
    result = await db.execute(
        select(ClientAPIKey).where(
            ClientAPIKey.key_hash == key_hash, ClientAPIKey.is_active == True
        )
    )
    key_obj = result.scalar_one_or_none()
    if not key_obj:
        return None
    result = await db.execute(select(User).where(User.id == key_obj.user_id))
    return result.scalar_one_or_none()


async def get_current_user_any(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    # Heuristic: JWT contains 2 dots; client API key starts with np-
    if token.startswith("np-") and token.count(".") < 2:
        user = await get_user_by_client_api_key(db, token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid API key")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="User disabled")
        return user

    return await get_current_user(token=token, db=db)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        username: Optional[str] = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=403, detail="User disabled")
    return user
