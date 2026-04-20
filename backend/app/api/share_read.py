"""Public read-only API for notebooks shared via share_token."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.studio.slide_deck import (
    _build_content_disposition,
    _build_media_headers,
    _build_slide_image_manifest,
    _build_slide_pdf_display_name,
    _build_variant_urls,
    _get_slide_image_entries,
    _get_variant_asset,
    _load_slide_variant_bytes,
    _normalize_slide_pdf_filename,
    _normalize_variant,
    _slide_workflow_dir,
    reconcile_stale_generation,
    reconcile_stale_generations,
)
from app.api.sources import (
    AUDIO_MEDIA_TYPES,
    IMAGE_MEDIA_TYPES,
    VIDEO_MEDIA_TYPES,
)
from app.database import get_db
from app.models.notebook import Notebook
from app.models.note import Note
from app.models.source import Source, SourceChunk
from app.models.studio import (
    DeepResearchReport,
    Infographic,
    MindMap,
    PodcastOverview,
    Report,
    SlideDeck,
)
from app.schemas.notebook import SharedNotebookView
from app.schemas.note import NoteResponse
from app.schemas.source import (
    ChunkContextResponse,
    SourceContentResponse,
    SourceResponse,
)
from app.schemas.studio import (
    DeepResearchResponse,
    InfographicResponse,
    MindMapResponse,
    PodcastResponse,
    ReportResponse,
    SlideDeckResponse,
)
from app.services.obs_storage import (
    download_file_from_obs,
    generate_presigned_url,
)
from app.services.studio.slide_service import build_slide_pptx_from_pdf_bytes
from app.services.source_service import (
    extract_text,
    finalize_uploaded_image,
    get_source_in_notebook,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/share/{share_token}", tags=["share"])

NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Not found",
)


async def _notebook_for_share(
    db: AsyncSession, share_token: str
) -> Notebook:
    result = await db.execute(
        select(Notebook).where(Notebook.share_token == share_token)
    )
    nb = result.scalar_one_or_none()
    if nb is None:
        raise NOT_FOUND
    return nb


async def _get_slide_for_share(
    db: AsyncSession, slide_id: str, notebook_id: str
) -> SlideDeck:
    result = await db.execute(
        select(SlideDeck).where(
            SlideDeck.id == slide_id,
            SlideDeck.notebook_id == notebook_id,
        )
    )
    slide = result.scalar_one_or_none()
    if slide is None:
        raise NOT_FOUND
    return slide


async def _get_mindmap_for_share(
    db: AsyncSession, mindmap_id: str, notebook_id: str
) -> MindMap:
    result = await db.execute(
        select(MindMap).where(
            MindMap.id == mindmap_id,
            MindMap.notebook_id == notebook_id,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise NOT_FOUND
    return row


async def _get_infographic_for_share(
    db: AsyncSession, infographic_id: str, notebook_id: str
) -> Infographic:
    result = await db.execute(
        select(Infographic).where(
            Infographic.id == infographic_id,
            Infographic.notebook_id == notebook_id,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise NOT_FOUND
    return row


async def _get_report_for_share(
    db: AsyncSession, report_id: str, notebook_id: str
) -> Report:
    result = await db.execute(
        select(Report).where(
            Report.id == report_id,
            Report.notebook_id == notebook_id,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise NOT_FOUND
    return row


async def _get_podcast_for_share(
    db: AsyncSession, podcast_id: str, notebook_id: str
) -> PodcastOverview:
    result = await db.execute(
        select(PodcastOverview).where(
            PodcastOverview.id == podcast_id,
            PodcastOverview.notebook_id == notebook_id,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise NOT_FOUND
    return row


async def _get_deep_research_for_share(
    db: AsyncSession, report_id: str, notebook_id: str
) -> DeepResearchReport:
    result = await db.execute(
        select(DeepResearchReport).where(
            DeepResearchReport.id == report_id,
            DeepResearchReport.notebook_id == notebook_id,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise NOT_FOUND
    return row


def _rewrite_slide_manifest_proxy_urls(
    manifest: dict, share_token: str, slide_id: str
) -> dict:
    for img in manifest.get("images", []):
        idx = img["index"]
        for var_name, var_data in img.get("variants", {}).items():
            proxy = (
                f"/api/share/{share_token}/slides/{slide_id}/images/{idx}"
                f"?variant={var_name}"
            )
            var_data["proxy_url"] = proxy
            var_data["preferred_url"] = var_data.get("url") or proxy
    return manifest


def _rewrite_variant_url_response(
    data: dict, share_token: str, slide_id: str, image_index: int, variant: str
) -> dict:
    proxy = (
        f"/api/share/{share_token}/slides/{slide_id}/images/{image_index}"
        f"?variant={variant}"
    )
    out = dict(data)
    out["proxy_url"] = proxy
    out["preferred_url"] = out.get("url") or proxy
    return out


@router.get("/notebook", response_model=SharedNotebookView)
async def share_get_notebook(
    share_token: str,
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    source_count_result = await db.execute(
        select(func.count(Source.id)).where(Source.notebook_id == notebook.id)
    )
    return SharedNotebookView(
        id=notebook.id,
        title=notebook.title,
        description=notebook.description,
        created_at=notebook.created_at,
        updated_at=notebook.updated_at,
        source_count=source_count_result.scalar_one(),
    )


@router.get("/sources", response_model=list[SourceResponse])
async def share_list_sources(
    share_token: str,
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    result = await db.execute(
        select(Source)
        .where(Source.notebook_id == notebook.id)
        .order_by(Source.created_at.desc())
    )
    return [SourceResponse.model_validate(s) for s in result.scalars().all()]


@router.get("/sources/{source_id}", response_model=SourceResponse)
async def share_get_source(
    share_token: str,
    source_id: str,
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    source = await get_source_in_notebook(db, source_id, notebook.id)
    return SourceResponse.model_validate(source)


@router.get("/sources/{source_id}/content", response_model=SourceContentResponse)
async def share_get_source_content(
    share_token: str,
    source_id: str,
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    source = await get_source_in_notebook(db, source_id, notebook.id)
    chunk_count_result = await db.execute(
        select(func.count(SourceChunk.id)).where(
            SourceChunk.source_id == source.id
        )
    )
    raw_content = source.raw_content
    file_url = None
    if source.type == "image" and source.file_path:
        if raw_content is None or not raw_content.strip() or raw_content.strip() == "[Image]":
            await finalize_uploaded_image(db, source)
            await db.refresh(source)
            raw_content = source.raw_content
        file_url = f"/api/share/{share_token}/sources/{source_id}/file"
    elif (
        raw_content is None
        and source.file_path
        and source.type not in ("image", "video", "audio")
    ):
        try:
            file_bytes = download_file_from_obs(source.file_path)
            raw_content = extract_text(file_bytes, source.type)
        except RuntimeError:
            logger.warning(
                "Failed to download source %s from OSS", source.id
            )
    return SourceContentResponse(
        id=source.id,
        title=source.title,
        summary=source.summary,
        tags=source.tags,
        raw_content=raw_content,
        chunk_count=chunk_count_result.scalar_one(),
        file_url=file_url,
    )


@router.get("/sources/{source_id}/file")
async def share_get_source_file(
    share_token: str,
    source_id: str,
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    source = await get_source_in_notebook(db, source_id, notebook.id)
    if source.type not in ("image", "video", "audio") or not source.file_path:
        raise NOT_FOUND
    try:
        url = generate_presigned_url(source.file_path, expiration=3600)
    except RuntimeError as exc:
        logger.warning("Failed to generate presigned URL: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to get image URL from storage",
        ) from exc
    return {"url": url}


@router.get("/sources/{source_id}/file/stream")
async def share_get_source_file_stream(
    share_token: str,
    source_id: str,
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    source = await get_source_in_notebook(db, source_id, notebook.id)
    if source.type not in ("image", "video", "audio") or not source.file_path:
        raise NOT_FOUND
    try:
        file_bytes = download_file_from_obs(source.file_path)
    except RuntimeError as exc:
        logger.warning("Failed to download file from OSS: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to load file from storage",
        ) from exc
    ext = (
        source.file_path.rsplit(".", 1)[-1].lower()
        if "." in source.file_path
        else ""
    )
    media_type = (
        VIDEO_MEDIA_TYPES.get(ext)
        or AUDIO_MEDIA_TYPES.get(ext)
        or IMAGE_MEDIA_TYPES.get(ext)
        or "application/octet-stream"
    )
    return Response(content=file_bytes, media_type=media_type)


@router.get("/sources/{source_id}/chunks/{chunk_id}", response_model=ChunkContextResponse)
async def share_get_chunk_context(
    share_token: str,
    source_id: str,
    chunk_id: str,
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    source = await get_source_in_notebook(db, source_id, notebook.id)
    result = await db.execute(
        select(SourceChunk).where(
            SourceChunk.id == chunk_id,
            SourceChunk.source_id == source.id,
        )
    )
    chunk = result.scalar_one_or_none()
    if chunk is None:
        raise NOT_FOUND
    meta = chunk.metadata_ or {}
    prev_result = await db.execute(
        select(SourceChunk)
        .where(
            SourceChunk.source_id == source.id,
            SourceChunk.chunk_index == chunk.chunk_index - 1,
        )
    )
    prev_chunk = prev_result.scalar_one_or_none()
    next_result = await db.execute(
        select(SourceChunk)
        .where(
            SourceChunk.source_id == source.id,
            SourceChunk.chunk_index == chunk.chunk_index + 1,
        )
    )
    next_chunk = next_result.scalar_one_or_none()
    return ChunkContextResponse(
        chunk_id=str(chunk.id),
        source_id=str(source.id),
        source_title=source.title,
        content=chunk.content,
        chunk_index=chunk.chunk_index,
        page_number=meta.get("page_number"),
        paragraph_index=meta.get("paragraph_index"),
        prev_content=prev_chunk.content if prev_chunk else None,
        next_content=next_chunk.content if next_chunk else None,
    )


@router.get("/mindmaps", response_model=list[MindMapResponse])
async def share_list_mindmaps(
    share_token: str,
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    result = await db.execute(
        select(MindMap)
        .where(MindMap.notebook_id == notebook.id)
        .order_by(MindMap.created_at.desc())
    )
    mind_maps = result.scalars().all()
    if reconcile_stale_generations(mind_maps):
        await db.flush()
    return [MindMapResponse.model_validate(m) for m in mind_maps]


@router.get("/mindmaps/{mindmap_id}", response_model=MindMapResponse)
async def share_get_mindmap(
    share_token: str,
    mindmap_id: str,
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    mind_map = await _get_mindmap_for_share(db, mindmap_id, notebook.id)
    if reconcile_stale_generation(mind_map):
        await db.flush()
    return MindMapResponse.model_validate(mind_map)


@router.get("/slides", response_model=list[SlideDeckResponse])
async def share_list_slides(
    share_token: str,
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    result = await db.execute(
        select(SlideDeck)
        .where(SlideDeck.notebook_id == notebook.id)
        .order_by(SlideDeck.created_at.desc())
    )
    slide_decks = result.scalars().all()
    if reconcile_stale_generations(slide_decks):
        await db.flush()
    return [SlideDeckResponse.model_validate(s) for s in slide_decks]


@router.get("/slides/{slide_id}", response_model=SlideDeckResponse)
async def share_get_slide(
    share_token: str,
    slide_id: str,
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    slide = await _get_slide_for_share(db, slide_id, notebook.id)
    if reconcile_stale_generation(slide):
        await db.flush()
    return SlideDeckResponse.model_validate(slide)


@router.get("/slides/{slide_id}/images-manifest")
async def share_get_slide_images_manifest(
    share_token: str,
    slide_id: str,
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    slide = await _get_slide_for_share(db, slide_id, notebook.id)
    manifest = _build_slide_image_manifest(slide)
    if manifest["image_count"] < 1:
        raise NOT_FOUND
    return _rewrite_slide_manifest_proxy_urls(
        manifest, share_token, slide.id
    )


@router.get("/slides/{slide_id}/pdf-url")
async def share_get_slide_pdf_url(
    share_token: str,
    slide_id: str,
    download: bool = False,
    filename: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    slide = await _get_slide_for_share(db, slide_id, notebook.id)
    if not slide.file_path:
        raise NOT_FOUND
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


@router.get("/slides/{slide_id}/images/{image_index}/url")
async def share_get_slide_image_url(
    share_token: str,
    slide_id: str,
    image_index: int,
    variant: str = "preview",
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    slide = await _get_slide_for_share(db, slide_id, notebook.id)
    normalized_variant = _normalize_variant(variant)
    if normalized_variant is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid slide image variant",
        )
    entries = _get_slide_image_entries(slide)
    if image_index < 0 or image_index >= len(entries):
        raise NOT_FOUND
    entry = entries[image_index]
    data = _build_variant_urls(slide, entry, normalized_variant)
    return _rewrite_variant_url_response(
        data, share_token, slide.id, image_index, normalized_variant
    )


@router.get("/slides/{slide_id}/pdf")
async def share_get_slide_pdf(
    share_token: str,
    slide_id: str,
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    slide = await _get_slide_for_share(db, slide_id, notebook.id)
    if not slide.file_path:
        raise NOT_FOUND
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


@router.get("/slides/{slide_id}/images/{image_index}")
async def share_get_slide_image(
    share_token: str,
    slide_id: str,
    image_index: int,
    variant: str = "preview",
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    slide = await _get_slide_for_share(db, slide_id, notebook.id)
    normalized_variant = _normalize_variant(variant)
    if normalized_variant is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid slide image variant",
        )
    entries = _get_slide_image_entries(slide)
    if not entries:
        raise NOT_FOUND
    if image_index < 0 or image_index >= len(entries):
        raise NOT_FOUND
    entry = entries[image_index]
    asset = _get_variant_asset(entry, normalized_variant)
    if asset is None:
        raise NOT_FOUND
    try:
        image_bytes, media_type, fname = await asyncio.to_thread(
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
    suffix = Path(fname).suffix or ".png"
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


@router.get("/slides/{slide_id}/pptx")
async def share_get_slide_pptx(
    share_token: str,
    slide_id: str,
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    slide = await _get_slide_for_share(db, slide_id, notebook.id)
    if not slide.file_path:
        raise NOT_FOUND
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


@router.get("/infographics", response_model=list[InfographicResponse])
async def share_list_infographics(
    share_token: str,
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    result = await db.execute(
        select(Infographic)
        .where(Infographic.notebook_id == notebook.id)
        .order_by(Infographic.created_at.desc())
    )
    rows = result.scalars().all()
    if reconcile_stale_generations(rows):
        await db.flush()
    return [InfographicResponse.model_validate(i) for i in rows]


@router.get("/infographics/{infographic_id}", response_model=InfographicResponse)
async def share_get_infographic(
    share_token: str,
    infographic_id: str,
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    infographic = await _get_infographic_for_share(
        db, infographic_id, notebook.id
    )
    if reconcile_stale_generation(infographic):
        await db.flush()
    return InfographicResponse.model_validate(infographic)


@router.get("/infographics/{infographic_id}/image-url")
async def share_get_infographic_image_url(
    share_token: str,
    infographic_id: str,
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    infographic = await _get_infographic_for_share(
        db, infographic_id, notebook.id
    )
    if not infographic.file_path:
        raise NOT_FOUND
    url = generate_presigned_url(infographic.file_path, expiration=3600)
    return {"url": url}


@router.get("/infographics/{infographic_id}/image")
async def share_get_infographic_image(
    share_token: str,
    infographic_id: str,
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    infographic = await _get_infographic_for_share(
        db, infographic_id, notebook.id
    )
    if not infographic.file_path:
        raise NOT_FOUND
    try:
        image_bytes = await asyncio.to_thread(
            download_file_from_obs,
            infographic.file_path,
        )
    except RuntimeError as exc:
        logger.exception("Infographic image download failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to load infographic image from storage",
        ) from exc
    display_base = (
        infographic.suggested_filename or infographic.title or "infographic"
    ).replace('"', "")
    if not display_base.lower().endswith(".png"):
        display_base = f"{display_base}.png"
    ascii_name = "infographic.png"
    utf8_quoted = quote(display_base, safe="")
    content_disposition = (
        f'inline; filename="{ascii_name}"; filename*=UTF-8\'\'{utf8_quoted}'
    )
    return Response(
        content=image_bytes,
        media_type="image/png",
        headers={
            "Content-Disposition": content_disposition,
            "Cache-Control": "private, max-age=300",
        },
    )


@router.get("/reports", response_model=list[ReportResponse])
async def share_list_reports(
    share_token: str,
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    result = await db.execute(
        select(Report)
        .where(Report.notebook_id == notebook.id)
        .order_by(Report.created_at.desc())
    )
    rows = result.scalars().all()
    if reconcile_stale_generations(rows):
        await db.flush()
    return [ReportResponse.model_validate(r) for r in rows]


@router.get("/reports/{report_id}", response_model=ReportResponse)
async def share_get_report(
    share_token: str,
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    report = await _get_report_for_share(db, report_id, notebook.id)
    if reconcile_stale_generation(report):
        await db.flush()
    return ReportResponse.model_validate(report)


@router.get("/podcasts", response_model=list[PodcastResponse])
async def share_list_podcasts(
    share_token: str,
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    result = await db.execute(
        select(PodcastOverview)
        .where(PodcastOverview.notebook_id == notebook.id)
        .order_by(PodcastOverview.created_at.desc())
    )
    rows = result.scalars().all()
    if reconcile_stale_generations(rows):
        await db.flush()
    return [PodcastResponse.model_validate(p) for p in rows]


@router.get("/podcasts/{podcast_id}", response_model=PodcastResponse)
async def share_get_podcast(
    share_token: str,
    podcast_id: str,
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    podcast = await _get_podcast_for_share(db, podcast_id, notebook.id)
    if reconcile_stale_generation(podcast):
        await db.flush()
    return PodcastResponse.model_validate(podcast)


@router.get("/podcasts/{podcast_id}/audio-url")
async def share_get_podcast_audio_url(
    share_token: str,
    podcast_id: str,
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    podcast = await _get_podcast_for_share(db, podcast_id, notebook.id)
    if not podcast.file_path:
        raise NOT_FOUND
    url = generate_presigned_url(podcast.file_path, expiration=3600)
    return {"url": url}


@router.get("/podcasts/{podcast_id}/audio")
async def share_get_podcast_audio(
    share_token: str,
    podcast_id: str,
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    podcast = await _get_podcast_for_share(db, podcast_id, notebook.id)
    if not podcast.file_path:
        raise NOT_FOUND
    try:
        audio_bytes = await asyncio.to_thread(
            download_file_from_obs,
            podcast.file_path,
        )
    except RuntimeError as exc:
        logger.exception("Podcast audio download failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to load podcast audio from storage",
        ) from exc
    display_base = (
        podcast.suggested_filename or podcast.title or "podcast"
    ).replace('"', "")
    if not display_base.lower().endswith(".wav"):
        display_base = f"{display_base}.wav"
    ascii_name = "podcast.wav"
    utf8_quoted = quote(display_base, safe="")
    content_disposition = (
        f'inline; filename="{ascii_name}"; filename*=UTF-8\'\'{utf8_quoted}'
    )
    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={
            "Content-Disposition": content_disposition,
            "Cache-Control": "private, max-age=300",
        },
    )


@router.get("/notes", response_model=list[NoteResponse])
async def share_list_notes(
    share_token: str,
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    result = await db.execute(
        select(Note)
        .where(Note.notebook_id == notebook.id)
        .order_by(Note.is_pinned.desc(), Note.updated_at.desc())
    )
    return [NoteResponse.model_validate(n) for n in result.scalars().all()]


@router.get("/deep-research", response_model=list[DeepResearchResponse])
async def share_list_deep_research(
    share_token: str,
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    result = await db.execute(
        select(DeepResearchReport)
        .where(DeepResearchReport.notebook_id == notebook.id)
        .order_by(DeepResearchReport.created_at.desc())
    )
    return [
        DeepResearchResponse.from_orm_report(r)
        for r in result.scalars().all()
    ]


@router.get("/deep-research/{report_id}", response_model=DeepResearchResponse)
async def share_get_deep_research(
    share_token: str,
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    notebook = await _notebook_for_share(db, share_token)
    report = await _get_deep_research_for_share(
        db, report_id, notebook.id
    )
    return DeepResearchResponse.from_orm_report(report)
