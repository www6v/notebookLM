"""Slide Deck API routes."""

import asyncio
import logging
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from notebooklm_shared.database import get_db
from notebooklm_shared.models.notebook import Notebook
from app.ratelimit import (
    GenerationKind,
    acquire_generation_rate_limit_slot,
    release_generation_rate_limit_on_db_failure,
)
from notebooklm_shared.models.studio import SlideDeck
from notebooklm_shared.models.user import User
from app.schemas.studio import (
    SlideDeckCreate,
    SlideDeckResponse,
    SlideDeckReviseRequest,
    SlideDeckStatus,
    SlideDeckUpdate,
)
from app.services.infra.obs_storage import (
    download_file_from_obs,
    generate_presigned_url,
)
from app.services.studio.slide_service import (
    build_slide_pptx_from_pdf_bytes,
)
from app.services.studio.studio_storage_cleanup import (
    delete_studio_objects_best_effort,
    slide_deck_storage_keys,
)
from app.services.studio.studio_status_service import (
    clear_generation_error,
    reconcile_stale_generation,
    reconcile_stale_generations,
)
from app.services.task_event_service import publish_task_event
from app.tasks.studio_tasks import (
    generate_slide_deck_task,
    revise_slide_deck_task,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["studio"])
THUMBNAIL_MAX_WIDTH = 320
PREVIEW_MAX_WIDTH = 1280
IMAGE_URL_EXPIRATION_SECONDS = 3600
INVALID_FILENAME_CHARS = str.maketrans(
    {char: "_" for char in '<>:"/\\|?*'}
)


def _slide_workflow_dir(slide_id: str) -> Path:
    """Return the local workflow directory for one slide deck."""
    backend_root = Path(__file__).resolve().parents[3]
    return backend_root / "agent" / "slide_deck" / "studio" / slide_id


def _build_slide_pdf_display_name(slide: SlideDeck) -> str:
    """Build a user-facing PDF filename for one slide deck."""
    display_name = slide.suggested_filename or slide.title or "slides"
    display_name = display_name.replace('"', "").strip()
    if display_name.lower().endswith(".pptx"):
        display_name = display_name[:-5]
    if not display_name.lower().endswith(".pdf"):
        display_name = f"{display_name}.pdf"
    return display_name or "slides.pdf"


def _normalize_slide_pdf_filename(
    requested_filename: str | None, fallback_name: str
) -> str:
    """Normalize an optional user-supplied PDF filename."""
    if not requested_filename:
        return fallback_name
    normalized = (
        requested_filename.strip()
        .replace("\r", "")
        .replace("\n", "")
        .translate(INVALID_FILENAME_CHARS)
    )
    if normalized.lower().endswith(".pptx"):
        normalized = normalized[:-5]
    if not normalized.lower().endswith(".pdf"):
        normalized = f"{normalized}.pdf"
    return normalized or fallback_name


def _build_content_disposition(
    filename: str, disposition_type: str = "inline"
) -> str:
    """Build a RFC 5987-compatible Content-Disposition header value."""
    ascii_name = filename.encode("ascii", "ignore").decode("ascii").strip()
    ascii_name = ascii_name.replace('"', "") or "slide-deck.pdf"
    utf8_quoted = quote(filename, safe="")
    return (
        f'{disposition_type}; filename="{ascii_name}"; '
        f"filename*=UTF-8''{utf8_quoted}"
    )


def _get_slide_image_paths(slide: SlideDeck) -> list[Path]:
    """Resolve generated slide images from the workflow directory."""
    workflow_dir = _slide_workflow_dir(slide.id)
    if not workflow_dir.exists():
        return []
    return sorted(workflow_dir.glob("*-slide-*.png"))


def _resize_slide_image(
    image_path: Path,
    *,
    max_width: int,
    format_name: str,
    content_type: str,
    quality: int,
) -> tuple[bytes, str]:
    """Build one resized slide image variant from a local file."""
    image_bytes = image_path.read_bytes()
    from PIL import Image

    with Image.open(BytesIO(image_bytes)) as image:
        if image.width <= max_width and content_type == "image/png":
            return image_bytes, "image/png"
        thumbnail = image.copy()
        thumbnail.thumbnail((max_width, max_width * 4))
        buffer = BytesIO()
        thumbnail.save(
            buffer,
            format=format_name,
            quality=quality,
            method=6,
        )
        return buffer.getvalue(), content_type


