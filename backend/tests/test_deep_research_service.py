"""Tests for Deep Research service orchestration."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.services.infra import deep_research_service as drs


class _FakeResult:
    def __init__(self, obj):
        self._obj = obj

    def scalar_one_or_none(self):
        return self._obj


class _FakeSession:
    """Minimal async session stub: same row object for all selects."""

    def __init__(self, row):
        self._row = row

    async def execute(self, _stmt):
        return _FakeResult(self._row)

    async def flush(self):
        return None

    async def commit(self):
        return None


class _FakeSessionContext:
    def __init__(self, session: _FakeSession):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        return None


def _patch_async_session(row):
    session = _FakeSession(row)

    def _factory():
        return _FakeSessionContext(session)

    return session, _factory


@pytest.mark.asyncio
async def test_wall_clock_timeout_sets_error_on_report() -> None:
    row = SimpleNamespace(
        id="rep-1",
        query="topic",
        status="pending",
        error_message=None,
        content=None,
        source_count=0,
        popular_count=0,
    )
    _, session_factory = _patch_async_session(row)

    async def _slow(*_a, **_k):
        await asyncio.sleep(1.0)
        return ("", 0, 0)

    with patch.object(drs, "async_session", session_factory):
        with patch.object(drs, "DEEP_RESEARCH_WALL_CLOCK_TIMEOUT_SEC", 0.05):
            with patch.object(drs, "run_deep_research", side_effect=_slow):
                await drs.run_deep_research_for_report("rep-1")
    assert row.status == drs.ERROR
    assert row.error_message == drs.TIMEOUT_ERROR_MESSAGE


@pytest.mark.asyncio
async def test_success_skips_ready_when_report_already_error() -> None:
    row = SimpleNamespace(
        id="rep-2",
        query="topic",
        status="pending",
        error_message=None,
        content=None,
        source_count=0,
        popular_count=0,
    )
    _, session_factory = _patch_async_session(row)

    async def deer(*_a, **_k):
        row.status = drs.ERROR
        row.error_message = "任务已取消。"
        return ("should-not-persist", 9, 9)

    with patch.object(drs, "async_session", session_factory):
        with patch.object(drs, "run_deep_research", side_effect=deer):
            out = await drs.run_deep_research_for_report("rep-2")
    assert out is not None
    assert out.status == drs.ERROR
    assert row.content is None or row.content != "should-not-persist"
