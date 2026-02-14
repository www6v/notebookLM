"""Source management API routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.notebook import Notebook
from app.models.source import Source, SourceChunk
from app.models.user import User
from app.schemas.source import (
    SourceCreate,
    SourceContentResponse,
    SourceResponse,
    SourceUpdate,
)
from app.services.obs_storage import (
    upload_file_to_obs,
    get_file_url,
    delete_file_from_obs,
    download_file_from_obs,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["sources"])


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
    await _verify_notebook_access(db, notebook_id, user.id)
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

    The file is stored in OBS (Object Storage Service) and
    its object key is saved in the ``file_path`` field.
    """
    await _verify_notebook_access(db, notebook_id, user.id)

    # Determine file type from extension
    filename = file.filename or "unknown"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"
    type_map = {
        "pdf": "pdf",
        "docx": "docx",
        "doc": "docx",
        "txt": "txt",
        "md": "markdown",
        "markdown": "markdown",
    }
    file_type = type_map.get(ext, "txt")

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
    await _verify_notebook_access(db, notebook_id, user.id)
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
    source = await _get_source(db, source_id, user.id)
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
    source = await _get_source(db, source_id, user.id)

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

    If ``raw_content`` is already stored in the database it is returned
    directly.  Otherwise the file is downloaded from OBS and text is
    extracted based on file type (txt / markdown are decoded as UTF-8,
    PDF uses PyPDF2, DOCX uses python-docx).
    """
    source = await _get_source(db, source_id, user.id)
    chunk_count_result = await db.execute(
        select(func.count(SourceChunk.id)).where(
            SourceChunk.source_id == source.id
        )
    )

    raw_content = source.raw_content

    # If no cached content, try downloading from OBS and extracting text
    if raw_content is None and source.file_path:
        try:
            file_bytes = download_file_from_obs(source.file_path)
            raw_content = _extract_text(file_bytes, source.type)
        except RuntimeError:
            logger.warning(
                "Failed to download source %s from OBS", source.id
            )

    return SourceContentResponse(
        id=source.id,
        title=source.title,
        raw_content=raw_content,
        chunk_count=chunk_count_result.scalar_one(),
    )


def _extract_text(file_bytes: bytes, file_type: str) -> str:
    """Extract text content from file bytes based on file type.

    Args:
        file_bytes: Raw file content.
        file_type: Source type (txt, markdown, pdf, docx).

    Returns:
        Extracted text content.
    """
    if file_type in ("txt", "markdown"):
        return file_bytes.decode("utf-8", errors="replace")

    if file_type == "pdf":
        try:
            from pypdf import PdfReader
            from io import BytesIO

            reader = PdfReader(BytesIO(file_bytes))
            pages = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            return "\n\n".join(pages)
        except Exception as exc:
            logger.warning("PDF text extraction failed: %s", exc)
            return "[Unable to extract PDF content]"

    if file_type == "docx":
        try:
            from docx import Document
            from io import BytesIO

            doc = Document(BytesIO(file_bytes))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paragraphs)
        except Exception as exc:
            logger.warning("DOCX text extraction failed: %s", exc)
            return "[Unable to extract DOCX content]"

    # Fallback: try decoding as text
    return file_bytes.decode("utf-8", errors="replace")


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


async def _get_source(
    db: AsyncSession, source_id: str, user_id: str
) -> Source:
    """Get a source and verify user access through its notebook."""
    result = await db.execute(
        select(Source)
        .join(Notebook, Source.notebook_id == Notebook.id)
        .where(Source.id == source_id, Notebook.user_id == user_id)
    )
    source = result.scalar_one_or_none()
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found",
        )
    return source
