"""Service for processing source documents: parsing, chunking, embedding."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import embed_chunks
from app.models.source import Source, SourceChunk


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
