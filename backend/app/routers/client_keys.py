from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from app.database import get_db
from app.models import ClientAPIKey, User
from app.services.auth import get_current_user, generate_client_api_key, hash_client_api_key, mask_api_key

router = APIRouter(prefix="/client-keys", tags=["client-keys"])


class CreateKeyRequest(BaseModel):
    name: str | None = None
    rotate: bool = True


class UpdateKeyRequest(BaseModel):
    is_active: bool


@router.get("")
async def list_keys(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ClientAPIKey).where(ClientAPIKey.user_id == user.id).order_by(ClientAPIKey.created_at.desc())
    )
    keys = result.scalars().all()
    return [
        {
            "id": k.id,
            "name": k.name,
            "prefix": k.prefix,
            "is_active": k.is_active,
            "created_at": k.created_at,
            "last_used_at": k.last_used_at,
        }
        for k in keys
    ]


@router.post("")
async def create_key(
    data: CreateKeyRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if data.rotate:
        await db.execute(
            update(ClientAPIKey)
            .where(ClientAPIKey.user_id == user.id)
            .values(is_active=False)
        )

    raw = generate_client_api_key()
    key_hash = hash_client_api_key(raw)
    prefix = raw.split("-", 1)[0] + "-" + raw.split("-", 1)[1][:4]
    obj = ClientAPIKey(
        user_id=user.id,
        name=(data.name or "default"),
        key_hash=key_hash,
        prefix=prefix,
        is_active=True,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return {"api_key": raw, "api_key_masked": mask_api_key(raw), "id": obj.id}


@router.patch("/{key_id}")
async def update_key(
    key_id: int,
    data: UpdateKeyRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ClientAPIKey).where(ClientAPIKey.id == key_id, ClientAPIKey.user_id == user.id)
    )
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Key not found")
    obj.is_active = bool(data.is_active)
    await db.commit()
    return {"id": obj.id, "is_active": obj.is_active}


@router.delete("/{key_id}")
async def delete_key(
    key_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ClientAPIKey).where(ClientAPIKey.id == key_id, ClientAPIKey.user_id == user.id)
    )
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Key not found")

    await db.execute(
        delete(ClientAPIKey).where(ClientAPIKey.id == key_id, ClientAPIKey.user_id == user.id)
    )
    await db.commit()
    return {"message": "deleted"}
