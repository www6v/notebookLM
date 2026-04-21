"""Web page content fetch via Jina Reader (markdown/plain text)."""

import httpx

_JINA_READER_PREFIX = "https://r.jinaai.cn/"


def build_jina_reader_url(page_url: str) -> str:
    """Build the Jina Reader URL for a target page.

    Args:
        page_url: Absolute http(s) URL of the page to read.

    Returns:
        Full Jina Reader endpoint URL.
    """
    trimmed = page_url.strip()
    return f"{_JINA_READER_PREFIX}{trimmed}"


async def fetch_web_markdown_via_jina(page_url: str) -> str:
    """Fetch page content as markdown via Jina Reader.

    Args:
        page_url: Target page URL (http or https).

    Returns:
        Response body (markdown text).

    Raises:
        httpx.HTTPError: On network or HTTP error responses.
    """
    jina_url = build_jina_reader_url(page_url)
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(jina_url, follow_redirects=True)
        response.raise_for_status()
    text = response.text or ""
    return text.strip()


async def parse_web_page(url: str) -> str:
    """Backward-compatible alias: fetch web page as markdown via Jina."""
    return await fetch_web_markdown_via_jina(url)
