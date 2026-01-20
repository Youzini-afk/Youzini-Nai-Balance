import asyncio
import hashlib
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_db
from app.models import ApiKey, RequestLog, SystemConfig, User
from app.services.auth import get_current_user
from app.services.crypto import encrypt_text
from app.services.health_check import check_all_keys, check_key_health
from app.services.upstream_proxy_pool import UpstreamProxyPool
from app.tasks.scheduler import reconcile_background_tasks
from app.services.system_config import is_config_key_allowed

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(user: User) -> None:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")


def _cast_value(value: str, current):
    if isinstance(current, bool):
        return value.lower() in ("1", "true", "yes", "on")
    if isinstance(current, int):
        return int(value)
    return value


class ConfigUpdate(BaseModel):
    key: str
    value: str


class UserUpdate(BaseModel):
    manual_rpm: int | None = None
    is_active: bool | None = None


class AdminKeyUploadRequest(BaseModel):
    api_keys: str
    verify_now: bool = True


def _split_api_keys(value: str) -> list[str]:
    parts = re.split(r"[\s,]+", (value or "").strip())
    return [p.strip() for p in parts if p and p.strip()]


@router.get("/users")
async def list_users(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    require_admin(user)
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "manual_rpm": u.manual_rpm,
            "created_at": u.created_at,
        }
        for u in users
    ]


