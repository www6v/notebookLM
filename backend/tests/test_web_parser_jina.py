"""Tests for Jina Reader web markdown fetch."""

import asyncio
from types import SimpleNamespace

import pytest

from app.parsers.web_parser import (
    build_jina_reader_url,
    fetch_web_markdown_via_jina,
    parse_web_page,
)


def test_build_jina_reader_url() -> None:
    assert (
        build_jina_reader_url("https://example.com/foo")
        == "https://r.jinaai.cn/https://example.com/foo"
    )


def test_fetch_web_markdown_via_jina_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        text = "  # Title\n"

        def raise_for_status(self) -> None:
            return None

    class FakeClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self) -> "FakeClient":
            return self

        async def __aexit__(self, *args) -> None:
            return None

        async def get(self, url: str, follow_redirects: bool = True) -> FakeResponse:
            assert url == "https://r.jinaai.cn/https://example.com/p"
            assert follow_redirects is True
            return FakeResponse()

    monkeypatch.setattr(
        "app.parsers.web_parser.httpx.AsyncClient",
        FakeClient,
    )

    async def _run() -> str:
        return await fetch_web_markdown_via_jina("https://example.com/p")

    out = asyncio.run(_run())
    assert out == "# Title"


def test_parse_web_page_delegates_to_jina(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_fetch(u: str) -> str:
        return f"ok:{u}"

    monkeypatch.setattr(
        "app.parsers.web_parser.fetch_web_markdown_via_jina",
        fake_fetch,
    )

    async def _run() -> str:
        return await parse_web_page("https://z.com/")

    assert asyncio.run(_run()) == "ok:https://z.com/"


def test_finalize_url_source_web_sets_raw_content_and_processes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unittest.mock import AsyncMock

    from app.services.source import source_service

    calls: dict = {}

    async def fake_fetch(u: str) -> str:
        calls["fetch_url"] = u
        return "# Markdown body"

    async def fake_process(db, source_id: str) -> None:
        calls["process_id"] = source_id

    monkeypatch.setattr(
        "app.services.source.source_service.fetch_web_markdown_via_jina",
        fake_fetch,
    )
    monkeypatch.setattr(
        "app.services.source.source_service.process_source",
        fake_process,
    )

    db = AsyncMock()
    source = SimpleNamespace(
        id="src-web-1",
        type="web",
        original_url="https://example.com/page",
        raw_content=None,
        status="pending",
    )

    async def _run() -> None:
        await source_service.finalize_url_source(db, source)

    asyncio.run(_run())

    assert source.raw_content == "# Markdown body"
    assert calls["fetch_url"] == "https://example.com/page"
    assert calls["process_id"] == "src-web-1"
    assert db.flush.await_count >= 1
