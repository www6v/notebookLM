"""Streaming task events for long-running async jobs."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.api.deps import get_current_user
from notebooklm_shared.database import async_session
from notebooklm_shared.models.notebook import Notebook
from notebooklm_shared.models.source import Source
from notebooklm_shared.models.studio import (
    DeepResearchReport,
    Infographic,
    MindMap,
    PodcastOverview,
    Report,
    SlideDeck,
)
from notebooklm_shared.models.user import User
from app.services.task_event_service import (
    TERMINAL_TASK_STATUSES,
    subscribe_task_events,
)

router = APIRouter(tags=["task-events"])

RESOURCE_MODELS = {
    "source": Source,
    "mindmap": MindMap,
    "slide": SlideDeck,
    "infographic": Infographic,
    "report": Report,
    "podcast": PodcastOverview,
    "deep-research": DeepResearchReport,
}


async def _load_task_state(
    resource_type: str,
    resource_id: str,
    user_id: str,
) -> dict[str, str | None]:
    """Load a task resource and verify ownership through its notebook."""
    model = RESOURCE_MODELS.get(resource_type)
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task resource type not supported",
        )

    async with async_session() as db:
        result = await db.execute(
            select(model)
            .join(Notebook, model.notebook_id == Notebook.id)
            .where(model.id == resource_id, Notebook.user_id == user_id)
        )
        record = result.scalar_one_or_none()
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task resource not found",
            )
        return {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "status": getattr(record, "status", None),
            "error_message": getattr(record, "error_message", None),
        }


@router.get("/api/task-events/{resource_type}/{resource_id}/stream")
async def stream_task_events(
    resource_type: str,
    resource_id: str,
    user: User = Depends(get_current_user),
):
    """Stream task status transitions over SSE."""

    async def event_generator():
        pubsub = await subscribe_task_events(resource_type, resource_id)
        last_payload: dict[str, str | None] | None = None
        try:
            current = await _load_task_state(resource_type, resource_id, user.id)
            last_payload = current
            yield f"data: {json.dumps(current, ensure_ascii=False)}\n\n"
            if current["status"] in TERMINAL_TASK_STATUSES:
                return

            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=15.0,
                )
                if message is None:
                    current = await _load_task_state(resource_type, resource_id, user.id)
                    if current != last_payload:
                        last_payload = current
                        yield f"data: {json.dumps(current, ensure_ascii=False)}\n\n"
                    else:
                        yield ": keepalive\n\n"
                    if current["status"] in TERMINAL_TASK_STATUSES:
                        return
                    continue

                payload = json.loads(message["data"])
                last_payload = {
                    "resource_type": payload.get("resource_type"),
                    "resource_id": payload.get("resource_id"),
                    "status": payload.get("status"),
                    "error_message": payload.get("error_message"),
                }
                yield f"data: {json.dumps(last_payload, ensure_ascii=False)}\n\n"
                if payload.get("status") in TERMINAL_TASK_STATUSES:
                    return
        finally:
            await pubsub.unsubscribe()
            if hasattr(pubsub, "aclose"):
                await pubsub.aclose()
            else:
                await pubsub.close()
            redis_client = getattr(pubsub, "_task_event_redis_client", None)
            if redis_client is not None:
                await redis_client.aclose()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
