from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import ApiKey, RequestLog, User


async def get_user_rpm(db: AsyncSession, user: User) -> int:
    if user.manual_rpm is not None:
        return max(0, user.manual_rpm)

    if not settings.auto_quota_enabled:
        return max(0, settings.manual_global_rpm)

    result = await db.execute(
        select(func.count(ApiKey.id))
        .where(ApiKey.status == "healthy")
        .where(ApiKey.is_enabled == True)
    )
    healthy_count = result.scalar() or 0

    rpm = settings.base_rpm + healthy_count * settings.per_key_rpm
    rpm = min(rpm, settings.max_rpm) if settings.max_rpm > 0 else rpm
    return max(0, rpm)


async def enforce_rate_limit(db: AsyncSession, user: User) -> None:
    rpm = await get_user_rpm(db, user)
    if rpm <= 0:
        raise PermissionError("No quota available")

    window_start = datetime.utcnow() - timedelta(seconds=60)
    result = await db.execute(
        select(func.count(RequestLog.id))
        .where(RequestLog.user_id == user.id)
        .where(RequestLog.created_at >= window_start)
    )
    used = result.scalar() or 0
    if used >= rpm:
        raise PermissionError(f"Rate limit exceeded ({used}/{rpm} per minute)")
