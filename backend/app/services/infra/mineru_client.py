"""HTTP client for an external MinerU-compatible PDF-to-Markdown service."""

from __future__ import annotations

import io
import logging
import mimetypes
import re
import time
import zipfile
from dataclasses import dataclass
from typing import Any

import httpx

from notebooklm_shared.config import settings

logger = logging.getLogger(__name__)

_OFFICIAL_EXTRACT_PATH = "/api/v4/extract/task"


def mineru_official_extract_api_configured() -> bool:
    """True when using MinerU net ``/api/v4/extract/task`` (URL + ZIP flow)."""
    path = (settings.mineru_parse_path or "").strip().replace("\\", "/")
    return path.rstrip("/") == _OFFICIAL_EXTRACT_PATH


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


# --- Legacy self-hosted gateway response parsing (POST /v1/parse, etc.) ---
# def _extract_markdown(payload: dict) -> str:
#     if not isinstance(payload, dict):
#         return ""
#     if "markdown" in payload and payload["markdown"] is not None:
#         return str(payload["markdown"])
#     nested = payload.get("data")
#     if isinstance(nested, dict) and nested.get("markdown") is not None:
#         return str(nested["markdown"])
#     nested = payload.get("result")
#     if isinstance(nested, dict) and nested.get("markdown") is not None:
#         return str(nested["markdown"])
#     return ""
#
#
# def _extract_file_entries(payload: dict) -> list[tuple[str, bytes]]:
#     import base64
#     import binascii
#
#     out: list[tuple[str, bytes]] = []
#     raw = payload.get("files")
#     if not isinstance(raw, list):
#         return out
#     for item in raw:
#         if not isinstance(item, dict):
#             continue
#         path = item.get("path") or item.get("name") or item.get("filename")
#         if not path:
#             continue
#         b64 = item.get("content_base64") or item.get("content_b64")
#         if not b64:
#             continue
#         try:
#             data = base64.b64decode(str(b64), validate=False)
#         except (binascii.Error, ValueError) as exc:
#             logger.warning("MinerU file skip invalid base64 %s: %s", path, exc)
#             continue
#         safe = _normalize_rel_path(str(path))
#         if safe is None:
#             continue
#         out.append((safe, data))
#     return out


def _mineru_v4_json_errors(payload: dict[str, Any], context: str) -> None:
    code = payload.get("code")
    if code == 0:
        return
    msg = payload.get("msg")
    raise MinerUClientError(
        f"{context}: code={code!r} msg={msg!r}"
    )


def _mineru_pick_full_md_zip_member(names: list[str]) -> str | None:
    files = [n.replace("\\", "/") for n in names if n and not n.endswith("/")]
    full_hits = [n for n in files if n.lower().split("/")[-1] == "full.md"]
    if not full_hits:
        return None
    return sorted(full_hits, key=lambda x: (x.count("/"), len(x)))[0]


def _mineru_parse_result_from_official_zip(zip_bytes: bytes) -> MinerUParseResult:
    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile as exc:
        raise MinerUClientError("MinerU result is not a valid ZIP") from exc

    with zf:
        names = zf.namelist()
        full_member = _mineru_pick_full_md_zip_member(names)
        if not full_member:
            raise MinerUClientError("ZIP has no full.md from MinerU")

        markdown = zf.read(full_member).decode("utf-8", errors="replace").strip()
        if not markdown:
            raise MinerUClientError("MinerU full.md is empty")

        slash = full_member.rfind("/")
        root_prefix = full_member[: slash + 1] if slash >= 0 else ""

        files_out: list[tuple[str, bytes]] = []
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = info.filename.replace("\\", "/")
            if name == full_member:
                continue
            raw = zf.read(info)
            if root_prefix and name.startswith(root_prefix):
                rel = name[len(root_prefix) :]
            else:
                rel = name.lstrip("/")
            safe = _normalize_rel_path(rel)
            if safe is not None:
                files_out.append((safe, raw))

    return MinerUParseResult(markdown=markdown, files=files_out)


