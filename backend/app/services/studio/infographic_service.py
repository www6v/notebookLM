"""Infographic generation service.

Supports the staged v2 skill-runtime infographic pipeline.
"""

import logging
import re
import uuid
from pathlib import Path

from langfuse import observe, propagate_attributes
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.studio import Infographic
from app.schemas.studio import InfographicStatus
from app.services.obs_storage import upload_file_to_obs
from app.services.source.source_service import (
    build_combined_content_from_sources,
    fetch_sources,
)
from app.services.studio.studio_status_service import (
    clear_generation_error,
    mark_generation_as_error,
)
from agent.run_skill_prompt import SkillWorkflowRequest, run_skill_workflow

logger = logging.getLogger(__name__)

DIRECTION_TO_WORKFLOW_ASPECT = {
    "横向": "landscape",
    "纵向": "portrait",
    "方形": "square",
}
INFOGRAPHIC_V2 = "v2"
SKILL_WORKFLOW_NAME = "baoyu-infographic"
DEFAULT_WORKFLOW_LAYOUT = "bento-grid"
DEFAULT_WORKFLOW_STYLE = "craft-handmade"
LEGACY_VISUAL_STYLE_TO_WORKFLOW_STYLE = {
    "auto": DEFAULT_WORKFLOW_STYLE,
    "hand_drawn": "craft-handmade",
    "cute": "kawaii",
    "professional": "corporate-memphis",
    "science": "technical-schematic",
    "anime": "bold-graphic",
}


def _normalize_workflow_style(visual_style: str | None) -> str:
    """Normalize UI-selected or legacy visual style into a skill style id."""
    if not visual_style:
        return DEFAULT_WORKFLOW_STYLE
    return LEGACY_VISUAL_STYLE_TO_WORKFLOW_STYLE.get(visual_style, visual_style)


def _upload_infographic_image(image_bytes: bytes) -> str:
    """Upload infographic PNG bytes to OSS and return object key."""
    unique_id = uuid.uuid4().hex[:12]
    filename = f"infographics/infographic_{unique_id}.png"
    return upload_file_to_obs(
        file_content=image_bytes,
        filename=filename,
        content_type="image/png",
    )


def _build_v2_workflow_options(infographic: Infographic) -> dict[str, str]:
    """Normalize existing infographic inputs into workflow-friendly options."""
    style = infographic.infographic_style or "标准"
    language = infographic.infographic_language or "简体中文"
    direction = infographic.infographic_direction or "横向"
    visual_style = _normalize_workflow_style(infographic.infographic_visual_style)
    options = {
        "title": infographic.title,
        "infographic_style": style,
        "infographic_language": language,
        "infographic_direction": direction,
        "infographic_visual_style": visual_style,
        "language": language,
        "lang": language,
        "aspect": DIRECTION_TO_WORKFLOW_ASPECT.get(direction, "landscape"),
        "detail_level": style,
        "layout": DEFAULT_WORKFLOW_LAYOUT,
        "style": visual_style,
    }
    custom_prompt = (infographic.infographic_custom_prompt or "").strip()
    if custom_prompt:
        options["infographic_custom_prompt"] = custom_prompt
        options["custom_prompt"] = custom_prompt
    return options


