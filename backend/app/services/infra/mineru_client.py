"""HTTP client for an external MinerU-compatible PDF → Markdown service."""

from __future__ import annotations

import base64
import binascii
import logging
import mimetypes
import time
from dataclasses import dataclass

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class MinerUClientError(Exception):
    """Raised when the MinerU HTTP API returns an error or invalid payload."""


@dataclass(frozen=True)
class MinerUParseResult:
    """Structured output from the MinerU parse endpoint."""

    markdown: str
    files: list[tuple[str, bytes]]


def _normalize_rel_path(path: str) -> str | None:
    """Return a safe OSS-relative path or None if unsafe."""
    if not path or not isinstance(path, str):
        return None
    normalized = path.replace("\\", "/").strip().lstrip("/")
    if not normalized:
        return None
    parts = normalized.split("/")
    if ".." in parts:
        return None
    return normalized


def _extract_markdown(payload: dict) -> str:
    if not isinstance(payload, dict):
        return ""
    if "markdown" in payload and payload["markdown"] is not None:
        return str(payload["markdown"])
    nested = payload.get("data")
    if isinstance(nested, dict) and nested.get("markdown") is not None:
        return str(nested["markdown"])
    nested = payload.get("result")
    if isinstance(nested, dict) and nested.get("markdown") is not None:
        return str(nested["markdown"])
    return ""


def _extract_file_entries(payload: dict) -> list[tuple[str, bytes]]:
    out: list[tuple[str, bytes]] = []
    raw = payload.get("files")
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        path = item.get("path") or item.get("name") or item.get("filename")
        if not path:
            continue
        b64 = item.get("content_base64") or item.get("content_b64")
        if not b64:
            continue
        try:
            data = base64.b64decode(str(b64), validate=False)
        except (binascii.Error, ValueError) as exc:
            logger.warning("MinerU file skip invalid base64 %s: %s", path, exc)
            continue
        safe = _normalize_rel_path(str(path))
        if safe is None:
            continue
        out.append((safe, data))
    return out


def call_mineru_parse(
    *,
    pdf_presigned_url: str | None,
    pdf_bytes: bytes | None,
    original_filename: str = "document.pdf",
) -> MinerUParseResult:
    """POST to the configured MinerU service and return markdown + sidecar files.

    Either ``pdf_presigned_url`` (JSON body) or ``pdf_bytes`` (multipart) must
    be set according to ``settings.mineru_use_multipart``.
    """
    base = (settings.mineru_base_url or "").strip().rstrip("/")
    if not base:
        raise MinerUClientError("mineru_base_url is not configured")

    path = (settings.mineru_parse_path or "/v1/parse").strip()
    if not path.startswith("/"):
        path = "/" + path
    url = f"{base}{path}"

    timeout = httpx.Timeout(settings.mineru_timeout_seconds)
    headers: dict[str, str] = {}
    key = (settings.mineru_api_key or "").strip()
    if key:
        headers["Authorization"] = f"Bearer {key}"

    use_multipart = settings.mineru_use_multipart
    t_req = time.perf_counter()
    if use_multipart:
        if not pdf_bytes:
            raise MinerUClientError("mineru_use_multipart requires pdf bytes")
        safe_name = original_filename.replace("\\", "/").split("/")[-1] or (
            "document.pdf"
        )
        files = {
            "pdf": (safe_name, pdf_bytes, "application/pdf"),
        }
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, files=files, headers=headers)
    else:
        if not pdf_presigned_url:
            raise MinerUClientError("pdf_presigned_url required for JSON mode")
        body = {
            "pdf_url": pdf_presigned_url,
            "output_preference": "markdown",
        }
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, json=body, headers=headers)
    http_elapsed_s = time.perf_counter() - t_req
    pdf_mb = (len(pdf_bytes) / (1024 * 1024)) if pdf_bytes else None
    logger.info(
        "MinerU HTTP POST done url=%s mode=%s status=%s elapsed_s=%.3f "
        "pdf_mb=%s",
        url,
        "multipart" if use_multipart else "json_url",
        response.status_code,
        http_elapsed_s,
        f"{pdf_mb:.2f}" if pdf_mb is not None else "n/a",
    )

    if response.status_code >= 400:
        raise MinerUClientError(
            f"HTTP {response.status_code}: {(response.text or '')[:400]}"
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise MinerUClientError("Response is not JSON") from exc

    if not isinstance(payload, dict):
        raise MinerUClientError("JSON root must be an object")

    markdown = _extract_markdown(payload).strip()
    files = _extract_file_entries(payload)
    if not markdown:
        raise MinerUClientError("MinerU response missing markdown")

    return MinerUParseResult(markdown=markdown, files=files)


def apply_asset_urls_to_markdown(
    markdown: str,
    path_to_public_url: dict[str, str],
) -> str:
    """Replace relative asset paths in markdown/HTML with absolute URLs."""
    if not path_to_public_url:
        return markdown

    ordered = sorted(
        path_to_public_url.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    )

    def _variants(rel: str) -> list[str]:
        rel = rel.replace("\\", "/")
        base = [rel, f"./{rel}"]
        encoded = "/".join(
            p.replace(" ", "%20") for p in rel.split("/")
        )
        if encoded != rel:
            base.append(encoded)
            base.append(f"./{encoded}")
        return base

    out = markdown
    for rel, public_url in ordered:
        for variant in _variants(rel):
            out = out.replace(variant, public_url)
    return out


def guess_content_type(relative_path: str) -> str:
    """Guess MIME type for an extracted asset path."""
    guessed, _ = mimetypes.guess_type(relative_path)
    return guessed or "application/octet-stream"
