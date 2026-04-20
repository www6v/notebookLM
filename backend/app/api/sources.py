"""Source management API routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.limits import ROLE_LIMITS
from app.models.source import Source, SourceChunk
from app.models.user import User
from app.schemas.source import (
    ChunkContextResponse,
    SourceCreate,
    SourceContentResponse,
    SourceResponse,
    SourceUpdate,
)
from app.services.obs_storage import (
    delete_file_from_obs,
    download_file_from_obs,
    generate_presigned_url,
    get_file_url,
    upload_file_to_obs,
)
# from app.ai.milvus_client import delete_by_source_id
from app.services.task_event_service import publish_task_event
from app.services.source.source_service import (
    extract_text,
    finalize_uploaded_image,
    get_source,
    verify_notebook_access,
)
from app.tasks.source_tasks import process_source_task

logger = logging.getLogger(__name__)

router = APIRouter(tags=["sources"])

# Allowed file extensions for upload (documents + images + audio + video)
ALLOWED_EXTENSIONS = frozenset({
    "pdf", "docx", "doc", "txt", "md", "csv", "pptx",
    "bmp", "gif", "png", "webp", "jpeg", "jpg", "ico",
    "mp3", "wav", "m4a", "aac", "ogg", "opus",
    "avi", "mp4", "mpeg",
})

FILE_TYPE_MAP = {
    "pdf": "pdf",
    "docx": "docx",
    "doc": "docx",
    "txt": "txt",
    "md": "markdown",
    "csv": "csv",
    "pptx": "pptx",
    "bmp": "image",
    "gif": "image",
    "png": "image",
    "webp": "image",
    "jpeg": "image",
    "jpg": "image",
    "ico": "image",
    "mp3": "audio",
    "wav": "audio",
    "m4a": "audio",
    "aac": "audio",
    "ogg": "audio",
    "opus": "audio",
    "avi": "video",
    "mp4": "video",
    "mpeg": "video",
}

# Content-Type for image stream (extension -> media type)
IMAGE_MEDIA_TYPES = {
    "bmp": "image/bmp",
    "gif": "image/gif",
    "png": "image/png",
    "webp": "image/webp",
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "ico": "image/x-icon",
}

# Content-Type for audio stream (extension -> media type)
AUDIO_MEDIA_TYPES = {
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "m4a": "audio/mp4",
    "aac": "audio/aac",
    "ogg": "audio/ogg",
    "opus": "audio/opus",
}

# Content-Type for video stream (extension -> media type)
VIDEO_MEDIA_TYPES = {
    "avi": "video/x-msvideo",
    "mp4": "video/mp4",
    "mpeg": "video/mpeg",
}


@router.post(
    "/api/notebooks/{notebook_id}/sources",
    response_model=SourceResponse,
    status_code=201,
)
async def add_source(
    notebook_id: str,
    body: SourceCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Add a source to a notebook (via URL or metadata)."""
    await verify_notebook_access(db, notebook_id, user.id)

    limits = ROLE_LIMITS.get(user.role, ROLE_LIMITS["free"])
    count_result = await db.execute(
        select(func.count(Source.id)).where(Source.notebook_id == notebook_id)
    )
    current_count = count_result.scalar_one()
    if current_count >= limits["max_sources_per_notebook"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"该笔记本已达到资源数量上限（{limits['max_sources_per_notebook']}）。"
                "请升级账户以添加更多资源。"
            ),
        )

    source = Source(
        notebook_id=notebook_id,
        title=body.title or body.url or "Untitled Source",
        type=body.type,
        original_url=body.url,
        status="pending",
    )
    db.add(source)
    await db.flush()
    await db.refresh(source)

    await db.commit()
    await db.refresh(source)

    if source.type in ("web", "youtube", "bilibili") and source.original_url:
        await publish_task_event("source", source.id, source.status)
        process_source_task.delay(source.id)

    return SourceResponse.model_validate(source)


