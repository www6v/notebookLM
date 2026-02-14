"""Chat service: manages chat sessions and message generation."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.rag_pipeline import generate_rag_response
from app.models.chat import ChatSession, Message


async def handle_chat_message(
    db: AsyncSession,
    session: ChatSession,
    user_content: str,
    source_ids: list[str] | None = None,
    style: str = "default",
    model: str | None = None,
) -> Message:
    """Process a user message and generate an AI response.

    1. Save the user message
    2. Run the RAG pipeline
    3. Save and return the assistant message
    """
    # Save user message
    user_msg = Message(
        session_id=session.id,
        role="user",
        content=user_content,
    )
    db.add(user_msg)
    await db.flush()

    # Generate AI response via RAG
    result = await generate_rag_response(
        db,
        session.notebook_id,
        user_content,
        source_ids=source_ids,
        style=style,
        model=model,
    )

    # Save assistant message
    assistant_msg = Message(
        session_id=session.id,
        role="assistant",
        content=result["content"],
        citations=result["citations"],
    )
    db.add(assistant_msg)
    await db.flush()
    await db.refresh(assistant_msg)

    return assistant_msg
