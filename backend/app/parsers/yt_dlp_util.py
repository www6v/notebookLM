"""Resolve how to invoke yt-dlp (CLI on PATH or ``python -m yt_dlp``)."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def _cookie_file_candidates(raw: str) -> list[Path]:
    """Paths to try for a cookies file (cwd / backend / repo root)."""
    expanded = Path(raw).expanduser()
    out: list[Path] = []
    if expanded.is_absolute():
        out.append(expanded)
        return out
    backend_dir = Path(__file__).resolve().parent.parent.parent
    repo_root = backend_dir.parent
    out.extend([
        Path.cwd() / expanded,
        backend_dir / expanded,
        repo_root / expanded,
        expanded,
    ])
    return out


def cookies_argv_from_path(cookies_file: str | None) -> list[str]:
    """Return ``--cookies <path>`` when a readable file is configured."""
    if not cookies_file:
        return []
    raw = cookies_file.strip().strip('"').strip("'")
    if not raw:
        return []
    seen: set[str] = set()
    for candidate in _cookie_file_candidates(raw):
        try:
            key = str(candidate.resolve())
        except OSError:
            continue
        if key in seen:
            continue
        seen.add(key)
        if candidate.is_file():
            return ["--cookies", key]
    return []


def resolve_yt_dlp_argv() -> list[str] | None:
    """Return argv prefix to run yt-dlp, or None if unavailable."""
    which_path = shutil.which("yt-dlp") or shutil.which("yt-dlp.exe")
    if which_path:
        return [which_path]

    try:
        import yt_dlp  # noqa: F401
    except ImportError:
        return None

    return [sys.executable, "-m", "yt_dlp"]
