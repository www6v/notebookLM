"""Per-user UTC daily quotas in Redis (free-tier generation caps)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from redis import asyncio as redis_asyncio

# ARGV: cap (int), ttl seconds (int)
_RESERVE_DAILY_COUNT_LUA = """
local cap = tonumber(ARGV[1])
local ttl = tonumber(ARGV[2])
if not cap or cap < 1 then
  return 1
end
local n = redis.call('INCR', KEYS[1])
if n == 1 then
  redis.call('EXPIRE', KEYS[1], ttl)
end
if n > cap then
  redis.call('DECR', KEYS[1])
  return 0
end
return 1
"""


def utc_calendar_date_str() -> str:
    """Current UTC date as YYYY-MM-DD."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def seconds_until_utc_midnight() -> int:
    """Whole seconds from now until next UTC midnight, at least 1."""
    now = datetime.now(timezone.utc)
    tomorrow = (now + timedelta(days=1)).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    return max(1, int((tomorrow - now).total_seconds()))


def build_daily_slide_generation_key(user_id: str) -> str:
    """Redis key for one user's slide-generation count for the UTC day."""
    return f"genrl:daily:slide:{user_id}:{utc_calendar_date_str()}"


def build_daily_deep_research_generation_key(user_id: str) -> str:
    """Redis key for one user's deep-research starts for the UTC day."""
    return f"genrl:daily:deep-research:{user_id}:{utc_calendar_date_str()}"


async def _try_reserve_daily_count(
    redis_client: redis_asyncio.Redis,
    key: str,
    cap: int,
) -> bool:
    """Atomically increment key; return False if over ``cap``."""
    if cap < 1:
        return True
    ttl = seconds_until_utc_midnight()
    raw = await redis_client.eval(
        _RESERVE_DAILY_COUNT_LUA,
        1,
        key,
        str(cap),
        str(ttl),
    )
    return int(raw) == 1


async def try_reserve_daily_slide_generation(
    redis_client: redis_asyncio.Redis,
    user_id: str,
    cap: int,
) -> bool:
    """Atomically increment today's slide counter; return False if over ``cap``."""
    key = build_daily_slide_generation_key(user_id)
    return await _try_reserve_daily_count(redis_client, key, cap)


async def release_daily_slide_generation(
    redis_client: redis_asyncio.Redis,
    user_id: str,
) -> None:
    """Undo one slide reservation (e.g. after DB commit failure)."""
    key = build_daily_slide_generation_key(user_id)
    await redis_client.decr(key)


async def try_reserve_daily_deep_research_generation(
    redis_client: redis_asyncio.Redis,
    user_id: str,
    cap: int,
) -> bool:
    """Atomically increment today's deep-research counter."""
    key = build_daily_deep_research_generation_key(user_id)
    return await _try_reserve_daily_count(redis_client, key, cap)


async def release_daily_deep_research_generation(
    redis_client: redis_asyncio.Redis,
    user_id: str,
) -> None:
    """Undo one deep-research reservation (e.g. after DB commit failure)."""
    key = build_daily_deep_research_generation_key(user_id)
    await redis_client.decr(key)
