"""Load and update curated featured notebook share links."""

from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.featured_notebook_link import FeaturedNotebookLink
from app.models.notebook import Notebook
from app.models.source import Source
from app.schemas.featured_notebook import (
    FeaturedNotebookAdminItem,
    FeaturedNotebookEntryInput,
    FeaturedNotebookPublicItem,
)


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


async def get_admin_items(db: AsyncSession) -> list[FeaturedNotebookAdminItem]:
    """Return all links with resolution status for the admin UI."""
    links = await list_links_ordered(db)
    out: list[FeaturedNotebookAdminItem] = []
    for link in links:
        token = link.share_token.strip()
        nb_row = await db.execute(
            select(Notebook).where(Notebook.share_token == token)
        )
        nb = nb_row.scalar_one_or_none()
        if nb is None:
            out.append(
                FeaturedNotebookAdminItem(
                    share_token=token,
                    custom_title=link.custom_title,
                    sort_order=link.sort_order,
                    notebook_found=False,
                    resolved_title=None,
                    source_count=None,
                    notebook_created_at=None,
                )
            )
            continue
        cnt = (
            await db.execute(
                select(func.count(Source.id)).where(Source.notebook_id == nb.id)
            )
        ).scalar_one()
        resolved = nb.title
        out.append(
            FeaturedNotebookAdminItem(
                share_token=token,
                custom_title=link.custom_title,
                sort_order=link.sort_order,
                notebook_found=True,
                resolved_title=resolved,
                source_count=int(cnt),
                notebook_created_at=nb.created_at,
            )
        )
    return out


async def replace_all(
    db: AsyncSession, items: list[FeaturedNotebookEntryInput]
) -> None:
    """Delete existing rows and insert the new ordered list."""
    normalized: list[tuple[str, str | None]] = []
    for item in items:
        t = item.share_token.strip()
        if not t:
            continue
        ct = item.custom_title
        if ct is not None:
            ct = ct.strip() or None
        normalized.append((t, ct))
    token_set = {t for t, _ in normalized}
    if len(token_set) != len(normalized):
        raise ValueError("Duplicate share_token in request")
    await db.execute(delete(FeaturedNotebookLink))
    await db.flush()
    for order, (t, ct) in enumerate(normalized):
        db.add(
            FeaturedNotebookLink(
                share_token=t,
                sort_order=order,
                custom_title=ct,
            )
        )
    await db.flush()