def _call_mineru_official_v4_extract(*, file_public_url: str) -> MinerUParseResult:
    """MinerU official API: submit URL, poll, download ``full_zip_url`` ZIP."""
    base = (settings.mineru_base_url or "").strip().rstrip("/")
    if not base:
        raise MinerUClientError("mineru_base_url is not configured")
    token = (settings.mineru_api_key or "").strip()
    if not token:
        raise MinerUClientError(
            "mineru_api_key is required for official /api/v4/extract/task"
        )

    create_url = f"{base}{_OFFICIAL_EXTRACT_PATH}"
    timeout = httpx.Timeout(settings.mineru_timeout_seconds)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    body = {
        "url": file_public_url.strip(),
        "model_version": (settings.mineru_model_version or "vlm").strip()
        or "vlm",
    }

    t0 = time.perf_counter()
    with httpx.Client(timeout=timeout) as client:
        create_resp = client.post(create_url, json=body, headers=headers)
        if create_resp.status_code >= 400:
            raise MinerUClientError(
                f"extract/task HTTP {create_resp.status_code}: "
                f"{(create_resp.text or '')[:400]}"
            )
        try:
            create_payload = create_resp.json()
        except ValueError as exc:
            raise MinerUClientError("extract/task response is not JSON") from exc
        if not isinstance(create_payload, dict):
            raise MinerUClientError("extract/task JSON root must be an object")
        _mineru_v4_json_errors(create_payload, "extract/task submit")
        data = create_payload.get("data")
        if not isinstance(data, dict):
            raise MinerUClientError("extract/task missing data object")
        task_id = data.get("task_id")
        if not task_id or not isinstance(task_id, str):
            raise MinerUClientError("extract/task missing data.task_id")

        poll_url = f"{base}{_OFFICIAL_EXTRACT_PATH}/{task_id}"
        deadline = time.monotonic() + float(settings.mineru_timeout_seconds)
        interval = float(settings.mineru_poll_interval_seconds)
        full_zip_url: str | None = None

        while time.monotonic() < deadline:
            poll_resp = client.get(poll_url, headers=headers)
            if poll_resp.status_code >= 400:
                raise MinerUClientError(
                    f"extract/task/{task_id} HTTP {poll_resp.status_code}: "
                    f"{(poll_resp.text or '')[:400]}"
                )
            try:
                poll_payload = poll_resp.json()
            except ValueError as exc:
                raise MinerUClientError(
                    f"extract/task/{task_id} response is not JSON"
                ) from exc
            if not isinstance(poll_payload, dict):
                raise MinerUClientError("poll JSON root must be an object")
            _mineru_v4_json_errors(poll_payload, f"extract/task/{task_id} poll")
            pdata = poll_payload.get("data")
            if not isinstance(pdata, dict):
                raise MinerUClientError("poll missing data object")

            state = pdata.get("state")
            if state == "failed":
                err = pdata.get("err_msg") or "MinerU task failed"
                raise MinerUClientError(str(err))
            if state == "done":
                raw_zip = pdata.get("full_zip_url")
                if not raw_zip or not isinstance(raw_zip, str):
                    raise MinerUClientError("done state missing full_zip_url")
                full_zip_url = raw_zip.strip()
                break
            time.sleep(interval)
        else:
            raise MinerUClientError(
                f"MinerU task {task_id} timed out after "
                f"{settings.mineru_timeout_seconds}s"
            )

        zip_resp = client.get(full_zip_url)
        if zip_resp.status_code >= 400:
            raise MinerUClientError(
                f"ZIP download HTTP {zip_resp.status_code}: "
                f"{(zip_resp.text or '')[:200]}"
            )
        zip_bytes = zip_resp.content

    elapsed = time.perf_counter() - t0
    logger.info(
        "MinerU official v4 extract done task_id=%s zip_bytes=%s elapsed_s=%.3f",
        task_id,
        len(zip_bytes),
        elapsed,
    )
    return _mineru_parse_result_from_official_zip(zip_bytes)


