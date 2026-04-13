"""Parse and normalize podcast script JSON for TTS (shared by workflow + API)."""

from __future__ import annotations

import json


def strip_json_fence(content: str) -> str:
    """Remove optional markdown code fences from model output."""
    text = content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.rsplit("```", 1)[0]
    return text.strip()


def parse_podcast_script_text(content: str) -> dict:
    """Parse script JSON from file or LLM string."""
    raw = strip_json_fence(content)
    return json.loads(raw)


def coerce_podcast_script_payload(data: dict) -> dict:
    """Ensure script dict is valid for generate.py."""
    if "lines" not in data or not isinstance(data["lines"], list):
        raise ValueError("Script JSON missing 'lines' array")
    loc = data.get("locale", "zh")
    if loc not in ("en", "zh"):
        loc = "zh"
    lines_out = []
    for item in data["lines"]:
        if not isinstance(item, dict):
            continue
        sp = item.get("speaker", "male")
        if sp not in ("male", "female"):
            sp = "male"
        para = item.get("paragraph", "")
        if not isinstance(para, str):
            para = str(para)
        para = para.strip()
        if para:
            lines_out.append({"speaker": sp, "paragraph": para})
    if not lines_out:
        raise ValueError("No non-empty dialogue lines in script")
    title = data.get("title", "Podcast")
    if not isinstance(title, str):
        title = str(title)
    return {
        "title": title.strip() or "Podcast",
        "locale": loc,
        "lines": lines_out,
    }
