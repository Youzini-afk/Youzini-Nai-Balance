import time
from datetime import datetime, timedelta
from typing import Mapping
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

import httpx

from app.config import settings
from app.database import get_db
from app.models import ApiKey, RequestLog, User
from sqlalchemy import select, func
from app.services.auth import get_current_user_any
from app.services.key_pool import select_healthy_key
from app.services.rate_limit import enforce_rate_limit
from app.services.upstream_proxy_pool import UpstreamProxyPool

router = APIRouter(prefix="/v1/novelai", tags=["proxy"])

def _parse_retry_after(headers: Mapping[str, str] | None) -> int | None:
    if not headers:
        return None
    value = headers.get("retry-after") or headers.get("Retry-After")
    if not value:
        return None
    value = value.strip()
    try:
        seconds = int(value)
        return max(0, seconds)
    except ValueError:
        # HTTP-date format is allowed by spec, but we keep it simple (treat as unknown).
        return None


def _set_key_cooldown(key: ApiKey, seconds: int) -> None:
    if seconds <= 0:
        return
    until = datetime.utcnow() + timedelta(seconds=seconds)
    if key.cooldown_until is None or key.cooldown_until < until:
        key.cooldown_until = until


def _compute_backoff(base_seconds: int, fail_streak: int, max_seconds: int) -> int:
    # Exponential backoff: base * 2^(fail_streak-1), capped.
    if base_seconds <= 0:
        return 0
    streak = max(1, int(fail_streak or 1))
    factor = 2 ** min(streak - 1, 4)
    seconds = base_seconds * factor
    return min(seconds, max_seconds) if max_seconds > 0 else seconds


def _update_key_from_upstream(
    key: ApiKey, status_code: int, message: str | None, headers: Mapping[str, str] | None = None
) -> None:
    """
    Update key health hints from upstream results.
    - 401: key invalid (revoked/expired)
    - 403: treated as invalid (forbidden/banned)
    - 402: treated as unhealthy (quota/anlas/subscription problem)
    - 409/429: transient (concurrency/rate-limit), keep status but record error and streak
    - 5xx/502/504: transient, increase streak; mark unhealthy if persistent
    """
    msg = message or ""
    key.last_error = f"{status_code}: {msg}"[:1000] if msg else f"{status_code}"

    if status_code in (401, 403):
        key.status = "invalid"
        key.fail_streak += 1
        return

    if status_code == 402:
        key.fail_streak += 1
        if settings.dynamic_cooldown_enabled:
            _set_key_cooldown(
                key,
                _compute_backoff(
                    settings.cooldown_402_base_seconds,
                    key.fail_streak,
                    settings.cooldown_max_seconds,
                ),
            )
        if key.fail_streak >= settings.health_check_fail_threshold:
            key.status = "unhealthy"
        return

    if status_code in (409, 429):
        # Likely concurrency/rate-limit; avoid quickly kicking the key out of the pool.
        key.fail_streak = min(key.fail_streak + 1, settings.health_check_fail_threshold)
        if settings.dynamic_cooldown_enabled:
            base = settings.cooldown_429_base_seconds if status_code == 429 else settings.cooldown_409_base_seconds
            cooldown = _compute_backoff(base, key.fail_streak, settings.cooldown_max_seconds)
            if status_code == 429:
                retry_after = _parse_retry_after(headers)
                if retry_after is not None:
                    cooldown = max(cooldown, retry_after)
            _set_key_cooldown(key, cooldown)
        return

    if status_code >= 500 or status_code in (502, 504):
        key.fail_streak += 1
        if settings.dynamic_cooldown_enabled:
            _set_key_cooldown(
                key,
                _compute_backoff(
                    settings.cooldown_5xx_base_seconds,
                    key.fail_streak,
                    settings.cooldown_max_seconds,
                ),
            )
        if key.fail_streak >= settings.health_check_fail_threshold:
            key.status = "unhealthy"
        return

    # Other 4xx: treat as transient/unknown; track streak and only mark unhealthy after threshold.
    if status_code >= 400:
        key.fail_streak += 1
        if settings.dynamic_cooldown_enabled:
            # For unknown 4xx, apply a small backoff to reduce repeated failures.
            _set_key_cooldown(
                key,
                _compute_backoff(
                    settings.cooldown_409_base_seconds,
                    key.fail_streak,
                    settings.cooldown_max_seconds,
                ),
            )
        if key.fail_streak >= settings.health_check_fail_threshold:
            key.status = "unhealthy"


def _validate_opus_limits(payload: dict) -> tuple[int, int, int, int]:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    required_fields = ("width", "height", "steps", "n_samples")
    for field in required_fields:
        if field not in payload:
            raise HTTPException(status_code=400, detail=f"Missing field: {field}")
    try:
        width = int(payload["width"])
        height = int(payload["height"])
        steps = int(payload["steps"])
        n_samples = int(payload["n_samples"])
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid numeric fields")

    if width <= 0 or height <= 0:
        raise HTTPException(status_code=400, detail="Width/height must be > 0")
    if steps <= 0:
        raise HTTPException(status_code=400, detail="Steps must be > 0")
    if width * height > settings.opus_max_pixels:
        raise HTTPException(status_code=400, detail="Pixel limit exceeded")
    if steps > settings.opus_max_steps:
        raise HTTPException(status_code=400, detail="Steps limit exceeded")
    if n_samples != settings.opus_max_samples:
        raise HTTPException(status_code=400, detail="n_samples must be 1")
    return width, height, steps, n_samples