def _normalize_variant(variant: str) -> str | None:
    """Normalize client variant aliases into one supported image tier."""
    normalized = (variant or "").strip().lower()
    if normalized == "full":
        return "export"
    if normalized in {"thumb", "preview", "export"}:
        return normalized
    return None


def _get_slide_image_entries(slide: SlideDeck) -> list[dict]:
    """Read structured slide image metadata, falling back to legacy rows."""
    raw = slide.slides_data if isinstance(slide.slides_data, dict) else {}
    artifacts = raw.get("artifacts") if isinstance(raw, dict) else {}
    images = artifacts.get("images") if isinstance(artifacts, dict) else None
    slides_meta = raw.get("slides") if isinstance(raw, dict) else None
    slide_rows = slides_meta if isinstance(slides_meta, list) else []
    if isinstance(images, list) and images:
        normalized: list[dict] = []
        for index, row in enumerate(images):
            if not isinstance(row, dict):
                continue
            title = row.get("title")
            if not isinstance(title, str) or not title.strip():
                title = f"Slide {index + 1}"
                if index < len(slide_rows):
                    candidate = slide_rows[index]
                    if isinstance(candidate, dict):
                        candidate_title = candidate.get("title")
                        if isinstance(candidate_title, str) and candidate_title.strip():
                            title = candidate_title.strip()
            variants = row.get("variants")
            normalized_variants = variants if isinstance(variants, dict) else {}
            legacy_path = row.get("path")
            legacy_name = row.get("name") or row.get("filename")
            if not normalized_variants:
                if isinstance(legacy_path, str) and legacy_path.strip():
                    normalized_variants = {
                        "export": {
                            "filename": legacy_name or Path(legacy_path).name,
                            "content_type": "image/png",
                            "local_path": legacy_path,
                        }
                    }
            normalized.append(
                {
                    "index": row.get("index", index),
                    "slide_number": row.get("slide_number", index + 1),
                    "title": title,
                    "filename": (
                        row.get("filename")
                        or legacy_name
                        or f"slide-{index + 1}.png"
                    ),
                    "variants": normalized_variants,
                }
            )
        if normalized:
            return normalized

    legacy_entries: list[dict] = []
    for index, image_path in enumerate(_get_slide_image_paths(slide)):
        title = f"Slide {index + 1}"
        if index < len(slide_rows):
            candidate = slide_rows[index]
            if isinstance(candidate, dict):
                candidate_title = candidate.get("title")
                if isinstance(candidate_title, str) and candidate_title.strip():
                    title = candidate_title.strip()
        legacy_entries.append(
            {
                "index": index,
                "slide_number": index + 1,
                "title": title,
                "filename": image_path.name,
                "variants": {
                    "export": {
                        "filename": image_path.name,
                        "content_type": "image/png",
                        "local_path": str(image_path),
                    }
                },
            }
        )
    return legacy_entries


def _get_variant_asset(entry: dict, variant: str) -> dict | None:
    """Resolve one image variant from structured metadata."""
    variants = entry.get("variants")
    if not isinstance(variants, dict):
        return None
    asset = variants.get(variant)
    if isinstance(asset, dict):
        return asset
    if variant in {"thumb", "preview"}:
        export_asset = variants.get("export")
        if isinstance(export_asset, dict):
            return export_asset
    return None


def _build_variant_urls(slide: SlideDeck, entry: dict, variant: str) -> dict:
    """Build preview URLs for one variant."""
    asset = _get_variant_asset(entry, variant) or {}
    object_key = asset.get("object_key")
    presigned_url = None
    if isinstance(object_key, str) and object_key.strip():
        presigned_url = generate_presigned_url(
            object_key,
            expiration=IMAGE_URL_EXPIRATION_SECONDS,
        )
    proxy_url = (
        f"/api/slides/{slide.id}/images/{entry['index']}?variant={variant}"
    )
    fallback_name = entry.get("filename") or f"slide-{entry['index'] + 1}"
    return {
        "filename": asset.get("filename") or fallback_name,
        "content_type": asset.get("content_type") or "image/png",
        "width": asset.get("width"),
        "height": asset.get("height"),
        "object_key": object_key,
        "url": presigned_url,
        "proxy_url": proxy_url,
        "preferred_url": presigned_url or proxy_url,
    }


