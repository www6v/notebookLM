"""Deterministic podcast script normalization and audio synthesis."""

from __future__ import annotations

import asyncio
import importlib.util
import json
from pathlib import Path

from app.services.podcast_script_schema import (
    coerce_podcast_script_payload,
    parse_podcast_script_text,
)


def finalize_podcast_script_json_file(path: Path) -> None:
    """Parse, coerce, and rewrite script JSON before TTS."""
    if not path.exists():
        raise FileNotFoundError(
            f"Podcast script file missing: {path}"
        )
    text = path.read_text(encoding="utf-8")
    data = parse_podcast_script_text(text)
    normalized = coerce_podcast_script_payload(data)
    path.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_podcast_generate_module(workspace: Path):
    """Load podcast-generation generate.py from workspace."""
    script_path = (
        workspace.resolve()
        / "agent"
        / "skills"
        / "podcast-generation"
        / "scripts"
        / "generate.py"
    )
    if not script_path.is_file():
        raise FileNotFoundError(
            f"Podcast generate.py not found: {script_path}"
        )
    spec = importlib.util.spec_from_file_location(
        "skill_runtime_podcast_generate",
        script_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load podcast generate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


async def run_podcast_audio_generation(
    workspace: Path,
    *,
    script_path: Path,
    wav_path: Path,
    transcript_path: Path,
) -> None:
    """Run Qwen TTS via the skill script (SKILL.md Step 3)."""
    mod = load_podcast_generate_module(workspace)
    await asyncio.to_thread(
        mod.generate_podcast,
        str(script_path.resolve()),
        str(wav_path.resolve()),
        str(transcript_path.resolve()),
    )
