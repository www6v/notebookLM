"""Thin helpers for API routes: acquire slot + Redis handle lifecycle."""

from __future__ import annotations

from redis import asyncio as redis_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.ratelimit.cooldown import release_cooldown_keys
from app.ratelimit.daily_quota import (
    release_daily_deep_research_generation,
    release_daily_slide_generation,
)
from app.ratelimit.errors import GenerationRateLimited, http_exception_from_generation
from app.ratelimit.kinds import GenerationKind
from app.ratelimit.policy import assert_generation_allowed
from app.ratelimit.redis_client import get_generation_rate_limit_redis


async def acquire_generation_rate_limit_slot(
    db: AsyncSession,
    *,
    user_id: str,
    kind: GenerationKind,
    notebook_id: str,
    source_ids: list[str] | None,
    artifact_id: str | None,
    user_role: str | None = None,
) -> tuple[redis_asyncio.Redis, list[str], bool, bool]:
    """Run concurrent, optional free daily caps, and cooldown checks.

    Returns ``(redis_client, acquired_cooldown_keys, daily_slide_reserved,
    daily_deep_research_reserved)``. On DB failure, call
    :func:`release_generation_rate_limit_on_db_failure`.
    Pass ``user_role`` for correct paid/admin exemption on gated kinds.
    """
    rl_redis = get_generation_rate_limit_redis()
    try:
        acquired, daily_slide_reserved, daily_dr_reserved = (
            await assert_generation_allowed(
                db,
                rl_redis,
                user_id=user_id,
                kind=kind,
                notebook_id=notebook_id,
                source_ids=source_ids,
                artifact_id=artifact_id,
                user_role=user_role,
            )
        )
    except GenerationRateLimited as exc:
        await rl_redis.aclose()
        raise http_exception_from_generation(exc) from exc
    except Exception:
        await rl_redis.aclose()
        raise
    return rl_redis, acquired, daily_slide_reserved, daily_dr_reserved


async def release_generation_rate_limit_on_db_failure(
    redis_client: redis_asyncio.Redis,
    cooldown_keys: list[str],
    *,
    user_id: str,
    daily_slide_reserved: bool,
    daily_deep_research_reserved: bool = False,
) -> None:
    """Undo Redis reservations after a failed DB commit."""
    await release_cooldown_keys(redis_client, cooldown_keys)
    if daily_slide_reserved:
        await release_daily_slide_generation(redis_client, user_id)
    if daily_deep_research_reserved:
        await release_daily_deep_research_generation(redis_client, user_id)
