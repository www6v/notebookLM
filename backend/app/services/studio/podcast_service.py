"""Podcast (audio overview) generation via podcast-generation skill workflow."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from langfuse import observe, propagate_attributes
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.studio import PodcastOverview
from app.schemas.studio import PodcastStatus
from app.services.obs_storage import upload_file_to_obs
from app.services.studio.podcast_script_schema import (
    coerce_podcast_script_payload,
    parse_podcast_script_text,
)
from app.services.source_service import (
    build_combined_content_from_sources,
    fetch_sources,
)
from app.services.studio.studio_status_service import (
    clear_generation_error,
    mark_generation_as_error,
)
from agent.run_skill_prompt import SkillWorkflowRequest, run_skill_workflow

logger = logging.getLogger(__name__)

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_PODCAST_SKILL_WORKFLOW = "podcast-generation"


def _sanitize_text_for_mysql_utf8mb3(text: str) -> str:
    """Strip 4-byte Unicode for utf8mb3 columns."""
    return "".join(ch for ch in text if ord(ch) <= 0xFFFF)


def _safe_filename_stem(name: str) -> str:
    stem = re.sub(r'[<>:"/\\|?*]', "_", name).strip()
    return stem or "podcast"


def _build_podcast_source_markdown(
    *,
    combined: str,
    audio_format: str,
    audio_language: str,
    audio_length: str,
    audio_focus_prompt: str | None,
) -> str:
    """One source file for the skill workflow (inputs + notebook text)."""
    focus = (audio_focus_prompt or "").strip()
    lines = [
        "# Podcast generation inputs",
        "",
        f"- **audio_format**: {audio_format}",
        f"- **audio_language**: {audio_language}",
        f"- **audio_length**: {audio_length}",
    ]
    if focus:
        lines.append(f"- **audio_focus_prompt**: {focus}")
    lines.extend(
        [
            "",
            "## Source material",
            "",
            combined.strip(),
            "",
        ]
    )
    return "\n".join(lines)


@observe(name="run_podcast_generation_for_existing", as_type="generation")
async def run_podcast_generation_for_existing(
    db: AsyncSession,
    podcast_id: str,
    source_ids: list[str] | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
) -> PodcastOverview:
    """Run podcast-generation skill workflow, upload WAV, save transcript."""
    with propagate_attributes(
        user_id=user_id or "",
        session_id=session_id or podcast_id,
        metadata={"llm": settings.litellm_model},
    ):
        result = await db.execute(
            select(PodcastOverview).where(PodcastOverview.id == podcast_id)
        )
        podcast = result.scalar_one_or_none()
        if podcast is None:
            raise ValueError(f"Podcast overview not found: {podcast_id}")

        podcast.status = PodcastStatus.PROCESSING.value
        clear_generation_error(podcast)
        await db.flush()

        workflow_dir = (
            _BACKEND_ROOT
            / "agent"
            / "skills"
            / "podcast-generation"
            / "studio"
            / podcast_id
        )
        workflow_dir.mkdir(parents=True, exist_ok=True)
        source_path = workflow_dir / "source.md"
        script_path = workflow_dir / "script.json"
        wav_path = workflow_dir / "podcast.wav"
        transcript_path = workflow_dir / "transcript.md"

        audio_format = podcast.audio_format or "deep_dive"
        audio_language = podcast.audio_language or "简体中文"
        audio_length = podcast.audio_length or "default"
        focus_raw = podcast.audio_focus_prompt

        try:
            sources = await fetch_sources(
                db, podcast.notebook_id, source_ids
            )
            combined = await build_combined_content_from_sources(sources)
            if not combined.strip():
                raise ValueError(
                    "No usable content from selected sources for podcast."
                )

            source_path.write_text(
                _build_podcast_source_markdown(
                    combined=combined,
                    audio_format=audio_format,
                    audio_language=audio_language,
                    audio_length=audio_length,
                    audio_focus_prompt=focus_raw,
                ),
                encoding="utf-8",
            )

            workflow_options = {
                "audio_format": audio_format,
                "audio_language": audio_language,
                "audio_length": audio_length,
                "audio_focus_prompt": focus_raw or "",
            }

            await run_skill_workflow(
                SkillWorkflowRequest(
                    skill_name=_PODCAST_SKILL_WORKFLOW,
                    source=str(source_path.relative_to(_BACKEND_ROOT)),
                    output_dir=str(workflow_dir.relative_to(_BACKEND_ROOT)),
                    through_stage="audio",
                    options=workflow_options,
                    model=settings.litellm_model,
                    temperature=0.4,
                    max_completion_tokens=8192,
                ),
                workspace=_BACKEND_ROOT,
            )

            script_data = parse_podcast_script_text(
                script_path.read_text(encoding="utf-8")
            )
            script_payload = coerce_podcast_script_payload(script_data)
            title_raw = script_payload["title"]
            podcast.title = _sanitize_text_for_mysql_utf8mb3(title_raw)[:255]
            stem = _safe_filename_stem(podcast.title)
            podcast.suggested_filename = f"{stem}.wav"

            transcript_text = transcript_path.read_text(encoding="utf-8")
            podcast.transcript = _sanitize_text_for_mysql_utf8mb3(transcript_text)

            wav_bytes = wav_path.read_bytes()
            object_key = upload_file_to_obs(
                file_content=wav_bytes,
                filename=f"podcasts/podcast_{podcast_id}.wav",
                content_type="audio/wav",
            )
            podcast.file_path = object_key
            podcast.status = PodcastStatus.READY.value
            clear_generation_error(podcast)
            await db.flush()
            logger.info(
                "Podcast %s ready, file_path=%s",
                podcast_id,
                object_key,
            )
            return podcast
        except Exception as exc:
            mark_generation_as_error(
                podcast,
                "podcast generation failed",
                str(exc),
            )
            await db.flush()
            logger.exception("Podcast %s failed: %s", podcast_id, exc)
            raise
