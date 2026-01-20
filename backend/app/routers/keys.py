import hashlib
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import ApiKey, User
from app.services.auth import get_current_user
from app.services.crypto import encrypt_text
from app.services.health_check import check_key_health

router = APIRouter(prefix="/keys", tags=["keys"])


class KeyUploadRequest(BaseModel):
    api_key: str
    verify_now: bool = True


@router.post("")
async def upload_key(
    data: KeyUploadRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    key_raw = data.api_key.strip()
    if not key_raw:
        raise HTTPException(status_code=400, detail="Empty key")
    key_hash = hashlib.sha256(key_raw.encode("utf-8")).hexdigest()
    result = await db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Key already exists")

    key = ApiKey(
        user_id=user.id,
        key_encrypted=encrypt_text(key_raw),
        key_hash=key_hash,
        status="pending",
    )
    db.add(key)
    await db.commit()
    await db.refresh(key)

    if data.verify_now:
        await check_key_health(db, key)
        await db.commit()

    return {"id": key.id, "status": key.status}


@router.get("")
async def list_my_keys(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ApiKey).where(ApiKey.user_id == user.id))
    keys = result.scalars().all()
    return [
        {
            "id": key.id,
            "status": key.status,
            "tier": key.tier,
            "is_enabled": key.is_enabled,
            "fail_streak": key.fail_streak,
            "last_checked_at": key.last_checked_at,
            "created_at": key.created_at,
        }
        for key in keys
    ]


@router.delete("/{key_id}")
async def delete_key(
    key_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user.id)
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    await db.delete(key)
    await db.commit()
    return {"message": "deleted"}
