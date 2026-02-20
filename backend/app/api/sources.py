"""Source management API routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.source import Source, SourceChunk
from app.models.user import User
from app.schemas.source import (
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
from app.services.source_service import (
    extract_text,
    get_source,
    verify_notebook_access,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["sources"])

# Allowed file extensions for upload (documents + images)
ALLOWED_EXTENSIONS = frozenset({
    "pdf", "docx", "doc", "txt", "md", "markdown",
    "bmp", "gif", "png", "webp", "jpeg", "jpg",
})

FILE_TYPE_MAP = {
    "pdf": "pdf",
    "docx": "docx",
    "doc": "docx",
    "txt": "txt",
    "md": "markdown",
    "markdown": "markdown",
    "bmp": "image",
    "gif": "image",
    "png": "image",
    "webp": "image",
    "jpeg": "image",
    "jpg": "image",
}

# Content-Type for image stream (extension -> media type)
IMAGE_MEDIA_TYPES = {
    "bmp": "image/bmp",
    "gif": "image/gif",
    "png": "image/png",
    "webp": "image/webp",
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
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

    Supported types: pdf, docx, doc, txt, md, markdown (documents);
    bmp, gif, png, webp, jpeg, jpg (images).
    File content is stored in OBS; metadata is stored in the database.
    """
    await verify_notebook_access(db, notebook_id, user.id)

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

    # Upload file to OBS
    try:
        object_key = upload_file_to_obs(
            file_content=content,
            filename=filename,
            content_type=content_type,
        )
        obs_url = get_file_url(object_key)
        logger.info(
            "File uploaded to OBS: %s -> %s", filename, obs_url
        )
    except RuntimeError as exc:
        logger.error("OBS upload failed for %s: %s", filename, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file to object storage: {exc}",
        ) from exc

    # For text-based files, also store raw_content for indexing
    raw_content = None
    if file_type in ("txt", "markdown"):
        raw_content = content.decode("utf-8", errors="replace")

    source = Source(
        notebook_id=notebook_id,
        title=title or filename,
        type=file_type,
        file_path=object_key,
        original_url=obs_url,
        raw_content=raw_content,
        status="ready",
    )
    db.add(source)
    await db.flush()
    await db.refresh(source)
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
    """Delete a source and its file from OBS (if applicable)."""
    source = await get_source(db, source_id, user.id)

    # Delete file from OBS if it was uploaded there
    if source.file_path:
        try:
            delete_file_from_obs(source.file_path)
        except RuntimeError:
            logger.warning(
                "Failed to delete OBS file %s, proceeding with DB deletion",
                source.file_path,
            )

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

    For images: returns ``file_url`` (presigned OBS URL) for frontend display.
    For documents: if ``raw_content`` is in the database it is returned;
    otherwise the file is downloaded from OBS and text is extracted
    (txt/markdown, PDF, DOCX).
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
        # Same-origin URL so frontend can fetch with auth and display the image
        file_url = f"/api/sources/{source_id}/file"
    elif (
        raw_content is None
        and source.file_path
        and source.type != "image"
    ):
        # For non-image sources, download from OBS and extract text if needed
        try:
            file_bytes = download_file_from_obs(source.file_path)
            raw_content = extract_text(file_bytes, source.type)
        except RuntimeError:
            logger.warning(
                "Failed to download source %s from OBS", source.id
            )

    return SourceContentResponse(
        id=source.id,
        title=source.title,
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
    """Return OBS presigned URL for image source. Frontend uses this URL to display."""
    logger.info(
        "get_source_file: source_id=%s, user_id=%s",
        source_id,
        user.id,
    )
    source = await get_source(db, source_id, user.id)
    if source.type != "image" or not source.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source is not an image or has no file",
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
    """Stream image bytes from OBS. Used when presigned URL fails in browser (e.g. CORS)."""
    source = await get_source(db, source_id, user.id)
    if source.type != "image" or not source.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source is not an image or has no file",
        )
    try:
        file_bytes = download_file_from_obs(source.file_path)
    except RuntimeError as exc:
        logger.warning("Failed to download image from OBS: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to load image from storage",
        ) from exc
    ext = (
        source.file_path.rsplit(".", 1)[-1].lower()
        if "." in source.file_path
        else ""
    )
    media_type = IMAGE_MEDIA_TYPES.get(ext, "application/octet-stream")
    return Response(content=file_bytes, media_type=media_type)
