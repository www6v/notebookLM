"""Count in-flight Studio generations per user from the database."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from notebooklm_shared.models.notebook import Notebook
from notebooklm_shared.models.studio import (
    DeepResearchReport,
    Infographic,
    MindMap,
    PodcastOverview,
    Report,
    SlideDeck,
)
from app.services.studio.studio_status_service import PENDING_GENERATION_STATUSES


async def count_inflight_generations(db: AsyncSession, user_id: str) -> int:
    """Count rows in pending/processing across all Studio tables for this user."""
    total = 0
    models = (
        MindMap,
        SlideDeck,
        Infographic,
        Report,
        PodcastOverview,
        DeepResearchReport,
    )
    statuses = tuple(PENDING_GENERATION_STATUSES)
    for model in models:
        stmt = (
            select(func.count())
            .select_from(model)
            .join(Notebook, model.notebook_id == Notebook.id)
            .where(
                Notebook.user_id == user_id,
                model.status.in_(statuses),
            )
        )
        result = await db.execute(stmt)
        total += result.scalar_one()
    return total
