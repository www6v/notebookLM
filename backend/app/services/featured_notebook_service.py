"""Load curated featured notebook share links."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from notebooklm_shared.models.featured_notebook_link import FeaturedNotebookLink
from notebooklm_shared.models.notebook import Notebook
from notebooklm_shared.models.source import Source
from app.schemas.featured_notebook import FeaturedNotebookPublicItem


async def list_links_ordered(db: AsyncSession) -> list[FeaturedNotebookLink]:
    """Return all featured rows in display order."""
    result = await db.execute(
        select(FeaturedNotebookLink).order_by(
            FeaturedNotebookLink.sort_order.asc(),
            FeaturedNotebookLink.created_at.asc(),
        )
    )
    return list(result.scalars().all())


async def get_public_items(
    db: AsyncSession,
) -> list[FeaturedNotebookPublicItem]:
    """Resolve tokens to notebook metadata; skip missing or invalid tokens."""
    links = await list_links_ordered(db)
    if not links:
        return []
    out: list[FeaturedNotebookPublicItem] = []
    for link in links:
        token = link.share_token.strip()
        nb_row = await db.execute(
            select(Notebook).where(Notebook.share_token == token)
        )
        nb = nb_row.scalar_one_or_none()
        if nb is None:
            continue
        cnt = (
            await db.execute(
                select(func.count(Source.id)).where(Source.notebook_id == nb.id)
            )
        ).scalar_one()
        title = (link.custom_title or "").strip() or nb.title
        out.append(
            FeaturedNotebookPublicItem(
                share_token=token,
                title=title,
                source_count=int(cnt),
                created_at=nb.created_at,
            )
        )
    return out