def _build_v2_source_markdown(
    infographic: Infographic,
    combined_content: str,
    workflow_options: dict[str, str],
) -> str:
    """Build the markdown source passed into the staged workflow."""
    lines = [
        f"# {infographic.title}",
        "",
        "## Infographic Request",
        f"- version: {INFOGRAPHIC_V2}",
        f"- language: {workflow_options.get('language', '简体中文')}",
        f"- detail_level: {workflow_options.get('detail_level', '标准')}",
        f"- direction: {infographic.infographic_direction or '横向'}",
        f"- aspect: {workflow_options.get('aspect', 'landscape')}",
        f"- layout: {workflow_options.get('layout', DEFAULT_WORKFLOW_LAYOUT)}",
        f"- style: {workflow_options.get('style', DEFAULT_WORKFLOW_STYLE)}",
        f"- visual_style: {workflow_options.get('infographic_visual_style', DEFAULT_WORKFLOW_STYLE)}",
    ]
    if infographic.infographic_custom_prompt and infographic.infographic_custom_prompt.strip():
        lines.extend(
            [
                "",
                "## Additional Instructions",
                infographic.infographic_custom_prompt.strip(),
            ]
        )
    lines.extend(
        [
            "",
            "## Source Content",
            combined_content or "No source content available.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def _studio_workflow_dir(infographic_id: str) -> Path:
    """Return the local workspace directory for one infographic workflow run."""
    backend_root = Path(__file__).resolve().parents[2]
    return backend_root / "agent" / "infographic" / "studio" / infographic_id


def _read_optional_text(path: Path) -> str | None:
    """Read one text artifact if it exists."""
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _default_suggested_filename(title: str) -> str:
    """Build a stable filename for generated infographic images."""
    cleaned = re.sub(r"[^\w\-]+", "_", (title or "infographic").strip())
    cleaned = cleaned.strip("_") or "infographic"
    return f"{cleaned[:80]}.png"


async def _run_infographic_generation_v2(
    db: AsyncSession,
    infographic: Infographic,
    source_ids: list[str] | None,
) -> Infographic:
    """Run the staged skill-runtime infographic pipeline."""
    sources = await fetch_sources(db, infographic.notebook_id, source_ids)
    combined_content = await build_combined_content_from_sources(sources)
    workflow_options = _build_v2_workflow_options(infographic)

    backend_root = Path(__file__).resolve().parents[2]
    workflow_dir = _studio_workflow_dir(infographic.id)
    workflow_dir.mkdir(parents=True, exist_ok=True)

    source_path = workflow_dir / "source.md"
    source_path.write_text(
        _build_v2_source_markdown(
            infographic=infographic,
            combined_content=combined_content,
            workflow_options=workflow_options,
        ),
        encoding="utf-8",
    )

    results = await run_skill_workflow(
        SkillWorkflowRequest(
            skill_name=SKILL_WORKFLOW_NAME,
            source=str(source_path.relative_to(backend_root)),
            output_dir=str(workflow_dir.relative_to(backend_root)),
            through_stage="image",
            options=workflow_options,
            model=settings.litellm_model,
            temperature=0.3,
            max_completion_tokens=8192,
        ),
        workspace=backend_root,
    )

    image_path = workflow_dir / "infographic.png"
    image_bytes = image_path.read_bytes()
    object_key = _upload_infographic_image(image_bytes)

    infographic.layout_data = {
        "generation_version": INFOGRAPHIC_V2,
        "workflow": SKILL_WORKFLOW_NAME,
        "options": workflow_options,
        "artifacts": {
            "analysis": _read_optional_text(workflow_dir / "analysis.md"),
            "structured_content": _read_optional_text(
                workflow_dir / "structured-content.md"
            ),
            "prompt": _read_optional_text(
                workflow_dir / "prompts" / "infographic.md"
            ),
        },
        "stage_results": [
            {
                "stage": result.stage,
                "output_path": str(result.output_path),
                "summary": result.llm_result.content.strip(),
            }
            for result in results
        ],
    }
    infographic.file_path = object_key
    infographic.suggested_filename = _default_suggested_filename(infographic.title)
    infographic.status = InfographicStatus.READY.value
    clear_generation_error(infographic)
    await db.flush()
    logger.info(
        "Infographic %s ready via v2, file_path=%s",
        infographic.id,
        object_key,
    )
    return infographic


@observe(name="run_infographic_generation_for_existing", as_type="generation")
async def run_infographic_generation_for_existing(
    db: AsyncSession,
    infographic_id: str,
    source_ids: list[str] | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
) -> Infographic:
    """Run infographic generation for an existing pending Infographic record."""
    with propagate_attributes(
        user_id=user_id or "",
        session_id=session_id or infographic_id,
        metadata={"llm": settings.litellm_model},
    ):
        result = await db.execute(
            select(Infographic).where(Infographic.id == infographic_id)
        )
        infographic = result.scalar_one_or_none()
        if infographic is None:
            raise ValueError(f"Infographic not found: {infographic_id}")

        infographic.status = InfographicStatus.PROCESSING.value
        clear_generation_error(infographic)
        await db.flush()

        try:
            return await _run_infographic_generation_v2(
                db,
                infographic,
                source_ids,
            )
        except Exception as exc:
            mark_generation_as_error(
                infographic,
                "infographic generation failed",
                str(exc),
            )
            await db.flush()
            raise