def _build_slide_image_manifest(slide: SlideDeck) -> dict:
    """Return one slide image manifest for frontend preview loading."""
    entries = _get_slide_image_entries(slide)
    images: list[dict] = []
    for entry in entries:
        images.append(
            {
                "index": entry["index"],
                "slide_number": entry.get("slide_number", entry["index"] + 1),
                "title": entry.get("title") or f"Slide {entry['index'] + 1}",
                "filename": entry.get("filename"),
                "variants": {
                    variant: _build_variant_urls(slide, entry, variant)
                    for variant in ("thumb", "preview", "export")
                },
            }
        )
    return {
        "slide_id": slide.id,
        "image_count": len(images),
        "images": images,
        "cache_ttl_seconds": IMAGE_URL_EXPIRATION_SECONDS,
    }


def _load_slide_variant_bytes(asset: dict, variant: str) -> tuple[bytes, str, str]:
    """Load bytes for one slide image variant from storage or local fallback."""
    object_key = asset.get("object_key")
    if isinstance(object_key, str) and object_key.strip():
        content_type = asset.get("content_type") or "application/octet-stream"
        filename = asset.get("filename") or "slide-image"
        return download_file_from_obs(object_key), content_type, filename

    local_path_value = asset.get("local_path")
    if not isinstance(local_path_value, str) or not local_path_value.strip():
        raise FileNotFoundError("Slide image asset path is missing")
    image_path = Path(local_path_value)
    if variant == "thumb":
        image_bytes, content_type = _resize_slide_image(
            image_path,
            max_width=THUMBNAIL_MAX_WIDTH,
            format_name="WEBP",
            content_type="image/webp",
            quality=78,
        )
        return image_bytes, content_type, f"{image_path.stem}-thumb.webp"
    if variant == "preview":
        image_bytes, content_type = _resize_slide_image(
            image_path,
            max_width=PREVIEW_MAX_WIDTH,
            format_name="WEBP",
            content_type="image/webp",
            quality=85,
        )
        return image_bytes, content_type, f"{image_path.stem}-preview.webp"
    return image_path.read_bytes(), asset.get("content_type") or "image/png", (
        asset.get("filename") or image_path.name
    )


def _build_media_headers(
    *,
    display_name: str,
    ascii_name: str,
    etag_seed: str,
) -> dict[str, str]:
    """Build HTTP headers shared by slide media responses."""
    utf8_quoted = quote(display_name.replace('"', ""), safe="")
    content_disposition = (
        f'inline; filename="{ascii_name}"; filename*=UTF-8\'\'{utf8_quoted}'
    )
    return {
        "Content-Disposition": content_disposition,
        "Cache-Control": "private, max-age=3600",
        "ETag": f'W/"{etag_seed}"',
    }


async def _verify_notebook_access(
    db: AsyncSession, notebook_id: str, user_id: str
):
    """Verify the user has access to the notebook."""
    result = await db.execute(
        select(Notebook).where(
            Notebook.id == notebook_id, Notebook.user_id == user_id
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        )


async def _get_slide(
    db: AsyncSession, slide_id: str, user_id: str
) -> SlideDeck:
    """Get a slide deck and verify user access."""
    result = await db.execute(
        select(SlideDeck)
        .join(Notebook, SlideDeck.notebook_id == Notebook.id)
        .where(SlideDeck.id == slide_id, Notebook.user_id == user_id)
    )
    slide = result.scalar_one_or_none()
    if slide is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slide deck not found",
        )
    return slide


