from datetime import datetime
from typing import Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models import ApiKey
from app.services.crypto import decrypt_text


SUBSCRIPTION_URL = "https://api.novelai.net/user/subscription"


def _mark_status(key: ApiKey, status: str, tier: Optional[int], error: Optional[str]) -> None:
    key.status = status
    key.tier = tier
    key.last_checked_at = datetime.utcnow()
    key.last_error = error


async def check_key_health(db: AsyncSession, key: ApiKey) -> None:
    raw_key = decrypt_text(key.key_encrypted)
    headers = {"Authorization": f"Bearer {raw_key}"}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(SUBSCRIPTION_URL, headers=headers)
        if resp.status_code == 401:
            _mark_status(key, "invalid", None, "Unauthorized")
            key.fail_streak += 1
        elif resp.status_code >= 400:
            key.fail_streak += 1
            if key.fail_streak >= settings.health_check_fail_threshold:
                _mark_status(key, "unhealthy", key.tier, f"HTTP {resp.status_code}")
            else:
                _mark_status(key, key.status, key.tier, f"HTTP {resp.status_code}")
        else:
            data = resp.json()
            tier = data.get("tier")
            # NovelAI Opus is tier=3
            if settings.require_opus_tier and tier != 3:
                _mark_status(key, "unhealthy", tier, "Not Opus tier")
            else:
                _mark_status(key, "healthy", tier, None)
                key.fail_streak = 0
    except Exception as exc:
        key.fail_streak += 1
        if key.fail_streak >= settings.health_check_fail_threshold:
            _mark_status(key, "unhealthy", key.tier, f"Error: {exc}")
        else:
            _mark_status(key, key.status, key.tier, f"Error: {exc}")


async def check_all_keys(db: AsyncSession) -> int:
    result = await db.execute(select(ApiKey).where(ApiKey.is_enabled == True))
    keys = result.scalars().all()
    for key in keys:
        await check_key_health(db, key)
    await db.commit()
    return len(keys)
