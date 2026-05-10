"""Bilibili transcript extractor using yt-dlp (same CLI model as YouTube)."""

from __future__ import annotations

import os
import re
import subprocess
import tempfile

from notebooklm_shared.config import settings
from app.parsers.subtitle_json3 import first_bilibili_style_json_transcript_in_dir
from app.parsers.yt_dlp_util import cookies_argv_from_path, resolve_yt_dlp_argv

_BILI_SUB_LOGIN_HINT = "only available when logged in"

# Prefer Chinese tracks; deprioritize unrelated dubs (e.g. ar) when using all.
_SUB_LANGS_ZH_FIRST = "zh-Hans,zh-CN,zh-Hant,zh-TW,zh,en"


def _lang_rank(filename: str) -> int:
    """Lower = try first when multiple subtitle files exist."""
    n = filename.lower()
    if re.search(
        r"zh[-_]?hans|zh[-_]?cn|zh_cn|cmn|\.cmn\.|\bcmn\b|mandarin",
        n,
    ):
        return 0
    if re.search(r"zh[-_]?hant|zh[-_]?tw|zh_tw", n):
        return 1
    if re.search(r"\.zh\.|[-_]zh[._]|[._]zho[._]", n):
        return 2
    if re.search(r"[-_.]en[._]|\beng\b|english", n):
        return 15
    if re.search(r"[-_.]ja[._]|japanese|\bjpn\b", n):
        return 20
    if re.search(r"[-_.]ko[._]|korean|\bkor\b", n):
        return 25
    if re.search(r"[-_.]ar[._]|\barab|arabic", n):
        return 500
    return 100


def _subtitle_sort_key(name: str) -> tuple[int, str]:
    return (_lang_rank(name), name)


def _text_from_srt_path(filepath: str) -> str:
    """Strip timing and indices from SRT, return dialogue text."""
    with open(filepath, encoding="utf-8", errors="replace") as handle:
        lines = handle.read().splitlines()
    parts: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.isdigit():
            continue
        if "-->" in stripped:
            continue
        cleaned = re.sub(r"<[^>]+>", "", stripped).strip()
        if cleaned:
            parts.append(cleaned)
    return " ".join(parts)


def _text_from_vtt_path(filepath: str) -> str:
    """Strip WEBVTT timing and cues, return plain text."""
    with open(filepath, encoding="utf-8", errors="replace") as handle:
        lines = handle.read().splitlines()
    parts: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        upper = stripped.upper()
        if upper.startswith("WEBVTT") or upper.startswith("NOTE"):
            continue
        if upper.startswith("STYLE") or upper.startswith("REGION"):
            continue
        if "-->" in stripped:
            continue
        if stripped.isdigit():
            continue
        cleaned = re.sub(r"<[^>]+>", "", stripped).strip()
        if cleaned:
            parts.append(cleaned)
    return " ".join(parts)


def _first_srt_transcript_in_dir(directory: str) -> str | None:
    names = [n for n in os.listdir(directory) if n.lower().endswith(".srt")]
    names.sort(key=_subtitle_sort_key)
    for name in names:
        path = os.path.join(directory, name)
        try:
            text = _text_from_srt_path(path).strip()
        except OSError:
            continue
        if text:
            return text
    return None


def _first_vtt_transcript_in_dir(directory: str) -> str | None:
    names = [n for n in os.listdir(directory) if n.lower().endswith(".vtt")]
    names.sort(key=_subtitle_sort_key)
    for name in names:
        path = os.path.join(directory, name)
        try:
            text = _text_from_vtt_path(path).strip()
        except OSError:
            continue
        if text:
            return text
    return None


def _login_required_message() -> str:
    if (settings.ytdlp_cookies_file or "").strip():
        return (
            "[Bilibili 字幕] 已配置 YTDLP_COOKIES_FILE 但仍无法拉取字幕，"
            "请重新导出 B 站登录 cookies（Netscape 格式）后重试。"
        )
    return (
        "[Bilibili 字幕] 该站字幕需登录态。"
        "请在 .env 设置 YTDLP_COOKIES_FILE 为 Netscape 格式 cookies 文件路径"
        "（可用 Get cookies.txt 等扩展从 bilibili.com 导出），"
        "保存后重启 Celery Worker。说明见 README / README.zh-CN。"
    )


