"""HTTP(S) URL validation for web sources."""

from urllib.parse import urlparse


def validate_web_source_url(raw: str | None) -> str:
    """Validate a web source URL and return the stripped value.

    Args:
        raw: User-provided URL string.

    Returns:
        Stripped URL string.

    Raises:
        ValueError: If the URL is missing or not a valid http(s) URL with host.
    """
    if raw is None:
        raise ValueError("网页来源需要填写有效的 URL。")
    text = raw.strip()
    if not text:
        raise ValueError("网页来源需要填写有效的 URL。")
    parsed = urlparse(text)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("URL 必须以 http:// 或 https:// 开头。")
    if not parsed.netloc:
        raise ValueError("URL 必须包含有效的主机名。")
    return text
