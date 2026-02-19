"""Studio API routes: Mind Map, Slide Deck, Infographic, Reports."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.notebook import Notebook
from app.models.studio import Infographic, MindMap, SlideDeck
from app.models.user import User
from app.schemas.studio import (
    InfographicCreate,
    InfographicResponse,
    InfographicUpdate,
    MindMapCreate,
    MindMapResponse,
    SlideDeckCreate,
    SlideDeckResponse,
    SlideDeckUpdate,
)

from app.services.mindmap_service import generate_mindmap_from_sources
from app.services.obs_storage import generate_presigned_url
from app.services.slide_service import generate_slide_deck

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(tags=["studio"])


# ── Mind Map ────────────────────────────────────────────────────────────

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


# ── Slide Deck ──────────────────────────────────────────────────────────

@router.post(
    "/api/notebooks/{notebook_id}/slides",
    response_model=SlideDeckResponse,
    status_code=201,
)
async def generate_slides(
    notebook_id: str,
    body: SlideDeckCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate a slide deck from notebook sources (content -> PPT -> images -> PDF)."""
    await _verify_notebook_access(db, notebook_id, user.id)
    slide_deck = await generate_slide_deck(
        db=db,
        notebook_id=notebook_id,
        title=body.title,
        theme=body.theme,
        source_ids=body.source_ids,
        focus_topic=body.focus_topic,
    )
    return SlideDeckResponse.model_validate(slide_deck)


@router.get(
    "/api/notebooks/{notebook_id}/slides",
    response_model=list[SlideDeckResponse],
)
async def list_slides(
    notebook_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List slide decks in a notebook."""
    await _verify_notebook_access(db, notebook_id, user.id)
    result = await db.execute(
        select(SlideDeck)
        .where(SlideDeck.notebook_id == notebook_id)
        .order_by(SlideDeck.created_at.desc())
    )
    return [
        SlideDeckResponse.model_validate(s)
        for s in result.scalars().all()
    ]


@router.get("/api/slides/{slide_id}", response_model=SlideDeckResponse)
async def get_slide(
    slide_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a slide deck by ID."""
    slide = await _get_slide(db, slide_id, user.id)
    return SlideDeckResponse.model_validate(slide)


@router.get("/api/slides/{slide_id}/pdf-url")
async def get_slide_pdf_url(
    slide_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a presigned URL for the slide deck PDF stored in OBS."""
    slide = await _get_slide(db, slide_id, user.id)
    if not slide.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF not available for this slide deck",
        )
    url = generate_presigned_url(slide.file_path, expiration=3600)
    return {"url": url}


@router.put("/api/slides/{slide_id}", response_model=SlideDeckResponse)
async def update_slide(
    slide_id: str,
    body: SlideDeckUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update a slide deck."""
    slide = await _get_slide(db, slide_id, user.id)
    if body.title is not None:
        slide.title = body.title
    if body.theme is not None:
        slide.theme = body.theme
    if body.slides_data is not None:
        slide.slides_data = body.slides_data
    await db.flush()
    await db.refresh(slide)
    return SlideDeckResponse.model_validate(slide)


@router.delete("/api/slides/{slide_id}", status_code=204)
async def delete_slide(
    slide_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a slide deck."""
    slide = await _get_slide(db, slide_id, user.id)
    await db.delete(slide)


# ── Infographic ─────────────────────────────────────────────────────────

@router.post(
    "/api/notebooks/{notebook_id}/infographics",
    response_model=InfographicResponse,
    status_code=201,
)
async def generate_infographic(
    notebook_id: str,
    body: InfographicCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate an infographic from notebook sources."""
    await _verify_notebook_access(db, notebook_id, user.id)
    infographic = Infographic(
        notebook_id=notebook_id,
        title=body.title,
        template_type=body.template_type,
        layout_data={"sections": []},  # placeholder
        status="pending",
    )
    db.add(infographic)
    await db.flush()
    await db.refresh(infographic)
    return InfographicResponse.model_validate(infographic)


@router.get(
    "/api/notebooks/{notebook_id}/infographics",
    response_model=list[InfographicResponse],
)
async def list_infographics(
    notebook_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List infographics in a notebook."""
    await _verify_notebook_access(db, notebook_id, user.id)
    result = await db.execute(
        select(Infographic)
        .where(Infographic.notebook_id == notebook_id)
        .order_by(Infographic.created_at.desc())
    )
    return [
        InfographicResponse.model_validate(i)
        for i in result.scalars().all()
    ]


@router.get(
    "/api/infographics/{infographic_id}",
    response_model=InfographicResponse,
)
async def get_infographic(
    infographic_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get an infographic by ID."""
    infographic = await _get_infographic(db, infographic_id, user.id)
    return InfographicResponse.model_validate(infographic)


@router.put(
    "/api/infographics/{infographic_id}",
    response_model=InfographicResponse,
)
async def update_infographic(
    infographic_id: str,
    body: InfographicUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update an infographic."""
    infographic = await _get_infographic(db, infographic_id, user.id)
    if body.title is not None:
        infographic.title = body.title
    if body.template_type is not None:
        infographic.template_type = body.template_type
    if body.layout_data is not None:
        infographic.layout_data = body.layout_data
    await db.flush()
    await db.refresh(infographic)
    return InfographicResponse.model_validate(infographic)


@router.delete("/api/infographics/{infographic_id}", status_code=204)
async def delete_infographic(
    infographic_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete an infographic."""
    infographic = await _get_infographic(db, infographic_id, user.id)
    await db.delete(infographic)


# ── Reports (placeholder) ──────────────────────────────────────────────

@router.post("/api/notebooks/{notebook_id}/reports")
async def generate_report(
    notebook_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate a report from notebook sources (placeholder)."""
    await _verify_notebook_access(db, notebook_id, user.id)
    return {"status": "not_implemented", "message": "Reports coming soon"}


# ── Helpers ─────────────────────────────────────────────────────────────

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


async def _get_slide(
    db: AsyncSession, slide_id: str, user_id: str
) -> SlideDeck:
    """Get a slide deck and verify user access."""
    result = await db.execute(
        select(SlideDeck)
        .join(Notebook, SlideDeck.notebook_id == Notebook.id)
        .where(SlideDeck.id == slide_id, Notebook.user_id == user_id)
    )
    slide = result.scalar_one_or_none()
    if slide is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slide deck not found",
        )
    return slide


async def _get_infographic(
    db: AsyncSession, infographic_id: str, user_id: str
) -> Infographic:
    """Get an infographic and verify user access."""
    result = await db.execute(
        select(Infographic)
        .join(Notebook, Infographic.notebook_id == Notebook.id)
        .where(
            Infographic.id == infographic_id, Notebook.user_id == user_id
        )
    )
    infographic = result.scalar_one_or_none()
    if infographic is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Infographic not found",
        )
    return infographic
