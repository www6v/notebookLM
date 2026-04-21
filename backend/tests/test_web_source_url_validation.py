"""Tests for web source URL validation."""

import pytest

from app.commons.url_validation import validate_web_source_url


def test_validate_web_source_url_accepts_http_https() -> None:
    assert (
        validate_web_source_url("https://example.com/path?q=1")
        == "https://example.com/path?q=1"
    )
    assert validate_web_source_url("  http://a.co/  ") == "http://a.co/"


@pytest.mark.parametrize(
    "raw",
    [
        None,
        "",
        "   ",
        "ftp://example.com/",
        "https://",
        "not-a-url",
        "javascript:alert(1)",
        "http:///no-host",
    ],
)
def test_validate_web_source_url_rejects_invalid(raw: str | None) -> None:
    with pytest.raises(ValueError):
        validate_web_source_url(raw)
