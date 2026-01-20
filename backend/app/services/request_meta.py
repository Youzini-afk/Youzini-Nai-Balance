"""
Request metadata helpers.

Keep all request-derived metadata logic (e.g. client IP) in one place.
"""

from __future__ import annotations

from fastapi import Request

from app.config import settings


def get_client_ip(request: Request) -> str | None:
    """
    Best-effort client IP.
    Only trust proxy headers when TRUST_PROXY_HEADERS=true.
    """
    if settings.trust_proxy_headers:
        x_real_ip = request.headers.get("x-real-ip")
        if x_real_ip:
            return x_real_ip.strip()[:64]
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()[:64]
    if request.client and request.client.host:
        return str(request.client.host)[:64]
    return None
