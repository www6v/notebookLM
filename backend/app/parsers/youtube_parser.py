"""YouTube transcript extractor using yt-dlp."""

import json
import subprocess
import tempfile


def extract_youtube_transcript(url: str) -> str:
    """Extract transcript/subtitles from a YouTube video.

    Uses yt-dlp to download auto-generated or manual subtitles.
    """
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Try to get subtitles
            result = subprocess.run(
                [
                    "yt-dlp",
                    "--skip-download",
                    "--write-auto-sub",
                    "--write-sub",
                    "--sub-lang", "en",
                    "--sub-format", "json3",
                    "--output", f"{tmpdir}/%(id)s",
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Find subtitle file
            import os
            for filename in os.listdir(tmpdir):
                if filename.endswith(".json3"):
                    filepath = os.path.join(tmpdir, filename)
                    with open(filepath) as f:
                        data = json.load(f)

                    # Extract text from json3 format
                    events = data.get("events", [])
                    texts = []
                    for event in events:
                        segs = event.get("segs", [])
                        for seg in segs:
                            text = seg.get("utf8", "").strip()
                            if text and text != "\n":
                                texts.append(text)
                    return " ".join(texts)

            # Fallback: get video description
            result = subprocess.run(
                [
                    "yt-dlp",
                    "--skip-download",
                    "--print", "%(title)s\n%(description)s",
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.stdout.strip() if result.stdout else "No transcript available."

    except Exception as e:
        return f"Failed to extract transcript: {str(e)}"
