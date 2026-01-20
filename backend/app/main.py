"""
FastAPI application entry.

Notes:
- Serves the static frontend (`/` and `/assets`) if `frontend/` exists.
- Provides liveness/readiness endpoints (`/healthz`, `/readyz`).
- Adds security response headers and node id header.
- In multi-node mode, can refresh SystemConfig from the shared DB periodically.
"""

import asyncio
import logging
from pathlib import Path
from datetime import datetime, timezone
import time as _time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import select

from app.config import settings
from app.database import engine, AsyncSessionLocal, Base
from app.models import User
from app.routers import admin, auth, proxy, logs, client_keys
from app.services.auth import get_password_hash, verify_password
from app.services.system_config import load_system_config_into_settings, get_system_config_updated_at
from app.tasks.scheduler import start_background_tasks, reconcile_background_tasks

logging.basicConfig(level=logging.INFO)

app = FastAPI(title=settings.app_name)


class NodeIdHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        node_id = getattr(settings, "node_id", None)
        if node_id:
            response.headers["X-NovelAIPool-Node"] = str(node_id)
        return response


app.add_middleware(NodeIdHeaderMiddleware)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        # CSP: keep it simple. The UI uses external JS/CSS but does use inline style attributes,
        # so we allow 'unsafe-inline' for styles only.
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data: blob:; "
            "connect-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';",
        )
        return response


app.add_middleware(SecurityHeadersMiddleware)

class SystemConfigRefreshMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if settings.multi_node_enabled and getattr(settings, "system_config_refresh_enabled", True):
            interval = max(1, int(getattr(settings, "system_config_refresh_interval_seconds", 5) or 5))
            now = _time.time()
            last_check = getattr(app.state, "_cfg_last_check_ts", 0.0)
            if now - last_check >= interval:
                lock = getattr(app.state, "_cfg_lock", None)
                if lock is None:
                    lock = asyncio.Lock()
                    app.state._cfg_lock = lock
                async with lock:
                    last_check = getattr(app.state, "_cfg_last_check_ts", 0.0)
                    now = _time.time()
                    if now - last_check >= interval:
                        try:
                            async with AsyncSessionLocal() as db:
                                latest = await get_system_config_updated_at(db)
                                cached = getattr(app.state, "_cfg_last_updated_at", None)
                                if latest and (cached is None or latest > cached):
                                    app.state._cfg_last_updated_at = await load_system_config_into_settings(db)
                                    reconcile_background_tasks(asyncio.get_running_loop())
                        except Exception:
                            pass
                        app.state._cfg_last_check_ts = now

        return await call_next(request)


app.add_middleware(SystemConfigRefreshMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        ["*"]
        if settings.cors_allow_origins.strip() == "*"
        else [o.strip() for o in settings.cors_allow_origins.split(",") if o.strip()]
    ),
    allow_credentials=bool(settings.cors_allow_credentials),
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="assets")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/healthz")
async def healthz():
    return {
        "status": "ok",
        "node_id": settings.node_id,
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/readyz")
async def readyz():
    ok = True
    error = None
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        ok = False
        error = str(exc)

    payload = {
        "status": "ok" if ok else "error",
        "db": ok,
        "node_id": settings.node_id,
        "time": datetime.now(timezone.utc).isoformat(),
    }
    if error:
        payload["error"] = error[:300]
    if ok:
        return payload
    return JSONResponse(payload, status_code=503)

app.include_router(auth.router)
app.include_router(client_keys.router)
app.include_router(proxy.router)
app.include_router(logs.router)
app.include_router(admin.router)


async def _ensure_sqlite_schema() -> None:
    # Lightweight migrations for SQLite (no Alembic).
    if not str(engine.url).startswith("sqlite"):
        return
    async with engine.begin() as conn:
        rows = await conn.execute(text("PRAGMA table_info('request_logs')"))
        cols = {r[1] for r in rows.fetchall()}
        if "ip_address" not in cols:
            await conn.execute(text("ALTER TABLE request_logs ADD COLUMN ip_address VARCHAR(64)"))

        rows = await conn.execute(text("PRAGMA table_info('api_keys')"))
        cols = {r[1] for r in rows.fetchall()}
        if "cooldown_until" not in cols:
            await conn.execute(text("ALTER TABLE api_keys ADD COLUMN cooldown_until DATETIME"))


@app.on_event("startup")
async def on_startup() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await _ensure_sqlite_schema()

    async with AsyncSessionLocal() as db:
        if settings.multi_node_enabled:
            try:
                app.state._cfg_last_updated_at = await load_system_config_into_settings(db)
            except Exception:
                app.state._cfg_last_updated_at = None

        result = await db.execute(select(User).where(User.username == settings.admin_username))
        admin_user = result.scalar_one_or_none()
        if not admin_user:
            admin_user = User(
                username=settings.admin_username,
                hashed_password=get_password_hash(settings.admin_password),
                role="admin",
            )
            db.add(admin_user)
            await db.commit()
        else:
            if settings.admin_force_reset:
                admin_user.hashed_password = get_password_hash(settings.admin_password)
                admin_user.role = "admin"
                await db.commit()
            elif not verify_password(settings.admin_password, admin_user.hashed_password):
                logging.warning(
                    "Admin password mismatch. Set ADMIN_FORCE_RESET=true to reset."
                )

    loop = asyncio.get_event_loop()
    start_background_tasks(loop)