@router.get("/models")
async def list_models(user: User = Depends(get_current_user_any)):
    models = [m.strip() for m in settings.novelai_models.split(",") if m.strip()]
    return {"models": models}


@router.post("/generate-image")
async def generate_image(
    request: Request,
    user: User = Depends(get_current_user_any),
    db: AsyncSession = Depends(get_db),
):
    try:
        await enforce_rate_limit(db, user)
    except PermissionError as exc:
        log = RequestLog(
            user_id=user.id,
            status="rejected",
            status_code=429,
            reject_reason=str(exc),
        )
        db.add(log)
        await db.commit()
        raise HTTPException(status_code=429, detail=str(exc))

    try:
        payload = await request.json()
    except Exception:
        log = RequestLog(
            user_id=user.id,
            status="rejected",
            status_code=400,
            reject_reason="Invalid JSON body",
        )
        db.add(log)
        await db.commit()
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    if isinstance(payload, dict) and "model" not in payload:
        payload["model"] = settings.novelai_default_model
    if isinstance(payload, dict):
        allowed_models = {m.strip() for m in settings.novelai_models.split(",") if m.strip()}
        model = payload.get("model")
        if allowed_models and model not in allowed_models:
            log = RequestLog(
                user_id=user.id,
                status="rejected",
                status_code=400,
                reject_reason=f"不支持的模型: {model}",
            )
            db.add(log)
            await db.commit()
            raise HTTPException(status_code=400, detail=f"不支持的模型: {model}")
    try:
        width, height, steps, samples = _validate_opus_limits(payload)
    except HTTPException as exc:
        log = RequestLog(
            user_id=user.id,
            width=payload.get("width") if isinstance(payload, dict) else None,
            height=payload.get("height") if isinstance(payload, dict) else None,
            steps=payload.get("steps") if isinstance(payload, dict) else None,
            samples=payload.get("n_samples") if isinstance(payload, dict) else None,
            status="rejected",
            status_code=exc.status_code,
            reject_reason=str(exc.detail),
        )
        db.add(log)
        await db.commit()
        raise

    selected = await select_healthy_key(db)
    if not selected:
        raise HTTPException(status_code=503, detail="No healthy keys available")
    key, raw_key = selected
    upstream_proxy = UpstreamProxyPool.get_proxy_for_user(user.id)

    start = time.time()
    status = "success"
    status_code = 200
    reject_reason = None

    try:
        headers = {"Authorization": f"Bearer {raw_key}"}
        async with httpx.AsyncClient(timeout=60.0, proxy=upstream_proxy) as client:
            resp = await client.post(
                "https://image.novelai.net/ai/generate-image",
                headers=headers,
                json=payload,
            )
        status_code = resp.status_code
        if resp.status_code >= 400:
            status = "failed"
            try:
                content_type = resp.headers.get("content-type", "")
                if "application/json" in content_type:
                    data = resp.json()
                    if isinstance(data, dict):
                        reject_reason = (
                            data.get("message")
                            or data.get("detail")
                            or data.get("error")
                            or str(data)[:200]
                        )
                    else:
                        reject_reason = str(data)[:200]
                else:
                    reject_reason = resp.text[:200]
            except Exception:
                reject_reason = f"HTTP {resp.status_code}"
        content_type = resp.headers.get("content-type", "application/json")
        if "application/json" in content_type:
            response = JSONResponse(content=resp.json(), status_code=resp.status_code)
        else:
            response = Response(
                content=resp.content,
                status_code=resp.status_code,
                media_type=content_type,
            )
    except httpx.HTTPError as exc:
        status = "failed"
        status_code = 502
        reject_reason = str(exc)
        response = JSONResponse(status_code=502, content={"detail": "Upstream error"})
        UpstreamProxyPool.report_result(upstream_proxy, status_code=None, error=str(exc))

    latency = (time.time() - start) * 1000
    key.total_requests += 1
    key.last_used_at = datetime.utcnow()
    if status == "success":
        key.success_requests += 1
        key.fail_streak = 0
        key.last_error = None
        key.cooldown_until = None
        UpstreamProxyPool.report_result(upstream_proxy, status_code=status_code)
    else:
        key.fail_requests += 1
        _update_key_from_upstream(key, status_code, reject_reason, resp.headers if "resp" in locals() else None)
        UpstreamProxyPool.report_result(upstream_proxy, status_code=status_code, error=reject_reason)

    log = RequestLog(
        user_id=user.id,
        api_key_id=key.id,
        width=width,
        height=height,
        steps=steps,
        samples=samples,
        status=status,
        status_code=status_code,
        latency_ms=latency,
        reject_reason=reject_reason,
    )
    db.add(log)
    await db.commit()

    return response
