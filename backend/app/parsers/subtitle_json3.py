"""Parse YouTube/Bilibili-style json3 subtitle payloads from yt-dlp."""

from __future__ import annotations

import json
import os
from typing import Any, Callable


def transcript_text_from_json3(data: dict[str, Any]) -> str:
    """Build plain text from a json3 subtitle document."""
    events = data.get("events", [])
    texts: list[str] = []
    for event in events:
        segs = event.get("segs", [])
        for seg in segs:
            text = seg.get("utf8", "").strip()
            if text and text != "\n":
                texts.append(text)
    return " ".join(texts)


def first_json3_transcript_in_dir(directory: str) -> str | None:
    """Return transcript text from the first ``*.json3`` file in a directory."""
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".json3"):
            continue
        path = os.path.join(directory, name)
        try:
            with open(path, encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError):
            continue
        text = transcript_text_from_json3(payload).strip()
        if text:
            return text
    return None


def first_bilibili_style_json_transcript_in_dir(
    directory: str,
    *,
    name_sort_key: Callable[[str], tuple] | None = None,
) -> str | None:
    """Like json3, but also accept ``*.json`` with ``events`` (yt-dlp / B站).

    ``name_sort_key`` optional: sort filenames before trying (e.g. zh before ar).
    """
    names = [n for n in os.listdir(directory)]
    if name_sort_key is not None:
        names.sort(key=name_sort_key)
    else:
        names.sort()
    for name in names:
        lower = name.lower()
        if lower.endswith(".info.json"):
            continue
        if not (lower.endswith(".json3") or lower.endswith(".json")):
            continue
        path = os.path.join(directory, name)
        try:
            with open(path, encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError, TypeError):
            continue
        if not isinstance(payload, dict) or "events" not in payload:
            continue
        text = transcript_text_from_json3(payload).strip()
        if text:
            return text
    return None
