"""Redis client for generation cooldown keys."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from redis import asyncio as redis_asyncio

from notebooklm_shared.config import settings


def resolve_generation_rate_limit_redis_url() -> str:
    """URL for cooldown keys; isolated DB index optional via env."""
    return (
        settings.generation_rate_limit_redis_url
        or settings.cache_redis_url
        or settings.redis_url
    )


def get_generation_rate_limit_redis() -> redis_asyncio.Redis:
    """New async Redis client (caller must aclose, or use context manager)."""
    return redis_asyncio.from_url(
        resolve_generation_rate_limit_redis_url(),
        encoding="utf-8",
        decode_responses=True,
    )


@asynccontextmanager
async def generation_rate_limit_redis_cm() -> AsyncGenerator[redis_asyncio.Redis, None]:
    """Async context manager closing the client on exit."""
    client = get_generation_rate_limit_redis()
    try:
        yield client
    finally:
        await client.aclose()
