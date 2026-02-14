"""Embedding service for document chunks."""

from app.ai.llm_router import get_embedding


async def embed_text(text: str) -> list[float]:
    """Generate an embedding vector for a piece of text."""
    return await get_embedding(text)


async def embed_chunks(chunks: list[str]) -> list[list[float]]:
    """Generate embedding vectors for multiple text chunks."""
    embeddings = []
    for chunk in chunks:
        emb = await embed_text(chunk)
        embeddings.append(emb)
    return embeddings