def call_mineru_parse(
    *,
    pdf_presigned_url: str | None,
    pdf_bytes: bytes | None,
    original_filename: str = "document.pdf",
) -> MinerUParseResult:
    """Call MinerU official extract API and return markdown + sidecar files.

    ``mineru_parse_path`` must be ``/api/v4/extract/task``. ``pdf_presigned_url``
    is a **public** HTTPS URL to the PDF (MinerU fetches it; no OSS keys on
    their side). Result is read from the returned ZIP (``full.md`` + assets).
    """
    if mineru_official_extract_api_configured():
        if not pdf_presigned_url or not pdf_presigned_url.strip():
            raise MinerUClientError(
                "Official extract API requires a public file URL (pdf_url)"
            )
        if settings.mineru_use_multipart and pdf_bytes:
            logger.warning(
                "mineru_use_multipart ignored for official /api/v4/extract/task"
            )
        return _call_mineru_official_v4_extract(
            file_public_url=pdf_presigned_url.strip(),
        )

    # --- Legacy: POST JSON ``pdf_url`` or multipart ``pdf`` to a sidecar ---
    # base = (settings.mineru_base_url or "").strip().rstrip("/")
    # if not base:
    #     raise MinerUClientError("mineru_base_url is not configured")
    #
    # path = (settings.mineru_parse_path or "/v1/parse").strip()
    # if not path.startswith("/"):
    #     path = "/" + path
    # url = f"{base}{path}"
    #
    # timeout = httpx.Timeout(settings.mineru_timeout_seconds)
    # headers: dict[str, str] = {}
    # key = (settings.mineru_api_key or "").strip()
    # if key:
    #     headers["Authorization"] = f"Bearer {key}"
    #
    # use_multipart = settings.mineru_use_multipart
    # t_req = time.perf_counter()
    # if use_multipart:
    #     if not pdf_bytes:
    #         raise MinerUClientError("mineru_use_multipart requires pdf bytes")
    #     safe_name = original_filename.replace("\\", "/").split("/")[-1] or (
    #         "document.pdf"
    #     )
    #     files = {
    #         "pdf": (safe_name, pdf_bytes, "application/pdf"),
    #     }
    #     with httpx.Client(timeout=timeout) as client:
    #         response = client.post(url, files=files, headers=headers)
    # else:
    #     if not pdf_presigned_url:
    #         raise MinerUClientError("pdf_presigned_url required for JSON mode")
    #     body = {
    #         "pdf_url": pdf_presigned_url,
    #         "output_preference": "markdown",
    #     }
    #     with httpx.Client(timeout=timeout) as client:
    #         response = client.post(url, json=body, headers=headers)
    # http_elapsed_s = time.perf_counter() - t_req
    # pdf_mb = (len(pdf_bytes) / (1024 * 1024)) if pdf_bytes else None
    # logger.info(
    #     "MinerU HTTP POST done url=%s mode=%s status=%s elapsed_s=%.3f "
    #     "pdf_mb=%s",
    #     url,
    #     "multipart" if use_multipart else "json_url",
    #     response.status_code,
    #     http_elapsed_s,
    #     f"{pdf_mb:.2f}" if pdf_mb is not None else "n/a",
    # )
    #
    # if response.status_code >= 400:
    #     raise MinerUClientError(
    #         f"HTTP {response.status_code}: {(response.text or '')[:400]}"
    #     )
    #
    # try:
    #     payload = response.json()
    # except ValueError as exc:
    #     raise MinerUClientError("Response is not JSON") from exc
    #
    # if not isinstance(payload, dict):
    #     raise MinerUClientError("JSON root must be an object")
    #
    # markdown = _extract_markdown(payload).strip()
    # files = _extract_file_entries(payload)
    # if not markdown:
    #     raise MinerUClientError("MinerU response missing markdown")
    #
    # return MinerUParseResult(markdown=markdown, files=files)

    raise MinerUClientError(
        "Legacy MinerU gateway client is disabled. Set mineru_parse_path to "
        "/api/v4/extract/task and mineru_base_url to https://mineru.net "
        "(see mineru.net API docs)."
    )


def _relative_path_variants(rel: str) -> list[str]:
    """Stable list of path spellings MinerU may emit (longest first, unique)."""
    rel = rel.replace("\\", "/").lstrip("/")
    if not rel:
        return []
    encoded = "/".join(p.replace(" ", "%20") for p in rel.split("/"))
    raw: list[str] = [rel, f"./{rel}"]
    if encoded != rel:
        raw.extend((encoded, f"./{encoded}"))
    seen: set[str] = set()
    ordered: list[str] = []
    for item in sorted(raw, key=len, reverse=True):
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def _replace_asset_path_occurrences(body: str, old: str, new: str) -> str:
    """Swap one relative path for a URL in markdown links and HTML img src."""
    if not old or old == new:
        return body
    esc = re.escape(old)
    body = re.sub(
        rf'(!\[[^\]]*\]\()\s*{esc}\s*(\))',
        lambda m: m.group(1) + new + m.group(2),
        body,
    )
    body = re.sub(
        rf'(!\[[^\]]*\]\()\s*<\s*{esc}\s*>\s*(\))',
        lambda m: m.group(1) + "<" + new + ">" + m.group(2),
        body,
    )
    body = re.sub(
        rf'(\[[^\]]*\]\()\s*{esc}\s*(\))',
        lambda m: m.group(1) + new + m.group(2),
        body,
    )
    body = re.sub(
        rf'(?i)(src\s*=\s*)(["\']){esc}\2',
        lambda m: m.group(1) + m.group(2) + new + m.group(2),
        body,
    )
    return body


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

    out = markdown
    for rel, public_url in ordered:
        for variant in _relative_path_variants(rel):
            out = _replace_asset_path_occurrences(out, variant, public_url)
        for variant in _relative_path_variants(rel):
            out = out.replace(variant, public_url)
    return out


def guess_content_type(relative_path: str) -> str:
    """Guess MIME type for an extracted asset path."""
    guessed, _ = mimetypes.guess_type(relative_path)
    return guessed or "application/octet-stream"
