"""Unit tests for Studio generation rate limit helpers."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.ratelimit.cooldown import acquire_cooldown_keys
from app.ratelimit.daily_quota import (
    build_daily_deep_research_generation_key,
    build_daily_slide_generation_key,
)
from app.ratelimit.keys import build_cooldown_keys
from app.ratelimit.kinds import GenerationKind


def test_build_keys_artifact_overrides_sources() -> None:
    keys = build_cooldown_keys(
        "u1",
        GenerationKind.REPORT,
        "nb1",
        source_ids=["a", "b"],
        artifact_id="art1",
    )
    assert len(keys) == 1
    assert keys[0].endswith(":artifact:art1")


def test_build_keys_sources_deduped_sorted() -> None:
    keys = build_cooldown_keys(
        "u1",
        GenerationKind.REPORT,
        "nb1",
        source_ids=["b", "a", "b"],
        artifact_id=None,
    )
    assert keys == [
        "genrl:cooldown:u1:report:source:a",
        "genrl:cooldown:u1:report:source:b",
    ]


def test_build_keys_notebook_when_no_sources() -> None:
    keys = build_cooldown_keys(
        "u1",
        GenerationKind.MINDMAP,
        "nb9",
        source_ids=None,
        artifact_id=None,
    )
    assert keys == ["genrl:cooldown:u1:mindmap:notebook:nb9"]


def test_build_keys_notebook_when_empty_source_list() -> None:
    keys = build_cooldown_keys(
        "u1",
        GenerationKind.PODCAST,
        "nb1",
        source_ids=[],
        artifact_id=None,
    )
    assert keys == ["genrl:cooldown:u1:podcast:notebook:nb1"]


def test_daily_slide_key_includes_user_and_date() -> None:
    key = build_daily_slide_generation_key("user-uuid-1")
    assert key.startswith("genrl:daily:slide:user-uuid-1:")
    suffix = key.split(":")[-1]
    assert len(suffix) == 10
    assert suffix[4] == "-"
    assert suffix[7] == "-"


def test_daily_deep_research_key_includes_user_and_date() -> None:
    key = build_daily_deep_research_generation_key("user-uuid-1")
    assert key.startswith("genrl:daily:deep-research:user-uuid-1:")
    suffix = key.split(":")[-1]
    assert len(suffix) == 10


def test_build_keys_notebook_when_only_blank_sources() -> None:
    keys = build_cooldown_keys(
        "u1",
        GenerationKind.INFOGRAPHIC,
        "nb1",
        source_ids=["", "  "],
        artifact_id=None,
    )
    assert keys == ["genrl:cooldown:u1:infographic:notebook:nb1"]


@pytest.mark.asyncio
async def test_acquire_cooldown_keys_success() -> None:
    redis_client = AsyncMock()
    redis_client.eval = AsyncMock(return_value=[1, 0])
    result = await acquire_cooldown_keys(redis_client, ["k1", "k2"], 300)
    assert result.ok
    redis_client.eval.assert_awaited()


@pytest.mark.asyncio
async def test_acquire_cooldown_keys_blocked() -> None:
    redis_client = AsyncMock()
    redis_client.eval = AsyncMock(return_value=[0, 2])
    result = await acquire_cooldown_keys(
        redis_client,
        ["k1", "k2", "k3"],
        300,
    )
    assert not result.ok
    assert result.blocking_key == "k2"