def _transcript_from_tmpdir(tmpdir: str) -> str | None:
    text = first_bilibili_style_json_transcript_in_dir(
        tmpdir,
        name_sort_key=_subtitle_sort_key,
    )
    if text:
        return text
    text = _first_srt_transcript_in_dir(tmpdir)
    if text:
        return text
    text = _first_vtt_transcript_in_dir(tmpdir)
    if text:
        return text
    return None


def _yt_dlp_write_subs(
    base: list[str],
    cookie_argv: list[str],
    url: str,
    out_template: str,
    *,
    sub_langs: str,
    sub_format: str | None,
) -> subprocess.CompletedProcess:
    parts = [
        "--skip-download",
        "--write-auto-sub",
        "--write-sub",
        "--sub-langs",
        sub_langs,
    ]
    if sub_format:
        parts.extend(["--sub-format", sub_format])
    parts.extend(["--output", out_template, url])
    cmd = base + cookie_argv + parts
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=settings.ytdlp_subprocess_timeout_seconds,
    )


def extract_bilibili_transcript(url: str) -> str:
    """Extract subtitles from a Bilibili video URL via yt-dlp.

    Prefers Chinese subtitles, then falls back to other languages, SRT, or
    title/description (when login is not required for subs).
    """
    try:
        base = resolve_yt_dlp_argv()
        if not base:
            return (
                "Failed to extract Bilibili transcript: yt-dlp is not "
                "available. Install yt-dlp in the Celery environment "
                "(pip install yt-dlp)."
            )

        cookie_argv = cookies_argv_from_path(settings.ytdlp_cookies_file)

        with tempfile.TemporaryDirectory() as tmpdir:
            out_template = os.path.join(tmpdir, "%(id)s")
            stderr_combined = ""

            sub_run = _yt_dlp_write_subs(
                base,
                cookie_argv,
                url,
                out_template,
                sub_langs=_SUB_LANGS_ZH_FIRST,
                sub_format="best",
            )
            stderr_combined += sub_run.stderr or ""

            text = _transcript_from_tmpdir(tmpdir)
            if not text:
                sub_run2 = _yt_dlp_write_subs(
                    base,
                    cookie_argv,
                    url,
                    out_template,
                    sub_langs=_SUB_LANGS_ZH_FIRST,
                    sub_format=None,
                )
                stderr_combined += sub_run2.stderr or ""
                text = _transcript_from_tmpdir(tmpdir)

            if not text:
                sub_run3 = _yt_dlp_write_subs(
                    base,
                    cookie_argv,
                    url,
                    out_template,
                    sub_langs="all",
                    sub_format="best",
                )
                stderr_combined += sub_run3.stderr or ""
                text = _transcript_from_tmpdir(tmpdir)

            if not text:
                sub_run4 = _yt_dlp_write_subs(
                    base,
                    cookie_argv,
                    url,
                    out_template,
                    sub_langs="all",
                    sub_format=None,
                )
                stderr_combined += sub_run4.stderr or ""
                text = _transcript_from_tmpdir(tmpdir)

            stderr_lower = stderr_combined.lower()

            if text:
                return text

            if _BILI_SUB_LOGIN_HINT in stderr_lower:
                return _login_required_message()

            meta = subprocess.run(
                base
                + cookie_argv
                + [
                    "--skip-download",
                    "--print",
                    "%(title)s\n%(description)s",
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=min(120, settings.ytdlp_subprocess_timeout_seconds),
            )
            out = (meta.stdout or "").strip()
            if out:
                return out
            return "No transcript available."

    except Exception as exc:
        return f"Failed to extract Bilibili transcript: {exc}"
