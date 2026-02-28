"""Slide Deck API routes."""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import async_session, get_db
from app.models.notebook import Notebook
from app.models.studio import SlideDeck
from app.models.user import User
from app.schemas.studio import (
    SlideDeckCreate,
    SlideDeckResponse,
    SlideDeckStatus,
    SlideDeckUpdate,
)
from app.services.obs_storage import generate_presigned_url
from app.services.slide_service import run_slide_deck_generation_for_existing

logger = logging.getLogger(__name__)
router = APIRouter(tags=["studio"])


async def _run_slide_deck_generation_background(
    slide_deck_id: str,
    source_ids: list[str] | None = None,
    focus_topic: str | None = None,
):
    """Run slide deck generation in background with its own DB session."""
    async with async_session() as session:
        try:
            await run_slide_deck_generation_for_existing(
                session,
                slide_deck_id,
                source_ids=source_ids,
                focus_topic=focus_topic,
            )
            await session.commit()
        except Exception as e:
            logger.exception("Slide deck background generation failed: %s", e)
            await session.rollback()


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


@router.post(
    "/api/notebooks/{notebook_id}/slides",
    response_model=SlideDeckResponse,
    status_code=202,
)
async def generate_slides(
    notebook_id: str,
    body: SlideDeckCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a pending slide deck and run generation in background. Returns 202."""
    await _verify_notebook_access(db, notebook_id, user.id)

    slide_deck = SlideDeck(
        notebook_id=notebook_id,
        title=body.title,
        theme=body.theme,
        slides_data=None,
        status=SlideDeckStatus.PENDING.value,
        file_path=None,
        slide_style=body.slide_style or "detailed",
        slide_language=body.slide_language or "简体中文",
        slide_duration=body.slide_duration or "default",
        slide_custom_prompt=body.slide_custom_prompt,
    )
    db.add(slide_deck)
    await db.flush()
    await db.refresh(slide_deck)
    await db.commit()

    background_tasks.add_task(
        _run_slide_deck_generation_background,
        slide_deck.id,
        body.source_ids,
        body.focus_topic,
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
    if body.slide_style is not None:
        slide.slide_style = body.slide_style
    if body.slide_language is not None:
        slide.slide_language = body.slide_language
    if body.slide_duration is not None:
        slide.slide_duration = body.slide_duration
    if body.slide_custom_prompt is not None:
        slide.slide_custom_prompt = body.slide_custom_prompt
    await db.flush()
    await db.refresh(slide)
    return SlideDeckResponse.model_validate(slide)


@router.post(
    "/api/slides/{slide_id}/regenerate",
    response_model=SlideDeckResponse,
    status_code=202,
)
async def regenerate_slide(
    slide_id: str,
    body: SlideDeckUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update slide options and re-run generation in background. Returns 202."""
    slide = await _get_slide(db, slide_id, user.id)
    if body.title is not None:
        slide.title = body.title
    if body.theme is not None:
        slide.theme = body.theme
    if body.slide_style is not None:
        slide.slide_style = body.slide_style
    if body.slide_language is not None:
        slide.slide_language = body.slide_language
    if body.slide_duration is not None:
        slide.slide_duration = body.slide_duration
    if body.slide_custom_prompt is not None:
        slide.slide_custom_prompt = body.slide_custom_prompt
    slide.status = SlideDeckStatus.PENDING.value
    slide.slides_data = None
    slide.file_path = None
    await db.flush()
    await db.refresh(slide)
    await db.commit()
    background_tasks.add_task(_run_slide_deck_generation_background, slide.id)
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
