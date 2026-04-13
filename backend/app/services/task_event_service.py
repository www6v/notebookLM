"""Task event helpers backed by Redis pub/sub."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from redis import asyncio as redis_asyncio

from app.config import settings

TERMINAL_TASK_STATUSES = {"ready", "error"}
logger = logging.getLogger(__name__)


def _resolve_task_event_redis_url() -> str:
    """Resolve the Redis URL used for task status events."""
    return (
        settings.task_event_redis_url
        or settings.cache_redis_url
        or settings.redis_url
    )


def get_task_event_redis_client() -> redis_asyncio.Redis:
    """Return a Redis client for task events."""
    return redis_asyncio.from_url(
        _resolve_task_event_redis_url(),
        encoding="utf-8",
        decode_responses=True,
    )


def build_task_event_channel(resource_type: str, resource_id: str) -> str:
    """Build the pub/sub channel name for a task resource."""
    return f"{settings.task_event_channel_prefix}:{resource_type}:{resource_id}"


def build_task_event_payload(
    resource_type: str,
    resource_id: str,
    status: str,
    error_message: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a normalized task event payload."""
    payload: dict[str, Any] = {
        "resource_type": resource_type,
        "resource_id": resource_id,
        "status": status,
        "error_message": error_message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        payload.update(extra)
    return payload


async def publish_task_event(
    resource_type: str,
    resource_id: str,
    status: str,
    error_message: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Publish a task status event to Redis."""
    payload = build_task_event_payload(
        resource_type=resource_type,
        resource_id=resource_id,
        status=status,
        error_message=error_message,
        extra=extra,
    )
    redis_client = get_task_event_redis_client()
    try:
        await redis_client.publish(
            build_task_event_channel(resource_type, resource_id),
            json.dumps(payload, ensure_ascii=False),
        )
    except Exception:
        logger.warning(
            "Failed to publish task event for %s:%s",
            resource_type,
            resource_id,
            exc_info=True,
        )
    finally:
        await redis_client.aclose()


async def subscribe_task_events(resource_type: str, resource_id: str):
    """Subscribe to task events for a single resource."""
    redis_client = get_task_event_redis_client()
    pubsub = redis_client.pubsub()
    setattr(pubsub, "_task_event_redis_client", redis_client)
    await pubsub.subscribe(build_task_event_channel(resource_type, resource_id))
    return pubsub
