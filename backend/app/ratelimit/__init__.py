"""Studio generation rate limiting (concurrent DB cap + Redis cooldown)."""

from __future__ import annotations

from typing import TYPE_CHECKING

__all__ = [
    "GenerationKind",
    "GenerationRateLimited",
    "acquire_generation_rate_limit_slot",
    "assert_generation_allowed",
    "release_generation_rate_limit_on_db_failure",
    "build_cooldown_keys",
    "count_inflight_generations",
    "generation_rate_limit_redis_cm",
    "get_generation_rate_limit_redis",
    "http_exception_from_generation",
    "release_cooldown_keys",
    "resolve_generation_rate_limit_redis_url",
]

if TYPE_CHECKING:
    from app.ratelimit.errors import GenerationRateLimited
    from app.ratelimit.integration import acquire_generation_rate_limit_slot
    from app.ratelimit.kinds import GenerationKind
    from app.ratelimit.policy import assert_generation_allowed


def __getattr__(name: str):
    if name == "GenerationKind":
        from app.ratelimit.kinds import GenerationKind as _v

        return _v
    if name == "GenerationRateLimited":
        from app.ratelimit.errors import GenerationRateLimited as _v

        return _v
    if name == "http_exception_from_generation":
        from app.ratelimit.errors import http_exception_from_generation as _v

        return _v
    if name == "assert_generation_allowed":
        from app.ratelimit.policy import assert_generation_allowed as _v

        return _v
    if name == "build_cooldown_keys":
        from app.ratelimit.keys import build_cooldown_keys as _v

        return _v
    if name == "count_inflight_generations":
        from app.ratelimit.concurrent import count_inflight_generations as _v

        return _v
    if name == "generation_rate_limit_redis_cm":
        from app.ratelimit.redis_client import generation_rate_limit_redis_cm as _v

        return _v
    if name == "get_generation_rate_limit_redis":
        from app.ratelimit.redis_client import get_generation_rate_limit_redis as _v

        return _v
    if name == "resolve_generation_rate_limit_redis_url":
        from app.ratelimit.redis_client import (
            resolve_generation_rate_limit_redis_url as _v,
        )

        return _v
    if name == "release_cooldown_keys":
        from app.ratelimit.cooldown import release_cooldown_keys as _v

        return _v
    if name == "acquire_generation_rate_limit_slot":
        from app.ratelimit.integration import acquire_generation_rate_limit_slot as _v

        return _v
    if name == "release_generation_rate_limit_on_db_failure":
        from app.ratelimit.integration import (
            release_generation_rate_limit_on_db_failure as _v,
        )

        return _v
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