@router.post(
    "/api/notebooks/{notebook_id}/slides",
    response_model=SlideDeckResponse,
    status_code=202,
)
async def generate_slides(
    notebook_id: str,
    body: SlideDeckCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a pending slide deck and run generation in background. Returns 202."""
    await _verify_notebook_access(db, notebook_id, user.id)
    rl_redis, acquired, slide_daily, _ = await acquire_generation_rate_limit_slot(
        db,
        user_id=user.id,
        kind=GenerationKind.SLIDE_DECK,
        notebook_id=notebook_id,
        source_ids=body.source_ids,
        artifact_id=None,
        user_role=user.role,
    )
    try:
        source_count = len(body.source_ids) if body.source_ids else 0
        slide_deck = SlideDeck(
            notebook_id=notebook_id,
            title=body.title,
            theme=body.theme,
            slides_data=None,
            status=SlideDeckStatus.PENDING.value,
            error_message=None,
            file_path=None,
            slide_style=body.slide_style or "blueprint",
            slide_audience=body.slide_audience or "general",
            slide_language=body.slide_language or "简体中文",
            slide_duration=body.slide_duration or "default",
            slide_custom_prompt=body.slide_custom_prompt,
            source_count=source_count if source_count > 0 else None,
        )
        db.add(slide_deck)
        await db.flush()
        await db.refresh(slide_deck)
        await db.commit()
    except Exception:
        await db.rollback()
        await release_generation_rate_limit_on_db_failure(
            rl_redis,
            acquired,
            user_id=user.id,
            daily_slide_reserved=slide_daily,
            daily_deep_research_reserved=False,
        )
        raise
    finally:
        await rl_redis.aclose()

    await publish_task_event("slide", slide_deck.id, slide_deck.status)
    generate_slide_deck_task.delay(
        slide_deck.id,
        body.source_ids,
        body.focus_topic,
    )
    return SlideDeckResponse.model_validate(slide_deck)


@router.get(
    "/api/notebooks/{notebook_id}/slides",
    response_model=list[SlideDeckResponse],
)
async def list_slides(
    notebook_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List slide decks in a notebook."""
    await _verify_notebook_access(db, notebook_id, user.id)
    result = await db.execute(
        select(SlideDeck)
        .where(SlideDeck.notebook_id == notebook_id)
        .order_by(SlideDeck.created_at.desc())
    )
    slide_decks = result.scalars().all()
    if reconcile_stale_generations(slide_decks):
        await db.flush()
    return [
        SlideDeckResponse.model_validate(s)
        for s in slide_decks
    ]


@router.get("/api/slides/{slide_id}", response_model=SlideDeckResponse)
async def get_slide(
    slide_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a slide deck by ID."""
    slide = await _get_slide(db, slide_id, user.id)
    if reconcile_stale_generation(slide):
        await db.flush()
    return SlideDeckResponse.model_validate(slide)


@router.get("/api/slides/{slide_id}/images-manifest")
async def get_slide_images_manifest(
    slide_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return preview metadata for all slide image variants."""
    slide = await _get_slide(db, slide_id, user.id)
    manifest = _build_slide_image_manifest(slide)
    if manifest["image_count"] < 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slide images not available for this slide deck",
        )
    return manifest


@router.get("/api/slides/{slide_id}/pdf-url")
async def get_slide_pdf_url(
    slide_id: str,
    download: bool = False,
    filename: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a presigned URL for the slide deck PDF stored in OSS."""
    slide = await _get_slide(db, slide_id, user.id)
    if not slide.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF not available for this slide deck",
        )
    display_name = _normalize_slide_pdf_filename(
        filename,
        _build_slide_pdf_display_name(slide),
    )
    content_disposition = _build_content_disposition(
        display_name,
        "attachment" if download else "inline",
    )
    url = generate_presigned_url(
        slide.file_path,
        expiration=3600,
        response_content_disposition=content_disposition,
    )
    return {"url": url}


@router.get("/api/slides/{slide_id}/images/{image_index}/url")
async def get_slide_image_url(
    slide_id: str,
    image_index: int,
    variant: str = "preview",
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return a presigned or proxy URL for one slide image variant."""
    slide = await _get_slide(db, slide_id, user.id)
    normalized_variant = _normalize_variant(variant)
    if normalized_variant is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid slide image variant",
        )
    entries = _get_slide_image_entries(slide)
    if image_index < 0 or image_index >= len(entries):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slide image not found",
        )
    entry = entries[image_index]
    return _build_variant_urls(slide, entry, normalized_variant)


