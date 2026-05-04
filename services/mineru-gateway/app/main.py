"""FastAPI gateway: OSS ``pdf_url`` or multipart PDF → MinerU CLI → JSON for NotebookLM."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

app = FastAPI(
    title="MinerU gateway",
    description="Implements POST /v1/parse for notebookLM backend (mineru_client).",
    version="1.0.0",
)

_GATEWAY_API_KEY = (os.environ.get("MINERU_GATEWAY_API_KEY") or "").strip()
_MINERU_TIMEOUT_SEC = int(os.environ.get("MINERU_GATEWAY_TIMEOUT_SEC", "600"))


class ParseJsonBody(BaseModel):
    pdf_url: str = Field(..., min_length=8)
    output_preference: str = Field(default="markdown")


def _require_bearer(request: Request) -> None:
    if not _GATEWAY_API_KEY:
        return
    auth = request.headers.get("authorization") or ""
    expected = f"Bearer {_GATEWAY_API_KEY}"
    if auth != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing Authorization")


def _download_pdf(url: str) -> bytes:
    try:
        with httpx.Client(timeout=httpx.Timeout(300.0, connect=30.0)) as client:
            response = client.get(url, follow_redirects=True)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to download pdf_url: {exc}",
        ) from exc
    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"pdf_url returned HTTP {response.status_code}",
        )
    data = response.content
    if not data:
        raise HTTPException(status_code=400, detail="Downloaded PDF is empty")
    return data


def _mineru_invocation_prefix() -> list[str]:
    """Resolve how to start MinerU: ``mineru`` on PATH, or ``python -m``."""
    cli_bin = (os.environ.get("MINERU_CLI_BIN") or "mineru").strip() or "mineru"
    if os.path.isfile(cli_bin):
        return [cli_bin]
    resolved = shutil.which(cli_bin)
    if resolved:
        return [resolved]
    return [sys.executable, "-m", "mineru.cli.client"]


def _run_mineru_cli(pdf_path: Path, output_dir: Path) -> None:
    """Run MinerU parse.

    Default: ``python -m app.mineru_invoke`` so exceptions become non-zero
    exits (the stock ``mineru`` CLI logs errors and still exits 0).

    Set ``MINERU_GATEWAY_LEGACY_MINERU_CLI=1`` to use ``mineru -p …`` plus
    ``MINERU_CLI_EXTRA_ARGS`` instead.
    """
    legacy = (
        (os.environ.get("MINERU_GATEWAY_LEGACY_MINERU_CLI") or "")
        .strip()
        .lower()
    )
    if legacy in ("1", "true", "yes"):
        prefix = _mineru_invocation_prefix()
        cmd = [
            *prefix,
            "-p",
            str(pdf_path),
            "-o",
            str(output_dir),
        ]
        extra = (os.environ.get("MINERU_CLI_EXTRA_ARGS") or "").strip()
        if extra:
            cmd.extend(extra.split())
    else:
        cmd = [
            sys.executable,
            "-m",
            "app.mineru_invoke",
            str(pdf_path),
            str(output_dir),
        ]
    logger.info("Running: %s", " ".join(cmd))
    started = time.perf_counter()
    try:
        subprocess.run(
            cmd,
            check=True,
            timeout=_MINERU_TIMEOUT_SEC,
            env=os.environ.copy(),
            capture_output=True,
            text=True,
        )
    finally:
        elapsed = time.perf_counter() - started
        logger.info("MinerU CLI parse wall time %.2fs", elapsed)


def _iter_markdown_paths(output_dir: Path) -> list[Path]:
    """All markdown files under output (case-insensitive suffix)."""
    found: list[Path] = []
    for path in output_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".markdown"}:
            continue
        found.append(path)
    return found


def _pick_markdown_file(output_dir: Path) -> Path | None:
    """Choose the main Markdown file under MinerU output tree."""
    md_files = sorted(
        _iter_markdown_paths(output_dir),
        key=lambda p: p.stat().st_size,
        reverse=True,
    )
    if not md_files:
        return None
    preferred = [p for p in md_files if "full" in p.name.lower()]
    return preferred[0] if preferred else md_files[0]


def _pick_content_list_json(output_dir: Path) -> Path | None:
    """Largest ``*_content_list.json`` (MinerU always writes this when enabled)."""
    candidates: list[Path] = []
    for path in output_dir.rglob("*_content_list.json"):
        if path.is_file():
            candidates.append(path)
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_size)


def _markdown_from_content_list(items: object) -> str:
    """Turn MinerU ``content_list`` JSON into readable markdown (gateway fallback)."""
    if not isinstance(items, list):
        return ""
    parts: list[str] = []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        block_type = raw.get("type")
        if block_type == "text":
            body = (raw.get("text") or "").strip()
            if not body:
                continue
            level = int(raw.get("text_level") or 0)
            if 1 <= level <= 6:
                parts.append(f"{'#' * level} {body}")
            else:
                parts.append(body)
        elif block_type == "image":
            img_path = (raw.get("img_path") or "").strip()
            captions = raw.get("image_caption") or []
            if isinstance(captions, list):
                cap_text = " ".join(
                    str(c).strip() for c in captions if str(c).strip()
                )
            else:
                cap_text = str(captions).strip()
            foots = raw.get("image_footnote") or []
            if isinstance(foots, list):
                fn_text = "\n".join(
                    str(f).strip() for f in foots if str(f).strip()
                )
            else:
                fn_text = str(foots).strip()
            if img_path:
                parts.append(f"![]({img_path})")
            if cap_text:
                parts.append(cap_text)
            if fn_text:
                parts.append(fn_text)
        elif block_type == "table":
            html = raw.get("table_body")
            if isinstance(html, str) and html.strip():
                parts.append(html.strip())
            img_path = (raw.get("img_path") or "").strip()
            if img_path:
                parts.append(f"![]({img_path})")
            caps = raw.get("table_caption") or []
            if isinstance(caps, list):
                cap_text = " ".join(
                    str(c).strip() for c in caps if str(c).strip()
                )
            else:
                cap_text = str(caps).strip()
            if cap_text:
                parts.append(cap_text)
        elif block_type == "equation":
            latex = (raw.get("text") or "").strip()
            img_path = (raw.get("img_path") or "").strip()
            if latex:
                parts.append(f"$$\n{latex}\n$$")
            elif img_path:
                parts.append(f"![]({img_path})")
    return "\n\n".join(parts)


def _output_dir_summary(output_dir: Path, limit: int = 4000) -> str:
    """Relative paths under output_dir for error messages."""
    lines: list[str] = []
    for path in sorted(output_dir.rglob("*")):
        rel = path.relative_to(output_dir).as_posix()
        if path.is_dir():
            lines.append(f"{rel}/")
        else:
            try:
                sz = path.stat().st_size
            except OSError:
                sz = -1
            lines.append(f"{rel} ({sz} bytes)")
    text = "\n".join(lines)
    if len(text) > limit:
        return text[:limit] + "\n... (truncated)"
    return text or "(empty output directory)"


def _collect_binary_assets(output_dir: Path) -> list[tuple[str, bytes]]:
    """Return (relative_path, bytes) for images next to MinerU output."""
    exts = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
    out: list[tuple[str, bytes]] = []
    for path in output_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in exts:
            continue
        rel = path.relative_to(output_dir).as_posix()
        if ".." in rel.split("/"):
            continue
        out.append((rel, path.read_bytes()))
    return out


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/parse")
async def parse_v1(request: Request) -> JSONResponse:
    """JSON ``pdf_url`` or multipart ``pdf`` (NotebookLM ``mineru_use_multipart``)."""
    _require_bearer(request)
    work = Path(tempfile.mkdtemp(prefix="mineru-gw-"))
    try:
        ct = (request.headers.get("content-type") or "").lower()
        if "application/json" in ct:
            data = await request.json()
            body = ParseJsonBody.model_validate(data)
            raw = _download_pdf(body.pdf_url.strip())
            pdf_path = work / "document.pdf"
            pdf_path.write_bytes(raw)
        elif "multipart/form-data" in ct:
            form = await request.form()
            upload = form.get("pdf")
            if upload is None:
                raise HTTPException(
                    status_code=400,
                    detail="multipart form must include pdf file field",
                )
            if isinstance(upload, str):
                raise HTTPException(status_code=400, detail="invalid pdf field")
            raw = await upload.read()
            if not raw:
                raise HTTPException(status_code=400, detail="Empty pdf upload")
            name = getattr(upload, "filename", None) or "upload.pdf"
            pdf_path = work / Path(name).name
            pdf_path.write_bytes(raw)
        else:
            raise HTTPException(
                status_code=415,
                detail="Use Content-Type: application/json or multipart/form-data",
            )

        out_dir = work / "out"
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            await asyncio.to_thread(_run_mineru_cli, pdf_path, out_dir)
        except subprocess.CalledProcessError as exc:
            err_tail = ""
            if exc.stderr:
                err_tail = exc.stderr[-2000:]
            elif exc.stdout:
                err_tail = exc.stdout[-2000:]
            logger.error("mineru failed: %s", err_tail)
            raise HTTPException(
                status_code=500,
                detail=f"mineru CLI failed: {err_tail or str(exc)}",
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise HTTPException(
                status_code=504,
                detail="mineru CLI timed out",
            ) from exc
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=503,
                detail=(
                    "mineru not found: pip install -r requirements.txt "
                    "(or mineru[core]) in the gateway environment / image"
                ),
            ) from exc

        md_path = _pick_markdown_file(out_dir)
        markdown = ""
        if md_path is not None:
            markdown = md_path.read_text(encoding="utf-8", errors="replace")
        if not markdown.strip():
            cl_path = _pick_content_list_json(out_dir)
            if cl_path is not None:
                try:
                    payload = json.loads(
                        cl_path.read_text(encoding="utf-8", errors="replace"),
                    )
                    markdown = _markdown_from_content_list(payload)
                except (json.JSONDecodeError, OSError) as exc:
                    logger.warning("content_list fallback failed: %s", exc)
        if not markdown.strip():
            tree = _output_dir_summary(out_dir)
            logger.error(
                "MinerU finished without markdown; output tree:\n%s",
                tree,
            )
            raise HTTPException(
                status_code=500,
                detail=(
                    "MinerU produced no markdown (and no usable content_list). "
                    "See gateway logs. With MINERU_GATEWAY_LEGACY_MINERU_CLI=1, "
                    "the stock mineru binary can exit 0 despite parse errors. "
                    "Output tree:\n"
                    f"{tree}"
                ),
            )
        assets = _collect_binary_assets(out_dir)
        files_payload = []
        for rel, blob in assets:
            files_payload.append({
                "path": rel,
                "content_base64": base64.b64encode(blob).decode("ascii"),
            })
        return JSONResponse({"markdown": markdown, "files": files_payload})
    finally:
        shutil.rmtree(work, ignore_errors=True)
