"""Service for processing source documents: parsing, chunking, embedding."""

import logging

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import embed_chunks
from app.models.notebook import Notebook
from app.models.source import Source, SourceChunk

logger = logging.getLogger(__name__)


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
