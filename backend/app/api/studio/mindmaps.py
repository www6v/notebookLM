"""Mind map API routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from notebooklm_shared.database import get_db
from notebooklm_shared.models.notebook import Notebook
from app.ratelimit import (
    GenerationKind,
    acquire_generation_rate_limit_slot,
    release_generation_rate_limit_on_db_failure,
)
from notebooklm_shared.models.studio import MindMap
from notebooklm_shared.models.user import User
from app.schemas.studio import MindMapCreate, MindMapResponse, MindMapStatus
from app.services.studio.studio_status_service import (
    reconcile_stale_generation,
    reconcile_stale_generations,
)
from app.services.task_event_service import publish_task_event
from app.tasks.studio_tasks import generate_mindmap_task

logger = logging.getLogger(__name__)

router = APIRouter(tags=["mindmaps"])


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


async def _get_mindmap(
    db: AsyncSession, mindmap_id: str, user_id: str
) -> MindMap:
    """Get a mind map and verify user access."""
    result = await db.execute(
        select(MindMap)
        .join(Notebook, MindMap.notebook_id == Notebook.id)
        .where(MindMap.id == mindmap_id, Notebook.user_id == user_id)
    )
    mind_map = result.scalar_one_or_none()
    if mind_map is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mind map not found",
        )
    return mind_map


@router.post(
    "/api/notebooks/{notebook_id}/mindmap",
    response_model=MindMapResponse,
    status_code=202,
)
async def generate_mindmap(
    notebook_id: str,
    body: MindMapCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a pending mind map and run generation in background. Returns 202."""
    await _verify_notebook_access(db, notebook_id, user.id)
    logger.info("generate_mindmap: notebook_id=%s, body=%s", notebook_id, body)
    rl_redis, acquired, _, _ = await acquire_generation_rate_limit_slot(
        db,
        user_id=user.id,
        kind=GenerationKind.MINDMAP,
        notebook_id=notebook_id,
        source_ids=body.source_ids,
        artifact_id=None,
    )
    try:
        source_count = len(body.source_ids) if body.source_ids else 0
        mind_map = MindMap(
            notebook_id=notebook_id,
            title=body.title,
            graph_data=None,
            status=MindMapStatus.PENDING.value,
            error_message=None,
            output_language=body.output_language,
            source_count=source_count if source_count > 0 else None,
        )
        db.add(mind_map)
        await db.flush()
        await db.refresh(mind_map)
        await db.commit()
    except Exception:
        await db.rollback()
        await release_generation_rate_limit_on_db_failure(
            rl_redis,
            acquired,
            user_id=user.id,
            daily_slide_reserved=False,
            daily_deep_research_reserved=False,
        )
        raise
    finally:
        await rl_redis.aclose()

    await publish_task_event("mindmap", mind_map.id, mind_map.status)
    generate_mindmap_task.delay(
        mind_map.id,
        notebook_id,
        body.title,
        body.source_ids,
    )
    return MindMapResponse.model_validate(mind_map)


@router.get(
    "/api/notebooks/{notebook_id}/mindmaps",
    response_model=list[MindMapResponse],
)
async def list_mindmaps(
    notebook_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List mind maps in a notebook."""
    await _verify_notebook_access(db, notebook_id, user.id)
    result = await db.execute(
        select(MindMap)
        .where(MindMap.notebook_id == notebook_id)
        .order_by(MindMap.created_at.desc())
    )
    mind_maps = result.scalars().all()
    if reconcile_stale_generations(mind_maps):
        await db.flush()
    return [
        MindMapResponse.model_validate(m)
        for m in mind_maps
    ]


@router.get("/api/mindmaps/{mindmap_id}", response_model=MindMapResponse)
async def get_mindmap(
    mindmap_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a mind map by ID."""
    mind_map = await _get_mindmap(db, mindmap_id, user.id)
    if reconcile_stale_generation(mind_map):
        await db.flush()
    return MindMapResponse.model_validate(mind_map)


@router.delete("/api/mindmaps/{mindmap_id}", status_code=204)
async def delete_mindmap(
    mindmap_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a mind map (graph is stored in DB only; no object storage)."""
    mind_map = await _get_mindmap(db, mindmap_id, user.id)
    await db.delete(mind_map)
