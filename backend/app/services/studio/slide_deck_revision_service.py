"""Apply per-slide prompt revisions via qwen-image-edit and re-merge PDF/PPTX."""

from __future__ import annotations

import asyncio
import copy
import logging
import re
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from notebooklm_shared.models.studio import SlideDeck
from app.schemas.studio import SlideDeckStatus
from app.services.infra.obs_storage import download_file_from_obs
from app.services.studio.qwen_image_edit import edit_image_with_instruction
from app.services.studio.slide_service import (
    SLIDE_DECK_V2,
    _build_slide_image_variants,
    _collect_prompt_artifacts,
    _merge_slide_deck_outputs,
    _parse_outline_slides,
    _read_optional_text,
    _studio_workflow_dir,
    _upload_slide_deck_pdf,
)
from app.services.studio.studio_status_service import clear_generation_error

logger = logging.getLogger(__name__)

_SLIDE_FILE_PATTERN = re.compile(
    r"^\d+-slide-.*\.(png|jpg|jpeg)$",
    re.IGNORECASE,
)


def _slide_png_stem_for_index(images: list[dict], index: int) -> str:
    """Return basename (no dir) for one slide PNG, matching merge script sort."""
    if 0 <= index < len(images):
        name = images[index].get("filename")
        if isinstance(name, str) and name.strip():
            return Path(name.strip()).name
    return f"{index + 1:02d}-slide-{index + 1}.png"


def _clear_slide_png_files(workflow_dir: Path) -> None:
    """Remove prior slide page images so merge scripts see exactly one set."""
    if not workflow_dir.is_dir():
        return
    for path in workflow_dir.iterdir():
        if path.is_file() and _SLIDE_FILE_PATTERN.match(path.name):
            try:
                path.unlink()
            except OSError:
                logger.warning("Could not remove old slide file %s", path)


def _slides_meta_for_variants(
    slides_data: dict,
    workflow_dir: Path,
    slide_count: int,
) -> list[dict]:
    """Build slides list for variant titles (reuse DB outline when possible)."""
    raw_slides = slides_data.get("slides")
    if isinstance(raw_slides, list) and len(raw_slides) >= slide_count:
        return [copy.deepcopy(s) for s in raw_slides[:slide_count]]

    outline_path = workflow_dir / "outline.md"
    outline_text = slides_data.get("artifacts", {}).get("outline")
    if not isinstance(outline_text, str) or not outline_text.strip():
        outline_text = _read_optional_text(outline_path)
    parsed = _parse_outline_slides(outline_text)
    if len(parsed) >= slide_count:
        return parsed[:slide_count]
    return [{"title": f"Slide {i + 1}"} for i in range(slide_count)]


async def run_slide_deck_prompt_revision(
    db: AsyncSession,
    slide_deck_id: str,
    edits: list[tuple[int, str]],
) -> SlideDeck:
    """Rebuild slide deck artifacts; only listed indices pass through image edit."""
    result = await db.execute(select(SlideDeck).where(SlideDeck.id == slide_deck_id))
    slide = result.scalar_one_or_none()
    if slide is None:
        raise ValueError("Slide deck not found")

    # API sets status to processing before enqueueing this task; accept that
    # state here. READY is allowed for direct callers (e.g. tests).
    if slide.status not in (
        SlideDeckStatus.READY.value,
        SlideDeckStatus.PROCESSING.value,
    ):
        raise ValueError(
            "Slide deck cannot be revised in its current state "
            f"(status={slide.status!r})"
        )

    sd = slide.slides_data
    if not isinstance(sd, dict):
        raise ValueError("Slide deck has no slides_data")

    if sd.get("generation_version") != SLIDE_DECK_V2:
        raise ValueError("Slide deck revision only supports v2 generation")

    artifacts = sd.get("artifacts")
    if not isinstance(artifacts, dict):
        raise ValueError("Slide deck has no artifacts")

    images = artifacts.get("images")
    if not isinstance(images, list) or not images:
        raise ValueError("Slide deck has no slide images to revise")

    n = len(images)
    edit_map = {idx: (prompt or "").strip() for idx, prompt in edits}
    for idx, prompt in edit_map.items():
        if idx < 0 or idx >= n:
            raise ValueError(f"slide_index {idx} is out of range (0..{n - 1})")
        if not prompt:
            raise ValueError(f"Empty prompt for slide_index {idx}")

    workflow_dir = _studio_workflow_dir(slide_deck_id)
    workflow_dir.mkdir(parents=True, exist_ok=True)
    _clear_slide_png_files(workflow_dir)

    for index in range(n):
        row = images[index]
        if not isinstance(row, dict):
            raise ValueError(f"Invalid image metadata at index {index}")
        variants = row.get("variants")
        if not isinstance(variants, dict):
            raise ValueError(f"Missing variants at index {index}")
        export = variants.get("export")
        if not isinstance(export, dict):
            raise ValueError(f"Missing export variant at index {index}")
        object_key = export.get("object_key")
        if not isinstance(object_key, str) or not object_key.strip():
            raise ValueError(f"Missing object_key for slide index {index}")

        png_bytes = await asyncio.to_thread(
            download_file_from_obs,
            object_key.strip(),
        )
        if index in edit_map:
            edited = await edit_image_with_instruction(
                png_bytes,
                edit_map[index],
                title=f"slide-{index + 1}",
            )
            if edited is None:
                raise RuntimeError(
                    f"Image edit failed for slide index {index}",
                )
            png_bytes = edited

        out_name = _slide_png_stem_for_index(images, index)
        out_path = workflow_dir / out_name
        out_path.write_bytes(png_bytes)

    pdf_path, pptx_path, merge_logs = await _merge_slide_deck_outputs(workflow_dir)
    new_pdf_key = _upload_slide_deck_pdf(pdf_path.read_bytes())

    slides_for_variants = _slides_meta_for_variants(sd, workflow_dir, n)
    image_artifacts = await asyncio.to_thread(
        _build_slide_image_variants,
        workflow_dir,
        slides_for_variants,
    )

    new_slides_data = copy.deepcopy(sd)
    new_artifacts = new_slides_data.setdefault("artifacts", {})
    if not isinstance(new_artifacts, dict):
        new_slides_data["artifacts"] = {}
        new_artifacts = new_slides_data["artifacts"]

    new_artifacts["images"] = image_artifacts
    new_artifacts["pdf"] = str(pdf_path)
    new_artifacts["pptx"] = str(pptx_path)
    new_artifacts["merge_logs"] = merge_logs
    prompts_dir = workflow_dir / "prompts"
    new_artifacts["prompts"] = _collect_prompt_artifacts(prompts_dir)

    slide.slides_data = new_slides_data
    slide.file_path = new_pdf_key
    slide.status = SlideDeckStatus.READY.value
    clear_generation_error(slide)
    await db.flush()

    logger.info(
        "Slide deck %s revised (%s edited page(s)), new pdf key=%s",
        slide_deck_id,
        len(edit_map),
        new_pdf_key,
    )
    return slide
