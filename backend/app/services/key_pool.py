from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy import select, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import ApiKey
from app.services.crypto import decrypt_text


async def select_healthy_key(db: AsyncSession) -> Optional[Tuple[ApiKey, str]]:
    now = datetime.utcnow()
    cutoff = now - timedelta(seconds=settings.key_cooldown_seconds)
    query = (
        select(ApiKey)
        .where(ApiKey.status == "healthy")
        .where(ApiKey.is_enabled == True)
        .where((ApiKey.cooldown_until == None) | (ApiKey.cooldown_until <= now))
        .where((ApiKey.last_used_at == None) | (ApiKey.last_used_at <= cutoff))
        .order_by(ApiKey.last_used_at.asc().nullsfirst(), ApiKey.id.asc())
        .limit(1)
    )
    if settings.require_opus_tier:
        query = query.where(ApiKey.tier == 3)
    result = await db.execute(query)
    key = result.scalar_one_or_none()
    if not key:
        return None
    return key, decrypt_text(key.key_encrypted)
