"""
Authentication hardening helpers.

Implements basic anti-bruteforce protections:
- per-IP rate limit (login / register)
- (ip + username) lockout after repeated failed logins
All records are stored in DB so it works in multi-node shared database mode.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import AuthAttempt


async def enforce_auth_rate_limits(
    db: AsyncSession,
    *,
    ip_address: str | None,
    username: str | None,
    action: str,
) -> None:
    now = datetime.utcnow()

    if action == "login":
        per_minute = max(0, int(settings.auth_login_rate_limit_per_minute))
        if per_minute > 0:
            window_start = now - timedelta(seconds=60)
            result = await db.execute(
                select(func.count(AuthAttempt.id))
                .where(AuthAttempt.action == "login")
                .where(AuthAttempt.ip_address == ip_address)
                .where(AuthAttempt.created_at >= window_start)
            )
            used = result.scalar() or 0
            if used >= per_minute:
                raise HTTPException(status_code=429, detail="Too many login attempts, please retry later")

        threshold = max(0, int(settings.auth_login_lockout_threshold))
        lockout_minutes = max(1, int(settings.auth_login_lockout_minutes))
        if threshold > 0:
            window_start = now - timedelta(minutes=lockout_minutes)
            result = await db.execute(
                select(func.count(AuthAttempt.id))
                .where(AuthAttempt.action == "login")
                .where(AuthAttempt.success == False)
                .where(AuthAttempt.ip_address == ip_address)
                .where(AuthAttempt.username == username)
                .where(AuthAttempt.created_at >= window_start)
            )
            fails = result.scalar() or 0
            if fails >= threshold:
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many failed logins, locked for {lockout_minutes} minutes",
                )

    if action == "register":
        per_minute = max(0, int(settings.auth_register_rate_limit_per_minute))
        if per_minute > 0:
            window_start = now - timedelta(seconds=60)
            result = await db.execute(
                select(func.count(AuthAttempt.id))
                .where(AuthAttempt.action == "register")
                .where(AuthAttempt.ip_address == ip_address)
                .where(AuthAttempt.created_at >= window_start)
            )
            used = result.scalar() or 0
            if used >= per_minute:
                raise HTTPException(status_code=429, detail="Too many registrations, please retry later")


async def record_auth_attempt(
    db: AsyncSession,
    *,
    ip_address: str | None,
    username: str | None,
    action: str,
    success: bool,
) -> None:
    db.add(
        AuthAttempt(
            ip_address=ip_address,
            username=(username or "")[:50] if username else None,
            action=action,
            success=bool(success),
        )
    )
    await db.commit()
