from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Optional

from app.config import settings
import httpx


@dataclass
class ProxyState:
    url: str
    cooldown_until: float = 0.0
    fail_streak: int = 0
    last_error: str | None = None


class UpstreamProxyPool:
    """
    Single-process upstream proxy pool for *availability*.

    Design goals:
    - Distribute traffic across a fixed set of outbound proxies owned/controlled by the operator.
    - Fail over quickly when a proxy appears unhealthy.
    - Avoid aggressive "IP rotation" behaviors; default strategy is sticky-by-user.
    """

    _states: list[ProxyState] | None = None
    _raw: str | None = None

    @classmethod
    def _load_states(cls) -> list[ProxyState]:
        raw = getattr(settings, "upstream_proxies", "") or ""
        if cls._states is not None and cls._raw == raw:
            return cls._states
        proxies = [p.strip() for p in raw.split(",") if p.strip()]
        cls._states = [ProxyState(url=p) for p in proxies]
        cls._raw = raw
        return cls._states

    @staticmethod
    def _now() -> float:
        return time.time()

    @classmethod
    def enabled(cls) -> bool:
        return bool(getattr(settings, "upstream_proxy_mode", "direct") == "proxy_pool") and bool(
            getattr(settings, "upstream_proxies", "").strip()
        )

    @staticmethod
    def mask_proxy_url(url: str) -> str:
        # Strip credentials: scheme://user:pass@host:port -> scheme://host:port
        if "@" not in url:
            return url
        try:
            scheme, rest = url.split("://", 1)
            after_at = rest.split("@", 1)[1]
            return f"{scheme}://{after_at}"
        except Exception:
            return url

    @classmethod
    def snapshot(cls) -> list[dict]:
        states = cls._load_states() if cls.enabled() else []
        now = cls._now()
        return [
            {
                "proxy": cls.mask_proxy_url(s.url),
                "is_available": s.cooldown_until <= now,
                "cooldown_seconds": max(0, int(s.cooldown_until - now)),
                "fail_streak": s.fail_streak,
                "last_error": s.last_error,
            }
            for s in states
        ]

    @classmethod
    def get_proxy_for_user(cls, user_id: int) -> Optional[str]:
        if not cls.enabled():
            return None
        states = cls._load_states()
        if not states:
            return None

        now = cls._now()
        available = [s for s in states if s.cooldown_until <= now]
        if not available:
            return None

        strategy = getattr(settings, "upstream_proxy_strategy", "sticky")
        if strategy == "sticky":
            salt = getattr(settings, "upstream_proxy_sticky_salt", "")
            digest = hashlib.sha256(f"{user_id}:{salt}".encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], "big") % len(available)
            return available[idx].url

        # Fallback: deterministic but non-sticky (still avoids time-based rotation).
        digest = hashlib.sha256(str(user_id).encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], "big") % len(available)
        return available[idx].url

    @classmethod
    def report_result(cls, proxy_url: str | None, status_code: int | None = None, error: str | None = None) -> None:
        if not cls.enabled() or not proxy_url:
            return
        states = cls._load_states()
        state = next((s for s in states if s.url == proxy_url), None)
        if not state:
            return

        # Successful response
        if status_code is not None and status_code < 500 and status_code not in (429,):
            state.fail_streak = 0
            state.last_error = None
            return

        # Decide whether to treat this signal as proxy failure.
        if status_code == 429 and not settings.upstream_proxy_handle_429:
            return
        if status_code is not None and status_code >= 500 and not settings.upstream_proxy_handle_5xx:
            return
        if status_code is None and not settings.upstream_proxy_handle_network_errors:
            return

        # Failures & upstream overload
        state.fail_streak = min(state.fail_streak + 1, settings.upstream_proxy_fail_streak_cap)
        state.last_error = error or (f"HTTP {status_code}" if status_code is not None else "unknown error")

        if state.fail_streak < max(1, settings.upstream_proxy_failure_threshold):
            return

        if status_code == 429:
            base = settings.upstream_proxy_cooldown_429_seconds
        elif status_code is not None and status_code >= 500:
            base = settings.upstream_proxy_cooldown_5xx_seconds
        elif status_code is None:
            base = settings.upstream_proxy_cooldown_error_seconds
        else:
            base = settings.upstream_proxy_cooldown_seconds

        max_cd = settings.upstream_proxy_max_cooldown_seconds
        cooldown = min(base * (2 ** (state.fail_streak - 1)), max_cd)
        state.cooldown_until = max(state.cooldown_until, cls._now() + cooldown)

    @classmethod
    async def keepalive_probe_once(cls, proxy_url: str) -> None:
        """
        Best-effort probe for availability: make a lightweight request through the proxy.
        This is for operator-controlled proxies to detect broken routes early.
        """
        url = getattr(settings, "upstream_proxy_keepalive_url", "https://api.novelai.net/") or "https://api.novelai.net/"
        timeout_s = float(getattr(settings, "upstream_proxy_keepalive_timeout_seconds", 8))
        try:
            async with httpx.AsyncClient(timeout=timeout_s, proxy=proxy_url) as client:
                resp = await client.get(url)
            cls.report_result(proxy_url, status_code=resp.status_code)
        except Exception as exc:
            cls.report_result(proxy_url, status_code=None, error=str(exc))

    @classmethod
    async def keepalive_probe_all(cls) -> None:
        if not cls.enabled():
            return
        states = cls._load_states()
        for s in states:
            await cls.keepalive_probe_once(s.url)
