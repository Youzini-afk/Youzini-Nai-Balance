"""
SystemConfig (DB-backed) loader.

In multi-node mode, nodes periodically refresh allowed SystemConfig keys from the shared DB
and apply them to in-process `settings`. Sensitive keys are blocked to avoid foot-guns.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import SystemConfig


FORBIDDEN_CONFIG_KEYS: set[str] = {
    # Security / secrets
    "secret_key",
    "encryption_key",
    "admin_password",
    "admin_username",
    # Runtime identity / deployment-critical
    "database_url",
    "node_id",
    "multi_node_enabled",
    # Prevent config-refresh self-mutation via DB
    "system_config_refresh_enabled",
    "system_config_refresh_interval_seconds",
    # JWT knobs (avoid foot-guns)
    "jwt_algorithm",
    "access_token_expire_minutes",
    # CORS / proxy trust are startup-time knobs; changing via DB is confusing.
    "cors_allow_origins",
    "cors_allow_credentials",
    "trust_proxy_headers",
    # Feature removed: request IP logging.
    "log_request_ip",
}


def is_config_key_allowed(key: str) -> bool:
    k = (key or "").strip()
    if not k:
        return False
    return k not in FORBIDDEN_CONFIG_KEYS


def _cast_value(value: str | None, current: Any) -> Any:
    if value is None:
        return None
    if isinstance(current, bool):
        return value.strip().lower() in ("1", "true", "yes", "on")
    if isinstance(current, int):
        return int(value)
    return value


async def get_system_config_updated_at(db: AsyncSession) -> datetime | None:
    result = await db.execute(select(func.max(SystemConfig.updated_at)))
    return result.scalar_one_or_none()


async def load_system_config_into_settings(db: AsyncSession) -> datetime | None:
    """
    Load SystemConfig from DB and apply to in-process settings.
    This enables multi-node consistency when nodes share the same DB.
    """
    result = await db.execute(select(SystemConfig))
    items = result.scalars().all()
    for item in items:
        key = (item.key or "").strip()
        if not key:
            continue
        if not is_config_key_allowed(key):
            continue
        if hasattr(settings, key):
            current = getattr(settings, key)
            setattr(settings, key, _cast_value(item.value, current))
    return await get_system_config_updated_at(db)
