"""Facade: concurrent cap + cooldown before starting a generation."""

from __future__ import annotations

from redis import asyncio as redis_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from notebooklm_shared.config import settings
from app.limits import ROLE_LIMITS
from app.ratelimit.concurrent import count_inflight_generations
from app.ratelimit.cooldown import acquire_cooldown_keys, pttl_seconds
from app.ratelimit.daily_quota import (
    release_daily_deep_research_generation,
    release_daily_slide_generation,
    try_reserve_daily_deep_research_generation,
    try_reserve_daily_slide_generation,
)
from app.ratelimit.errors import GenerationRateLimited
from app.ratelimit.keys import build_cooldown_keys
from app.ratelimit.kinds import GenerationKind


async def assert_generation_allowed(
    db: AsyncSession,
    redis_client: redis_asyncio.Redis,
    *,
    user_id: str,
    kind: GenerationKind,
    notebook_id: str,
    source_ids: list[str] | None,
    artifact_id: str | None,
    user_role: str | None = None,
    cooldown_seconds: int | None = None,
    max_concurrent: int | None = None,
) -> tuple[list[str], bool, bool]:
    """Raise GenerationRateLimited if blocked.

    Returns cooldown keys and flags for free-tier daily reservations
    (slide / deep research); caller must release matching flags on DB failure.
    """
    cooldown = (
        cooldown_seconds
        if cooldown_seconds is not None
        else settings.generation_cooldown_seconds
    )
    max_c = (
        max_concurrent
        if max_concurrent is not None
        else settings.generation_max_concurrent
    )

    inflight = await count_inflight_generations(db, user_id)
    if inflight >= max_c:
        raise GenerationRateLimited(
            code="concurrent_limit",
            message=(
                f"同时进行的生成任务已达上限（最多 {max_c} 个），请稍后再试。"
            ),
        )

    daily_slide_reserved = False
    daily_deep_research_reserved = False
    tier_role = user_role if user_role is not None else "free"
    tier_limits = ROLE_LIMITS.get(tier_role, ROLE_LIMITS["free"])

    if kind == GenerationKind.SLIDE_DECK:
        slide_cap = tier_limits.get("max_daily_slide_generations")
        if slide_cap is not None:
            reserved = await try_reserve_daily_slide_generation(
                redis_client,
                user_id,
                slide_cap,
            )
            if not reserved:
                raise GenerationRateLimited(
                    code="daily_slide_limit",
                    message=(
                        f"免费用户每日最多生成 {slide_cap} 次幻灯片，"
                        "请明日再试或升级账户。"
                    ),
                )
            daily_slide_reserved = True

    if kind == GenerationKind.DEEP_RESEARCH:
        dr_cap = tier_limits.get("max_daily_deep_research_generations")
        if dr_cap is not None:
            reserved = await try_reserve_daily_deep_research_generation(
                redis_client,
                user_id,
                dr_cap,
            )
            if not reserved:
                raise GenerationRateLimited(
                    code="daily_deep_research_limit",
                    message=(
                        f"免费用户每日最多发起 {dr_cap} 次深度研究，"
                        "请明日再试或升级账户。"
                    ),
                )
            daily_deep_research_reserved = True

    keys = build_cooldown_keys(
        user_id,
        kind,
        notebook_id,
        source_ids,
        artifact_id,
    )
    result = await acquire_cooldown_keys(redis_client, keys, cooldown)
    if not result.ok:
        if daily_slide_reserved:
            await release_daily_slide_generation(redis_client, user_id)
        if daily_deep_research_reserved:
            await release_daily_deep_research_generation(redis_client, user_id)
        retry_after = None
        if result.blocking_key:
            retry_after = await pttl_seconds(redis_client, result.blocking_key)
        raise GenerationRateLimited(
            code="cooldown",
            message="同一来源同类生成过于频繁，请稍后再试。",
            retry_after_seconds=retry_after,
        )
    return keys, daily_slide_reserved, daily_deep_research_reserved
