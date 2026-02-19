"""Mind map API routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.notebook import Notebook
from app.models.studio import MindMap
from app.models.user import User
from app.schemas.studio import MindMapCreate, MindMapResponse
from app.services.mindmap_service import generate_mindmap_from_sources

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
    status_code=201,
)
async def generate_mindmap(
    notebook_id: str,
    body: MindMapCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate a mind map from notebook sources via LLM."""
    await _verify_notebook_access(db, notebook_id, user.id)
    logger.info("generate_mindmap: notebook_id=%s, body=%s", notebook_id, body)
    mind_map = await generate_mindmap_from_sources(
        db=db,
        notebook_id=notebook_id,
        title=body.title,
        source_ids=body.source_ids,
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
    return [
        MindMapResponse.model_validate(m)
        for m in result.scalars().all()
    ]


@router.get("/api/mindmaps/{mindmap_id}", response_model=MindMapResponse)
async def get_mindmap(
    mindmap_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a mind map by ID."""
    mind_map = await _get_mindmap(db, mindmap_id, user.id)
    return MindMapResponse.model_validate(mind_map)


@router.delete("/api/mindmaps/{mindmap_id}", status_code=204)
async def delete_mindmap(
    mindmap_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a mind map."""
    mind_map = await _get_mindmap(db, mindmap_id, user.id)
    await db.delete(mind_map)
