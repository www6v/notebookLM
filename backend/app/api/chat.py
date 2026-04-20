"""Chat session and message API routes."""

import asyncio
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

# from app.ai.deep_search import deep_search
from app.api.deps import get_current_user
from app.database import get_db
from app.limits import ROLE_LIMITS
from app.models.chat import ChatSession, Message
from app.models.notebook import Notebook
from app.models.user import User
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionResponse,
    MessageCreate,
    MessageResponse,
)
# from app.services.chat_service import handle_chat_message
from app.services.infra.deep_searcher import deepsearch_query


logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


def _extract_answer_from_deepsearch_payload(
    payload: dict,
) -> tuple[str, dict | None]:
    """Resolve answer text and citations from deep-search JSON (mirrors frontend)."""
    root = payload
    data = payload
    inner = payload.get("data")
    if isinstance(inner, dict):
        data = inner
    content = ""
    for key in (
        "answer",
        "content",
        "result",
        "message",
        "text",
        "final_answer",
    ):
        val = data.get(key)
        if isinstance(val, str) and val:
            content = val
            break
    if not content:
        val = root.get("answer")
        if isinstance(val, str):
            content = val
    citations = None
    raw_c = data.get("citations")
    if isinstance(raw_c, dict):
        citations = raw_c
    else:
        raw_c = root.get("citations")
        if isinstance(raw_c, dict):
            citations = raw_c
    return content, citations


async def _check_daily_chat_limit(
    db: AsyncSession, user: User
) -> None:
    """Raise 403 if the user has exceeded the daily chat message limit."""
    limits = ROLE_LIMITS.get(user.role, ROLE_LIMITS["free"])
    max_daily = limits.get("max_daily_chats", 50)
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    count_result = await db.execute(
        select(func.count(Message.id))
        .join(ChatSession, Message.session_id == ChatSession.id)
        .join(Notebook, ChatSession.notebook_id == Notebook.id)
        .where(
            Notebook.user_id == user.id,
            Message.role == "user",
            Message.created_at >= today_start,
        )
    )
    current_count = count_result.scalar_one()
    if current_count >= max_daily:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"已达到每日对话次数上限（{max_daily}）。"
                "请升级账户以获取更多对话次数。"
            ),
        )


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


# @router.post(
#     "/api/chat/{session_id}/messages",
#     response_model=MessageResponse,
#     status_code=201,
# )
# async def send_message(
#     session_id: str,
#     body: MessageCreate,
#     db: AsyncSession = Depends(get_db),
#     user: User = Depends(get_current_user),
# ):
#     """Send a user message and get an AI response via RAG pipeline."""
#     await _check_daily_chat_limit(db, user)
#     session = await _get_session(db, session_id, user.id)
#     assistant_msg = await handle_chat_message(
#         db,
#         session,
#         body.content,
#         source_ids=body.source_ids,
#         user_id=user.username,
#         session_id=session_id,
#     )
#     return MessageResponse.model_validate(assistant_msg)



@router.post("/api/chat/{session_id}/messages/stream")
async def send_message_stream(
    session_id: str,
    body: MessageCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Send a user message with SSE streaming of search steps and final answer.

    Tries the remote deep-search service first; on failure (e.g. upstream
    strict JSON parse errors), falls back to the local deep_search pipeline.
    """
    await _check_daily_chat_limit(db, user)
    session = await _get_session(db, session_id, user.id)

    user_msg = Message(
        session_id=session.id,
        role="user",
        content=body.content,
    )
    db.add(user_msg)
    await db.flush()

    remote_result = await asyncio.to_thread(deepsearch_query, body.content)
    if remote_result is None:
        # Use 200 so the client fetch adapter parses JSON and surfaces detail.
        return JSONResponse(
            content={
                "detail": (
                    "Deep search service returned no response. "
                    "Please try again later."
                ),
            },
        )
    if isinstance(remote_result, dict):
        answer_text, answer_citations = _extract_answer_from_deepsearch_payload(
            remote_result
        )
        if answer_text.strip():
            assistant_msg = Message(
                session_id=session.id,
                role="assistant",
                content=answer_text,
                citations=answer_citations,
            )
            db.add(assistant_msg)
            await db.flush()
            await db.refresh(assistant_msg)
        return JSONResponse(content=remote_result)

    return JSONResponse(
        content={"detail": "Unexpected response type from deep search service."},
    )

    # async def event_generator():
    #     out_queue: asyncio.Queue[
    #         tuple[str, dict | str] | None
    #     ] = asyncio.Queue()

    #     async def on_search_step(step: dict) -> None:
    #         await out_queue.put(("step", step))

    #     async def on_final_chunk(text: str) -> None:
    #         if text:
    #             await out_queue.put(("chunk", text))

    #     async def run_deep_search() -> None:
    #         try:
    #             result = await deep_search(
    #                 db,
    #                 session.notebook_id,
    #                 body.content,
    #                 source_ids=body.source_ids,
    #                 conversation_style=body.conversation_style,
    #                 custom_prompt=body.custom_prompt,
    #                 answer_length=body.answer_length,
    #                 user_id=user.username,
    #                 session_id=session_id,
    #                 on_search_step=on_search_step,
    #                 on_final_chunk=on_final_chunk,
    #             )
    #             await out_queue.put(("result", result))
    #         except Exception as exc:
    #             logger.exception("SSE stream error")
    #             await out_queue.put(("error", str(exc)))
    #         finally:
    #             await out_queue.put(None)

    #     worker = asyncio.create_task(run_deep_search())
    #     try:
    #         while True:
    #             item = await out_queue.get()
    #             if item is None:
    #                 break
    #             kind, payload = item
    #             if kind == "step":
    #                 yield (
    #                     "data: "
    #                     + json.dumps(
    #                         {"type": "step", "data": payload},
    #                         ensure_ascii=False,
    #                     )
    #                     + "\n\n"
    #                 )
    #             elif kind == "chunk":
    #                 yield (
    #                     "data: "
    #                     + json.dumps(
    #                         {"type": "chunk", "data": {"content": payload}},
    #                         ensure_ascii=False,
    #                     )
    #                     + "\n\n"
    #                 )
    #             elif kind == "error":
    #                 yield (
    #                     "data: "
    #                     + json.dumps(
    #                         {"type": "error", "data": {"message": payload}},
    #                         ensure_ascii=False,
    #                     )
    #                     + "\n\n"
    #                 )
    #                 return
    #             elif kind == "result":
    #                 result = payload
    #                 assistant_msg = Message(
    #                     session_id=session.id,
    #                     role="assistant",
    #                     content=result["content"],
    #                     citations=result["citations"],
    #                 )
    #                 db.add(assistant_msg)
    #                 await db.flush()
    #                 await db.refresh(assistant_msg)

    #                 msg_data = MessageResponse.model_validate(
    #                     assistant_msg
    #                 ).model_dump(mode="json")
    #                 yield (
    #                     "data: "
    #                     + json.dumps(
    #                         {"type": "answer", "data": msg_data},
    #                         ensure_ascii=False,
    #                     )
    #                     + "\n\n"
    #                 )
    #                 yield "data: {\"type\": \"done\"}\n\n"
    #                 return
    #     finally:
    #         await worker

    # return StreamingResponse(
    #     event_generator(),
    #     media_type="text/event-stream",
    #     headers={
    #         "Cache-Control": "no-cache",
    #         "Connection": "keep-alive",
    #         "X-Accel-Buffering": "no",
    #     },
    # )


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
