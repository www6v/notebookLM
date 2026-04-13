"""RAG pipeline: retrieval-augmented generation for chat.

Delegates to the deep_search module for iterative query decomposition,
vector retrieval, reasoning, and reflection.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.deep_search import deep_search


async def generate_rag_response(
    db: AsyncSession,
    notebook_id: str,
    query: str,
    source_ids: list[str] | None = None,
    style: str = "default",
    model: str | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
) -> dict:
    """Full RAG pipeline using deep search.

    Returns {"content": str, "citations": dict}.
    """
    result = await deep_search(
        db,
        notebook_id,
        query,
        source_ids=source_ids,
        user_id=user_id,
        session_id=session_id,
    )
    return {
        "content": result["content"],
        "citations": result["citations"],
    }