@router.get("/api/slides/{slide_id}/pdf")
async def get_slide_pdf(
    slide_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Stream the slide deck PDF through the API (same-origin, avoids storage CORS)."""
    slide = await _get_slide(db, slide_id, user.id)
    if not slide.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF not available for this slide deck",
        )
    try:
        pdf_bytes = await asyncio.to_thread(
            download_file_from_obs,
            slide.file_path,
        )
    except RuntimeError as exc:
        logger.exception("Slide PDF download failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to load slide PDF from storage",
        ) from exc
    content_disposition = _build_content_disposition(
        _build_slide_pdf_display_name(slide)
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": content_disposition,
            "Cache-Control": "private, max-age=300",
        },
    )


@router.get("/api/slides/{slide_id}/images/{image_index}")
async def get_slide_image(
    slide_id: str,
    image_index: int,
    variant: str = "preview",
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Stream one generated slide image through the API."""
    slide = await _get_slide(db, slide_id, user.id)
    normalized_variant = _normalize_variant(variant)
    if normalized_variant is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid slide image variant",
        )
    entries = _get_slide_image_entries(slide)
    if not entries:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slide images not available for this slide deck",
        )
    if image_index < 0 or image_index >= len(entries):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slide image not found",
        )
    entry = entries[image_index]
    asset = _get_variant_asset(entry, normalized_variant)
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slide image variant not available",
        )
    try:
        image_bytes, media_type, filename = await asyncio.to_thread(
            _load_slide_variant_bytes,
            asset,
            normalized_variant,
        )
    except OSError as exc:
        logger.exception("Slide image load failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load slide image",
        ) from exc
    except Exception as exc:
        logger.exception("Slide image resize failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process slide image",
        ) from exc
    display_base = (
        f"{slide.suggested_filename or slide.title or 'slides'}"
        f"-{image_index + 1}-{normalized_variant}"
    )
    suffix = Path(filename).suffix or ".png"
    display_name = f"{display_base}{suffix}"
    ascii_name = f"slide-image{suffix}"
    etag_seed = (
        str(asset.get("object_key"))
        if asset.get("object_key")
        else f"{asset.get('local_path')}:{normalized_variant}"
    )
    return Response(
        content=image_bytes,
        media_type=media_type,
        headers=_build_media_headers(
            display_name=display_name,
            ascii_name=ascii_name,
            etag_seed=etag_seed,
        ),
    )


