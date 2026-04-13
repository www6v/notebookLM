"""Readiness and dependency probes for production traffic management."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from sqlalchemy import text

from app.ai.milvus_client import ensure_connected
from app.config import settings
from app.database import async_session
from app.services.task_event_service import get_task_event_redis_client


async def probe_database() -> dict[str, Any]:
    """Check whether the primary database is reachable."""
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        return {"ok": True}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


async def probe_redis() -> dict[str, Any]:
    """Check whether Redis is reachable."""
    redis_client = get_task_event_redis_client()
    try:
        pong = await redis_client.ping()
        return {"ok": bool(pong)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
    finally:
        await redis_client.aclose()


async def probe_milvus() -> dict[str, Any]:
    """Check whether Milvus is reachable."""
    try:
        await asyncio.to_thread(ensure_connected)
        return {"ok": True}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


async def probe_deer_flow() -> dict[str, Any]:
    """Check whether DeerFlow is reachable."""
    try:
        timeout = settings.healthcheck_timeout_seconds
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(settings.deer_flow_base_url)
        return {"ok": response.status_code < 500, "status_code": response.status_code}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


async def collect_dependency_status() -> dict[str, Any]:
    """Return a dependency status summary for liveness and readiness probes."""
    checks = {
        "database": probe_database(),
        "redis": probe_redis(),
        "milvus": probe_milvus(),
    }
    if settings.readiness_include_external_dependencies:
        checks["deer_flow"] = probe_deer_flow()

    results = {
        name: result
        for name, result in zip(
            checks.keys(),
            await asyncio.gather(*checks.values()),
        )
    }
    ready = all(result.get("ok") for result in results.values())
    return {"ready": ready, "checks": results}