@router.post(
    "/api/notebooks/{notebook_id}/sources/upload",
    response_model=SourceResponse,
    status_code=201,
)
async def upload_source(
    notebook_id: str,
    file: UploadFile = File(...),
    title: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Upload a file as a source.

    Supported types: pdf, docx, doc, txt, md, csv, pptx (documents);
    bmp, gif, png, webp, jpeg, jpg, ico (images);
    mp3, wav, m4a, aac, ogg, opus (audio);
    avi, mp4, mpeg (video).
    File content is stored in OSS; metadata is stored in the database.
    """
    await verify_notebook_access(db, notebook_id, user.id)

    limits = ROLE_LIMITS.get(user.role, ROLE_LIMITS["free"])
    count_result = await db.execute(
        select(func.count(Source.id)).where(Source.notebook_id == notebook_id)
    )
    current_count = count_result.scalar_one()
    if current_count >= limits["max_sources_per_notebook"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"该笔记本已达到资源数量上限（{limits['max_sources_per_notebook']}）。"
                "请升级账户以添加更多资源。"
            ),
        )

    filename = file.filename or "unknown"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"File type '.{ext}' not allowed. Allowed: "
                f"{', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
        )
    file_type = FILE_TYPE_MAP.get(ext, "txt")

    # Read file content
    content = await file.read()
    content_type = file.content_type or "application/octet-stream"

    # Upload file to object storage (OSS)
    try:
        object_key = upload_file_to_obs(
            file_content=content,
            filename=filename,
            content_type=content_type,
        )
        storage_url = get_file_url(object_key)
        logger.info(
            "File uploaded to OSS: %s -> %s", filename, storage_url
        )
    except RuntimeError as exc:
        logger.error("OSS upload failed for %s: %s", filename, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file to object storage: {exc}",
        ) from exc

    raw_content = None
    if file_type in (
        "txt",
        "markdown",
        "pdf",
        "docx",
        "csv",
        "pptx",
        "image",
    ):
        raw_content = extract_text(content, file_type)

    source = Source(
        notebook_id=notebook_id,
        title=title or filename,
        type=file_type,
        file_path=object_key,
        file_size_bytes=len(content),
        original_url=storage_url,
        raw_content=raw_content,
        status="pending",
    )
    db.add(source)
    await db.flush()
    await db.refresh(source)

    await db.commit()
    await db.refresh(source)

    if file_type in ("video", "image", "audio") or (
        raw_content and raw_content.strip()
    ):
        await publish_task_event("source", source.id, source.status)
        process_source_task.delay(source.id)

    return SourceResponse.model_validate(source)


@router.get(
    "/api/notebooks/{notebook_id}/sources",
    response_model=list[SourceResponse],
)
async def list_sources(
    notebook_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all sources in a notebook."""
    await verify_notebook_access(db, notebook_id, user.id)
    result = await db.execute(
        select(Source)
        .where(Source.notebook_id == notebook_id)
        .order_by(Source.created_at.desc())
    )
    return [SourceResponse.model_validate(s) for s in result.scalars().all()]


@router.get("/api/sources/{source_id}", response_model=SourceResponse)
async def get_source_detail(
    source_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a source by id."""
    source = await get_source(db, source_id, user.id)
    return SourceResponse.model_validate(source)


@router.patch("/api/sources/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: str,
    body: SourceUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update a source (toggle active, rename)."""
    source = await get_source(db, source_id, user.id)
    if body.title is not None:
        source.title = body.title
    if body.is_active is not None:
        source.is_active = body.is_active
    await db.flush()
    await db.refresh(source)
    return SourceResponse.model_validate(source)


@router.delete("/api/sources/{source_id}", status_code=204)
async def delete_source(
    source_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a source and its file from OSS (if applicable)."""
    source = await get_source(db, source_id, user.id)

    # Delete file from OSS if it was uploaded there
    if source.file_path:
        try:
            delete_file_from_obs(source.file_path)
        except RuntimeError:
            logger.warning(
                "Failed to delete OSS file %s, proceeding with DB deletion",
                source.file_path,
            )

    # try:
    #     delete_by_source_id(source_id)
    # except Exception as exc:
    #     logger.warning(
    #         "Milvus delete_by_source_id failed for %s: %s",
    #         source_id,
    #         exc,
    #     )

    await db.delete(source)


@router.get(
    "/api/sources/{source_id}/content",
    response_model=SourceContentResponse,
)
async def get_source_content(
    source_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get parsed content of a source.

    For images: returns ``file_url`` for frontend display.
    For video/audio: returns extracted ``raw_content`` only (no ``file_url``).
    For documents: if ``raw_content`` is in the database it is returned;
    otherwise the file is downloaded from OSS and text is extracted
    (txt/markdown, CSV, PDF, DOCX, PPTX).
    """
    source = await get_source(db, source_id, user.id)
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
        # Same-origin URL so frontend can fetch with auth and display
        file_url = f"/api/sources/{source_id}/file"
    elif (
        raw_content is None
        and source.file_path
        and source.type not in ("image", "video", "audio")
    ):
        # For non-image sources, download from OSS and extract text if needed
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


@router.get("/api/sources/{source_id}/file")
async def get_source_file(
    source_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return OSS presigned URL for image/video/audio source."""
    logger.info(
        "get_source_file: source_id=%s, user_id=%s",
        source_id,
        user.id,
    )
    source = await get_source(db, source_id, user.id)
    if source.type not in ("image", "video", "audio") or not source.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source is not an image/video/audio or has no file",
        )
    try:
        url = generate_presigned_url(source.file_path, expiration=3600)
    except RuntimeError as exc:
        logger.warning("Failed to generate presigned URL: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to get image URL from storage",
        ) from exc
    logger.info("get_source_file: success source_id=%s", source_id)
    return {"url": url}


@router.get("/api/sources/{source_id}/file/stream")
async def get_source_file_stream(
    source_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Stream image/video/audio bytes from OSS."""
    source = await get_source(db, source_id, user.id)
    if source.type not in ("image", "video", "audio") or not source.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source is not an image/video/audio or has no file",
        )
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


@router.get(
    "/api/sources/{source_id}/chunks/{chunk_id}",
    response_model=ChunkContextResponse,
)
async def get_chunk_context(
    source_id: str,
    chunk_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a specific chunk with surrounding context for citation preview."""
    source = await get_source(db, source_id, user.id)

    result = await db.execute(
        select(SourceChunk).where(
            SourceChunk.id == chunk_id,
            SourceChunk.source_id == source.id,
        )
    )
    chunk = result.scalar_one_or_none()
    if chunk is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chunk not found",
        )

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
