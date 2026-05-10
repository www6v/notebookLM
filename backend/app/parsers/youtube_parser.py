"""YouTube transcript extractor using yt-dlp."""

import subprocess
import tempfile

from notebooklm_shared.config import settings
from app.parsers.subtitle_json3 import first_json3_transcript_in_dir
from app.parsers.yt_dlp_util import cookies_argv_from_path, resolve_yt_dlp_argv


def extract_youtube_transcript(url: str) -> str:
    """Extract transcript/subtitles from a YouTube video.

    Uses yt-dlp to download auto-generated or manual subtitles.
    """
    try:
        base = resolve_yt_dlp_argv()
        if not base:
            return (
                "Failed to extract transcript: yt-dlp is not available. "
                "Install yt-dlp in the Celery environment (pip install yt-dlp)."
            )

        cookie_argv = cookies_argv_from_path(settings.ytdlp_cookies_file)

        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(
                base
                + cookie_argv
                + [
                    "--skip-download",
                    "--write-auto-sub",
                    "--write-sub",
                    "--sub-lang",
                    "en",
                    "--sub-format",
                    "json3",
                    "--output",
                    f"{tmpdir}/%(id)s",
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=settings.ytdlp_subprocess_timeout_seconds,
            )

            text = first_json3_transcript_in_dir(tmpdir)
            if text:
                return text

            result = subprocess.run(
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
            return result.stdout.strip() if result.stdout else "No transcript available."

    except Exception as e:
        return f"Failed to extract transcript: {str(e)}"
