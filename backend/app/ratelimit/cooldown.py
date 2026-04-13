"""Redis SET NX EX for cooldown keys; atomic multi-key acquire with rollback."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redis import asyncio as redis_asyncio

logger = logging.getLogger(__name__)

# KEYS[1..n] = cooldown keys, ARGV[1] = TTL seconds
_ACQUIRE_LUA = """
local ttl = tonumber(ARGV[1])
if not ttl or ttl < 1 then
  ttl = 1
end
for i = 1, #KEYS do
  local ok = redis.call('SET', KEYS[i], '1', 'NX', 'EX', ttl)
  if not ok then
    for j = 1, i - 1 do
      redis.call('DEL', KEYS[j])
    end
    return {0, i}
  end
end
return {1, 0}
"""


class CooldownAcquireResult:
    """Outcome of trying to acquire all cooldown keys."""

    __slots__ = ("ok", "failed_index", "blocking_key")

    def __init__(
        self,
        ok: bool,
        failed_index: int = 0,
        blocking_key: str | None = None,
    ) -> None:
        self.ok = ok
        self.failed_index = failed_index
        self.blocking_key = blocking_key


async def acquire_cooldown_keys(
    redis_client: redis_asyncio.Redis,
    keys: list[str],
    ttl_seconds: int,
) -> CooldownAcquireResult:
    """Atomically SET NX EX all keys, or roll back partial sets. Empty keys -> ok."""
    if not keys:
        return CooldownAcquireResult(True)
    if ttl_seconds < 1:
        logger.warning("Cooldown TTL %s invalid, using 1", ttl_seconds)
        ttl_seconds = 1
    raw = await redis_client.eval(_ACQUIRE_LUA, len(keys), *keys, ttl_seconds)
    if not isinstance(raw, (list, tuple)) or len(raw) < 2:
        return CooldownAcquireResult(False, 1, keys[0] if keys else None)
    ok_flag = int(raw[0]) == 1
    failed_at = int(raw[1])
    if ok_flag:
        return CooldownAcquireResult(True)
    blocking = keys[failed_at - 1] if 0 < failed_at <= len(keys) else keys[0]
    return CooldownAcquireResult(False, failed_at, blocking)


async def release_cooldown_keys(
    redis_client: redis_asyncio.Redis,
    keys: list[str],
) -> None:
    """Delete keys (e.g. after DB failure post-acquire)."""
    if not keys:
        return
    await redis_client.delete(*keys)


async def pttl_seconds(
    redis_client: redis_asyncio.Redis,
    key: str,
) -> int | None:
    """Return remaining TTL in whole seconds, or None if key missing / no TTL."""
    ms = await redis_client.pttl(key)
    if ms is None or ms < 0:
        return None
    return max(1, (ms + 999) // 1000)
