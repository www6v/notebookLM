"""Service for processing source documents: parsing, chunking, embedding."""

import logging

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import embed_chunks
from app.commons.util import get_image_source_content
from app.models.notebook import Notebook
from app.models.source import Source, SourceChunk
from app.services.obs_storage import download_file_from_obs

logger = logging.getLogger(__name__)

# Max characters per source to include in combined content for LLM.
_MAX_CONTENT_PER_SOURCE = 3000


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks."""
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start = end - overlap

    return [c for c in chunks if c]


async def process_source(db: AsyncSession, source_id: str):
    """Process a source: chunk the content and generate embeddings."""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if source is None:
        return

    source.status = "processing"
    await db.flush()

    try:
        content = source.raw_content or ""
        if not content:
            source.status = "error"
            await db.flush()
            return

        # Chunk the content
        chunks = chunk_text(content)
        if not chunks:
            source.status = "error"
            await db.flush()
            return

        # Generate embeddings
        try:
            embeddings = await embed_chunks(chunks)
        except Exception:
            # If embedding fails, still store chunks without embeddings
            embeddings = [None] * len(chunks)

        # Store chunks
        for i, (chunk_text_content, embedding) in enumerate(
            zip(chunks, embeddings)
        ):
            chunk = SourceChunk(
                source_id=source.id,
                content=chunk_text_content,
                embedding=embedding,
                chunk_index=i,
                metadata_={"char_start": i * 800, "char_end": (i + 1) * 800},
            )
            db.add(chunk)

        source.status = "ready"
        await db.flush()

    except Exception as e:
        source.status = "error"
        await db.flush()
        raise


def extract_text(file_bytes: bytes, file_type: str) -> str:
    """Extract text content from file bytes based on file type.

    Args:
        file_bytes: Raw file content.
        file_type: Source type (txt, markdown, pdf, docx, image).

    Returns:
        Extracted text content. For images, returns a placeholder.
    """
    if file_type == "image":
        return "[Image]"

    if file_type in ("txt", "markdown"):
        return file_bytes.decode("utf-8", errors="replace")

    if file_type == "pdf":
        try:
            from io import BytesIO

            from pypdf import PdfReader

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
            from io import BytesIO

            from docx import Document

            doc = Document(BytesIO(file_bytes))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paragraphs)
        except Exception as exc:
            logger.warning("DOCX text extraction failed: %s", exc)
            return "[Unable to extract DOCX content]"

    # Fallback: try decoding as text
    return file_bytes.decode("utf-8", errors="replace")


async def _get_single_source_content(source: Source) -> str | None:
    """Get text content for one source from raw_content, OBS file, or vision API.

    Returns content string (suitable for mind map), or None if unavailable.
    """
    raw_content = source.raw_content
    if raw_content is not None:
        return raw_content[:_MAX_CONTENT_PER_SOURCE] if raw_content else None

    if not source.file_path:
        return None

    try:
        if source.type == "image":
            return await get_image_source_content(
                source, _MAX_CONTENT_PER_SOURCE
            )

        file_bytes = download_file_from_obs(source.file_path)
        raw_content = extract_text(file_bytes, source.type)
        return raw_content[:_MAX_CONTENT_PER_SOURCE] if raw_content else None
    except RuntimeError as e:
        logger.error(
            "Failed to download content from OBS for source '%s': %s",
            source.title,
            str(e),
        )
        return None
    except Exception as e:
        logger.error(
            "Unexpected error getting content for source '%s': %s",
            source.title,
            str(e),
        )
        fallback = (source.raw_content or "")[:_MAX_CONTENT_PER_SOURCE]
        if fallback:
            logger.info("Using fallback content for source '%s'", source.title)
        return fallback if fallback else None


async def build_combined_content_from_sources(
    sources: list[Source],
) -> str:
    """Build a single combined text from multiple sources for mind map LLM."""
    parts = []
    for source in sources:
        content = await _get_single_source_content(source)
        if not content:
            logger.warning(
                "No content available for source '%s', skipping",
                source.title,
            )
            continue
        logger.info(
            "Source '%s' content length: %s characters",
            source.title,
            len(content),
        )
        logger.info(
            "Source '%s' content preview: %s",
            source.title,
            content[:500],
        )
        parts.append(f"[{source.title}]: {content}")
    return "\n\n".join(parts)


async def fetch_sources(
    db: AsyncSession,
    notebook_id: str,
    source_ids: list[str] | None = None,
) -> list[Source]:
    """Load active sources for a notebook, optionally filtered by source_ids."""
    stmt = select(Source).where(
        Source.notebook_id == notebook_id,
        Source.is_active.is_(True),
    )
    if source_ids:
        stmt = stmt.where(Source.id.in_(source_ids))
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def verify_notebook_access(
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


async def get_source(
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
