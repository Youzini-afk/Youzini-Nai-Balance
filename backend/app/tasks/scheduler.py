"""
Background loops scheduler.

This module owns the lifecycle of long-running background tasks (health checks, proxy keepalive).
It supports toggling tasks on/off at runtime (reconcile) and multi-node leader-only gating.
"""

import asyncio
import logging

from app.config import settings
from app.database import AsyncSessionLocal
from app.services.health_check import check_all_keys
from app.services.upstream_proxy_pool import UpstreamProxyPool

log = logging.getLogger(__name__)

_TASKS: dict[str, asyncio.Task] = {}


def _should_run_health_check() -> bool:
    if not settings.health_check_enabled:
        return False
    if (
        settings.multi_node_enabled
        and settings.health_check_leader_only
        and settings.node_id != settings.health_check_leader_node_id
    ):
        log.info(
            "Skip health check loop on node %s (leader-only enabled; leader=%s)",
            settings.node_id,
            settings.health_check_leader_node_id,
        )
        return False
    return True


def _should_run_upstream_proxy_keepalive() -> bool:
    if not settings.upstream_proxy_keepalive_enabled:
        return False
    if (
        settings.multi_node_enabled
        and
        settings.upstream_proxy_keepalive_leader_only
        and settings.node_id != settings.upstream_proxy_keepalive_leader_node_id
    ):
        log.info(
            "Skip upstream proxy keepalive on node %s (leader-only enabled; leader=%s)",
            settings.node_id,
            settings.upstream_proxy_keepalive_leader_node_id,
        )
        return False
    return True


async def health_check_loop() -> None:
    if not _should_run_health_check():
        return
    while True:
        try:
            async with AsyncSessionLocal() as db:
                total = await check_all_keys(db)
                log.info("Health check completed for %s keys", total)
        except Exception as exc:
            log.warning("Health check failed: %s", exc)
        try:
            await asyncio.sleep(settings.health_check_interval_seconds)
        except asyncio.CancelledError:
            return

async def upstream_proxy_keepalive_loop() -> None:
    if not _should_run_upstream_proxy_keepalive():
        return
    while True:
        try:
            await UpstreamProxyPool.keepalive_probe_all()
        except Exception as exc:
            log.warning("Upstream proxy keepalive failed: %s", exc)
        try:
            await asyncio.sleep(settings.upstream_proxy_keepalive_interval_seconds)
        except asyncio.CancelledError:
            return


def reconcile_background_tasks(loop: asyncio.AbstractEventLoop) -> None:
    desired = {
        "health_check": _should_run_health_check(),
        "upstream_proxy_keepalive": _should_run_upstream_proxy_keepalive(),
    }

    for name, should_run in desired.items():
        task = _TASKS.get(name)
        task_alive = task is not None and not task.done()
        if should_run and not task_alive:
            if name == "health_check":
                _TASKS[name] = loop.create_task(health_check_loop())
            elif name == "upstream_proxy_keepalive":
                _TASKS[name] = loop.create_task(upstream_proxy_keepalive_loop())
        if not should_run and task_alive:
            task.cancel()
            _TASKS.pop(name, None)


def start_background_tasks(loop: asyncio.AbstractEventLoop) -> None:
    reconcile_background_tasks(loop)