@router.get("/keys")
async def list_keys(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    require_admin(user)
    result = await db.execute(
        select(ApiKey, User.username)
        .join(User, User.id == ApiKey.user_id)
        .order_by(ApiKey.id.asc())
    )
    rows = result.all()
    return [
        {
            "id": k.id,
            "user_id": k.user_id,
            "username": username,
            "status": k.status,
            "tier": k.tier,
            "is_enabled": k.is_enabled,
            "fail_streak": k.fail_streak,
            "cooldown_until": k.cooldown_until,
            "last_checked_at": k.last_checked_at,
        }
        for (k, username) in rows
    ]


@router.post("/keys")
async def upload_keys(
    data: AdminKeyUploadRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    require_admin(user)
    keys_raw = _split_api_keys(data.api_keys)
    if not keys_raw:
        raise HTTPException(status_code=400, detail="Empty key list")

    unique_by_hash: dict[str, str] = {}
    for raw in keys_raw:
        key_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        unique_by_hash.setdefault(key_hash, raw)

    hashes = list(unique_by_hash.keys())
    existing = await db.execute(select(ApiKey.key_hash).where(ApiKey.key_hash.in_(hashes)))
    existing_hashes = set(existing.scalars().all())

    created: list[ApiKey] = []
    for key_hash, raw in unique_by_hash.items():
        if key_hash in existing_hashes:
            continue
        key = ApiKey(
            user_id=user.id,
            key_encrypted=encrypt_text(raw),
            key_hash=key_hash,
            status="pending",
        )
        db.add(key)
        created.append(key)

    await db.flush()

    if data.verify_now:
        for key in created:
            await check_key_health(db, key)

    await db.commit()

    return {
        "created": [{"id": k.id, "status": k.status, "tier": k.tier} for k in created],
        "skipped_existing": len(existing_hashes),
        "received": len(keys_raw),
        "deduped": len(hashes),
    }


@router.post("/keys/{key_id}/toggle")
async def toggle_key(
    key_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    require_admin(user)
    result = await db.execute(select(ApiKey).where(ApiKey.id == key_id))
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    key.is_enabled = not key.is_enabled
    await db.commit()
    return {"id": key.id, "is_enabled": key.is_enabled}


@router.post("/config")
async def update_config(
    data: ConfigUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    require_admin(user)
    key = (data.key or "").strip()
    if not is_config_key_allowed(key):
        raise HTTPException(status_code=400, detail="This config key is not allowed via API")
    result = await db.execute(select(SystemConfig).where(SystemConfig.key == key))
    item = result.scalar_one_or_none()
    if not item:
        item = SystemConfig(key=key, value=data.value)
        db.add(item)
    else:
        item.value = data.value
    if hasattr(settings, key):
        current = getattr(settings, key)
        setattr(settings, key, _cast_value(data.value, current))
    await db.commit()
    try:
        reconcile_background_tasks(asyncio.get_running_loop())
    except RuntimeError:
        pass
    return {"key": data.key, "value": data.value}


@router.get("/config")
async def get_config(
    user: User = Depends(get_current_user),
):
    require_admin(user)
    return {
        "node_id": settings.node_id,
        "multi_node_enabled": settings.multi_node_enabled,
        "auto_quota_enabled": settings.auto_quota_enabled,
        "base_rpm": settings.base_rpm,
        "per_key_rpm": settings.per_key_rpm,
        "max_rpm": settings.max_rpm,
        "base_rpm_contributor_only": settings.base_rpm_contributor_only,
        "manual_global_rpm": settings.manual_global_rpm,
        "key_cooldown_seconds": settings.key_cooldown_seconds,
        "dynamic_cooldown_enabled": settings.dynamic_cooldown_enabled,
        "cooldown_max_seconds": settings.cooldown_max_seconds,
        "cooldown_409_base_seconds": settings.cooldown_409_base_seconds,
        "cooldown_429_base_seconds": settings.cooldown_429_base_seconds,
        "cooldown_5xx_base_seconds": settings.cooldown_5xx_base_seconds,
        "cooldown_402_base_seconds": settings.cooldown_402_base_seconds,
        "opus_max_pixels": settings.opus_max_pixels,
        "opus_max_steps": settings.opus_max_steps,
        "opus_max_samples": settings.opus_max_samples,
        "allow_registration": settings.allow_registration,
        "require_opus_tier": settings.require_opus_tier,
        "health_check_enabled": settings.health_check_enabled,
        "health_check_interval_seconds": settings.health_check_interval_seconds,
        "health_check_fail_threshold": settings.health_check_fail_threshold,
        "health_check_leader_only": settings.health_check_leader_only,
        "health_check_leader_node_id": settings.health_check_leader_node_id,
        "upstream_proxy_mode": settings.upstream_proxy_mode,
        "upstream_proxy_strategy": settings.upstream_proxy_strategy,
        "upstream_proxy_sticky_salt": settings.upstream_proxy_sticky_salt,
        "upstream_proxy_cooldown_seconds": settings.upstream_proxy_cooldown_seconds,
        "upstream_proxy_max_cooldown_seconds": settings.upstream_proxy_max_cooldown_seconds,
        "upstream_proxy_failure_threshold": settings.upstream_proxy_failure_threshold,
        "upstream_proxy_fail_streak_cap": settings.upstream_proxy_fail_streak_cap,
        "upstream_proxy_handle_429": settings.upstream_proxy_handle_429,
        "upstream_proxy_handle_5xx": settings.upstream_proxy_handle_5xx,
        "upstream_proxy_handle_network_errors": settings.upstream_proxy_handle_network_errors,
        "upstream_proxy_cooldown_429_seconds": settings.upstream_proxy_cooldown_429_seconds,
        "upstream_proxy_cooldown_5xx_seconds": settings.upstream_proxy_cooldown_5xx_seconds,
        "upstream_proxy_cooldown_error_seconds": settings.upstream_proxy_cooldown_error_seconds,
        "upstream_proxy_keepalive_enabled": settings.upstream_proxy_keepalive_enabled,
        "upstream_proxy_keepalive_interval_seconds": settings.upstream_proxy_keepalive_interval_seconds,
        "upstream_proxy_keepalive_url": settings.upstream_proxy_keepalive_url,
        "upstream_proxy_keepalive_timeout_seconds": settings.upstream_proxy_keepalive_timeout_seconds,
        "upstream_proxy_keepalive_leader_only": settings.upstream_proxy_keepalive_leader_only,
        "upstream_proxy_keepalive_leader_node_id": settings.upstream_proxy_keepalive_leader_node_id,
        "upstream_proxies_configured": bool(settings.upstream_proxies.strip()),
    }


@router.get("/proxy-pool")
async def proxy_pool_status(user: User = Depends(get_current_user)):
    require_admin(user)
    return {
        "enabled": UpstreamProxyPool.enabled(),
        "mode": settings.upstream_proxy_mode,
        "strategy": settings.upstream_proxy_strategy,
        "items": UpstreamProxyPool.snapshot(),
    }


@router.post("/health-check")
async def trigger_health_check(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    require_admin(user)
    total = await check_all_keys(db)
    return {"checked": total}


@router.patch("/users/{user_id}")
async def update_user(
    user_id: int,
    data: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    require_admin(user)
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if data.manual_rpm is not None:
        target.manual_rpm = data.manual_rpm
    if data.is_active is not None:
        target.is_active = data.is_active
    await db.commit()
    return {"id": target.id, "manual_rpm": target.manual_rpm, "is_active": target.is_active}


@router.get("/logs")
async def list_logs(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    require_admin(user)
    result = await db.execute(
        select(RequestLog, User.username)
        .join(User, User.id == RequestLog.user_id)
        .order_by(RequestLog.created_at.desc())
        .limit(200)
    )
    rows = result.all()
    return [
        {
            "id": log.id,
            "username": username,
            "action": log.action,
            "status": log.status,
            "status_code": log.status_code,
            "api_key_id": log.api_key_id,
            "latency_ms": log.latency_ms,
            "reject_reason": log.reject_reason,
            "created_at": log.created_at,
        }
        for (log, username) in rows
    ]
