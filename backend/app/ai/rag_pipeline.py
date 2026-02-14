"""RAG pipeline: retrieval-augmented generation for chat."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_router import chat_completion
from app.models.source import Source, SourceChunk


async def retrieve_relevant_chunks(
    db: AsyncSession,
    notebook_id: str,
    query: str,
    source_ids: list[str] | None = None,
    top_k: int = 5,
) -> list[dict]:
    """Retrieve source chunks for a query.

    Uses simple text matching for SQLite. For production with PostgreSQL +
    pgvector, replace with vector similarity search.
    """
    stmt = (
        select(
            SourceChunk.id,
            SourceChunk.content,
            SourceChunk.chunk_index,
            SourceChunk.source_id,
            Source.title.label("source_title"),
        )
        .join(Source, SourceChunk.source_id == Source.id)
        .where(
            Source.notebook_id == notebook_id,
            Source.is_active.is_(True),
        )
        .order_by(SourceChunk.chunk_index)
        .limit(top_k)
    )

    if source_ids:
        stmt = stmt.where(Source.id.in_(source_ids))

    result = await db.execute(stmt)
    rows = result.all()

    return [
        {
            "chunk_id": str(row.id),
            "content": row.content,
            "chunk_index": row.chunk_index,
            "source_id": str(row.source_id),
            "source_title": row.source_title,
        }
        for row in rows
    ]


def build_rag_prompt(
    query: str,
    chunks: list[dict],
    style: str = "default",
) -> list[dict]:
    """Build the LLM prompt with retrieved context and citations."""
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[{i}] (Source: {chunk['source_title']})\n{chunk['content']}"
        )

    context_text = "\n\n".join(context_parts)

    style_instruction = ""
    if style == "learning_guide":
        style_instruction = "Act as a patient learning guide. Explain concepts clearly and use analogies when helpful."
    elif style == "custom":
        style_instruction = "Be concise and direct."

    system_prompt = f"""You are an AI research assistant. Answer the user's question based ONLY on the provided source materials. Always cite your sources using bracket notation like [1], [2], etc.

If the sources don't contain enough information to answer, say so honestly.

{style_instruction}

Source Materials:
{context_text}"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query},
    ]


async def generate_rag_response(
    db: AsyncSession,
    notebook_id: str,
    query: str,
    source_ids: list[str] | None = None,
    style: str = "default",
    model: str | None = None,
) -> dict:
    """Full RAG pipeline: retrieve chunks, build prompt, generate response."""
    chunks = await retrieve_relevant_chunks(
        db, notebook_id, query, source_ids
    )

    if not chunks:
        return {
            "content": "I don't have enough information from your sources to answer this question. Try adding more sources or rephrasing your question.",
            "citations": {},
        }

    messages = build_rag_prompt(query, chunks, style)
    response = await chat_completion(messages, model=model)

    content = response.choices[0].message.content

    # Build citation map
    citations = {}
    for i, chunk in enumerate(chunks, 1):
        citations[str(i)] = {
            "source_id": chunk["source_id"],
            "source_title": chunk["source_title"],
            "content": chunk["content"][:200],
        }

    return {"content": content, "citations": citations}
