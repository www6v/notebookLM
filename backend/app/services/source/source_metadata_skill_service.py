"""Generate source metadata through the skill runtime."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from json_repair import loads as json_repair_loads
from sqlalchemy.ext.asyncio import AsyncSession

from agent.skill_runtime import OpenAISkillExecutor, SkillLoader, SkillPromptBuilder
from notebooklm_shared.config import settings
from notebooklm_shared.models.source import Source

logger = logging.getLogger(__name__)

_SKILL_NAME = "source-metadata"
_MAX_CONTENT_CHARS = 16000
_INVALID_FILENAME_CHARS = re.compile(r"[\\/:*?\"<>|]+")
_EXT_RE = re.compile(r"(\.[A-Za-z0-9]{1,10})$")
_DEFAULT_TAGS = ("source", "analysis", "summary", "insights", "reference")


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _parse_json_payload(raw: str) -> dict:
    text = (raw or "").strip()
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        try:
            parsed = json_repair_loads(text)
        except Exception:
            return {}
    return parsed if isinstance(parsed, dict) else {}


def _extract_extension(filename: str | None) -> str:
    if not filename:
        return ""
    match = _EXT_RE.search(filename.strip())
    if not match:
        return ""
    return match.group(1)


def _normalize_filename_stem(stem: str, fallback: str) -> str:
    cleaned = _INVALID_FILENAME_CHARS.sub(" ", (stem or "").strip())
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    cleaned = cleaned[:80].strip()
    return cleaned or fallback


def _normalize_tags(raw_tags: object) -> list[str]:
    candidates: list[str]
    if isinstance(raw_tags, list):
        candidates = [str(item) for item in raw_tags]
    elif isinstance(raw_tags, str):
        candidates = [item.strip() for item in raw_tags.split(",")]
    else:
        candidates = []

    tags: list[str] = []
    for tag in candidates:
        normalized = re.sub(r"\s+", " ", tag).strip(" ,")
        if not normalized:
            continue
        if normalized.lower() in {item.lower() for item in tags}:
            continue
        tags.append(normalized[:32])
        if len(tags) == 5:
            return tags

    for fallback in _DEFAULT_TAGS:
        if fallback.lower() not in {item.lower() for item in tags}:
            tags.append(fallback)
        if len(tags) == 5:
            break
    return tags[:5]


def _normalize_summary(raw_summary: object) -> str | None:
    if not isinstance(raw_summary, str):
        return None
    text = re.sub(r"\s+", " ", raw_summary).strip()
    if not text:
        return None
    return text[:2000]


def _build_task_payload_from_inputs(
    content: str,
    original_title: str,
    source_type: str,
) -> str:
    body = (content or "").strip()
    if len(body) > _MAX_CONTENT_CHARS:
        body = body[:_MAX_CONTENT_CHARS]
    return (
        "Generate metadata for this uploaded source and return strict JSON only.\n\n"
        f"original_filename: {original_title}\n"
        f"source_type: {source_type}\n"
        "content_language_hint: auto-detect from content\n"
        "content:\n"
        f"{body}\n"
    )


def _build_task_payload(source: Source) -> str:
    return _build_task_payload_from_inputs(
        source.raw_content or "",
        source.title,
        source.type,
    )


def apply_source_metadata_payload(source: Source, payload: dict) -> None:
    """Apply parsed skill JSON to ``source`` (no DB flush)."""
    extension = _extract_extension(source.title)
    fallback_stem = _normalize_filename_stem(
        source.title.rsplit(".", 1)[0] if extension else source.title,
        fallback="Uploaded Source",
    )
    stem = _normalize_filename_stem(
        str(payload.get("filename") or ""),
        fallback=fallback_stem,
    )
    source.title = f"{stem}{extension}" if extension else stem
    source.tags = _normalize_tags(payload.get("tags"))

    summary = _normalize_summary(payload.get("summary"))
    if summary is not None:
        source.summary = summary


async def run_source_metadata_skill(
    content: str,
    original_title: str,
    source_type: str,
    *,
    log_label: str | None = None,
) -> dict | None:
    """Run source-metadata skill LLM only; returns parsed payload or None."""
    stripped = (content or "").strip()
    if not stripped:
        return None
    label = log_label or "unknown"
    if not settings.litellm_model:
        logger.warning(
            "Skip source metadata skill for %s: LITELLM_MODEL is not set",
            label,
        )
        return None

    workspace = _backend_root()
    loader = SkillLoader(workspace=workspace)
    skill = loader.get_skill(_SKILL_NAME)
    if skill is None:
        logger.warning(
            "Skip source metadata skill for %s: skill `%s` not found",
            label,
            _SKILL_NAME,
        )
        return None

    executor = OpenAISkillExecutor(
        workspace=workspace,
        loader=loader,
        prompt_builder=SkillPromptBuilder(workspace=workspace),
    )

    result = await executor.run(
        skill_name=_SKILL_NAME,
        task=_build_task_payload_from_inputs(
            stripped,
            original_title,
            source_type,
        ),
        options={},
        attachments=[],
        model=settings.litellm_model,
        selected_skills=[_SKILL_NAME],
        temperature=0.2,
        max_completion_tokens=1200,
    )
    payload = _parse_json_payload(result.content)
    if not payload:
        logger.warning(
            "Source metadata skill returned invalid payload for %s",
            label,
        )
        return None
    return payload


async def enrich_source_metadata_with_skill(
    db: AsyncSession,
    source: Source,
) -> None:
    """Populate source title/summary/tags using the source-metadata skill."""
    payload = await run_source_metadata_skill(
        source.raw_content or "",
        source.title,
        source.type,
        log_label=str(source.id),
    )
    if not payload:
        return
    apply_source_metadata_payload(source, payload)
    await db.flush()