@router.get("/api/slides/{slide_id}/pptx")
async def get_slide_pptx(
    slide_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Build a .pptx from the stored slide PDF (one image per page)."""
    slide = await _get_slide(db, slide_id, user.id)
    if not slide.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF not available for this slide deck",
        )
    try:
        pdf_bytes = await asyncio.to_thread(
            download_file_from_obs,
            slide.file_path,
        )
    except RuntimeError as exc:
        logger.exception("Slide PPTX: PDF load failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to load slide PDF from storage",
        ) from exc
    try:
        pptx_bytes = await asyncio.to_thread(
            build_slide_pptx_from_pdf_bytes,
            pdf_bytes,
        )
    except Exception as exc:
        logger.exception("Slide PPTX conversion failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to build PowerPoint file",
        ) from exc
    display_base = (slide.suggested_filename or slide.title or "slides").replace(
        '"', ""
    )
    if display_base.lower().endswith(".pdf"):
        display_base = display_base[:-4]
    if not display_base.lower().endswith(".pptx"):
        display_base = f"{display_base}.pptx"
    ascii_name = "slide-deck.pptx"
    utf8_quoted = quote(display_base, safe="")
    content_disposition = (
        f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{utf8_quoted}'
    )
    return Response(
        content=pptx_bytes,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "presentationml.presentation"
        ),
        headers={
            "Content-Disposition": content_disposition,
            "Cache-Control": "private, max-age=300",
        },
    )


@router.put("/api/slides/{slide_id}", response_model=SlideDeckResponse)
async def update_slide(
    slide_id: str,
    body: SlideDeckUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update a slide deck."""
    slide = await _get_slide(db, slide_id, user.id)
    if body.title is not None:
        slide.title = body.title
    if body.theme is not None:
        slide.theme = body.theme
    if body.slides_data is not None:
        slide.slides_data = body.slides_data
    if body.slide_style is not None:
        slide.slide_style = body.slide_style
    if body.slide_audience is not None:
        slide.slide_audience = body.slide_audience
    if body.slide_language is not None:
        slide.slide_language = body.slide_language
    if body.slide_duration is not None:
        slide.slide_duration = body.slide_duration
    if body.slide_custom_prompt is not None:
        slide.slide_custom_prompt = body.slide_custom_prompt
    await db.flush()
    await db.refresh(slide)
    return SlideDeckResponse.model_validate(slide)


@router.post(
    "/api/slides/{slide_id}/regenerate",
    response_model=SlideDeckResponse,
    status_code=202,
)
async def regenerate_slide(
    slide_id: str,
    body: SlideDeckUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update slide options and re-run generation in background. Returns 202."""
    slide = await _get_slide(db, slide_id, user.id)
    rl_redis, acquired, slide_daily, _ = await acquire_generation_rate_limit_slot(
        db,
        user_id=user.id,
        kind=GenerationKind.SLIDE_DECK,
        notebook_id=slide.notebook_id,
        source_ids=None,
        artifact_id=slide.id,
        user_role=user.role,
    )
    try:
        if body.title is not None:
            slide.title = body.title
        if body.theme is not None:
            slide.theme = body.theme
        if body.slide_style is not None:
            slide.slide_style = body.slide_style
        if body.slide_audience is not None:
            slide.slide_audience = body.slide_audience
        if body.slide_language is not None:
            slide.slide_language = body.slide_language
        if body.slide_duration is not None:
            slide.slide_duration = body.slide_duration
        if body.slide_custom_prompt is not None:
            slide.slide_custom_prompt = body.slide_custom_prompt
        slide.status = SlideDeckStatus.PENDING.value
        slide.slides_data = None
        slide.file_path = None
        clear_generation_error(slide)
        await db.flush()
        await db.refresh(slide)
        await db.commit()
    except Exception:
        await db.rollback()
        await release_generation_rate_limit_on_db_failure(
            rl_redis,
            acquired,
            user_id=user.id,
            daily_slide_reserved=slide_daily,
            daily_deep_research_reserved=False,
        )
        raise
    finally:
        await rl_redis.aclose()
    await publish_task_event("slide", slide.id, slide.status)
    generate_slide_deck_task.delay(
        slide.id,
        None,
        None,
    )
    return SlideDeckResponse.model_validate(slide)


@router.post(
    "/api/slides/{slide_id}/revise",
    response_model=SlideDeckResponse,
    status_code=202,
)
async def revise_slide_deck(
    slide_id: str,
    body: SlideDeckReviseRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Queue per-slide image edits (qwen-image-edit) and re-merge PDF/PPTX."""
    slide = await _get_slide(db, slide_id, user.id)
    if slide.status != SlideDeckStatus.READY.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Slide deck is not ready for revision",
        )
    raw = slide.slides_data if isinstance(slide.slides_data, dict) else {}
    artifacts = raw.get("artifacts") if isinstance(raw, dict) else {}
    images = artifacts.get("images") if isinstance(artifacts, dict) else None
    if not isinstance(images, list) or not images:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slide deck has no images to revise",
        )
    n = len(images)
    for edit in body.edits:
        if edit.slide_index >= n:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"slide_index {edit.slide_index} is out of range "
                    f"(valid: 0..{n - 1})"
                ),
            )

    rl_redis, acquired, slide_daily, _ = await acquire_generation_rate_limit_slot(
        db,
        user_id=user.id,
        kind=GenerationKind.SLIDE_DECK,
        notebook_id=slide.notebook_id,
        source_ids=None,
        artifact_id=slide.id,
        user_role=user.role,
    )
    try:
        slide.status = SlideDeckStatus.PROCESSING.value
        clear_generation_error(slide)
        await db.flush()
        await db.refresh(slide)
        await db.commit()
    except Exception:
        await db.rollback()
        await release_generation_rate_limit_on_db_failure(
            rl_redis,
            acquired,
            user_id=user.id,
            daily_slide_reserved=slide_daily,
            daily_deep_research_reserved=False,
        )
        raise
    finally:
        await rl_redis.aclose()
    await publish_task_event("slide", slide.id, slide.status)
    revise_slide_deck_task.delay(
        slide.id,
        [e.model_dump() for e in body.edits],
    )
    return SlideDeckResponse.model_validate(slide)


@router.delete("/api/slides/{slide_id}", status_code=204)
async def delete_slide(
    slide_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a slide deck and its files from object storage."""
    slide = await _get_slide(db, slide_id, user.id)
    keys = slide_deck_storage_keys(slide.slides_data, slide.file_path)
    delete_studio_objects_best_effort(keys)
    await db.delete(slide)
