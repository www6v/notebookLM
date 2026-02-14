"""Chat session and message API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.chat import ChatSession, Message
from app.models.notebook import Notebook
from app.models.user import User
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionResponse,
    MessageResponse,
)

router = APIRouter(tags=["chat"])


@router.post(
    "/api/notebooks/{notebook_id}/chat/sessions",
    response_model=ChatSessionResponse,
    status_code=201,
)
async def create_session(
    notebook_id: str,
    body: ChatSessionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new chat session in a notebook."""
    await _verify_notebook_access(db, notebook_id, user.id)
    session = ChatSession(
        notebook_id=notebook_id,
        title=body.title,
        settings=body.settings,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return ChatSessionResponse.model_validate(session)


@router.get(
    "/api/notebooks/{notebook_id}/chat/sessions",
    response_model=list[ChatSessionResponse],
)
async def list_sessions(
    notebook_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List chat sessions in a notebook."""
    await _verify_notebook_access(db, notebook_id, user.id)
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.notebook_id == notebook_id)
        .order_by(ChatSession.created_at.desc())
    )
    return [
        ChatSessionResponse.model_validate(s)
        for s in result.scalars().all()
    ]


@router.get(
    "/api/chat/{session_id}/messages",
    response_model=list[MessageResponse],
)
async def list_messages(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get message history for a chat session."""
    session = await _get_session(db, session_id, user.id)
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session.id)
        .order_by(Message.created_at)
    )
    return [
        MessageResponse.model_validate(m) for m in result.scalars().all()
    ]


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


async def _get_session(
    db: AsyncSession, session_id: str, user_id: str
) -> ChatSession:
    """Get a chat session and verify user access."""
    result = await db.execute(
        select(ChatSession)
        .join(Notebook, ChatSession.notebook_id == Notebook.id)
        .where(ChatSession.id == session_id, Notebook.user_id == user_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )
    return session
