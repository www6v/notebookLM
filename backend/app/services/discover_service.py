"""Discover catalog: publish, list, detail, subscribe / unsubscribe."""

from __future__ import annotations

import secrets

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.discover import (
    DiscoverNotebookDetail,
    DiscoverNotebookListItem,
    DiscoverPublishBody,
)
from notebooklm_shared.models.notebook import Notebook
from notebooklm_shared.models.notebook_discover_profile import (
    NotebookDiscoverProfile,
)
from notebooklm_shared.models.notebook_subscription import NotebookSubscription
from notebooklm_shared.models.source import Source
from notebooklm_shared.models.user import User


def owner_display_name(user: User) -> str:
    """Public label for notebook owner (spec: @handle style)."""
    name = (user.username or "").strip()
    if name:
        return f"@{name}"
    local = (user.email or "").split("@", 1)[0].strip()
    return f"@{local}" if local else "@user"


async def _allocate_share_token(db: AsyncSession) -> str:
    """Allocate a unique share_token (same rules as notebooks API)."""
    for _ in range(20):
        token = secrets.token_urlsafe(32)
        exists = await db.execute(
            select(Notebook.id).where(Notebook.share_token == token).limit(1)
        )
        if exists.scalar_one_or_none() is None:
            return token
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Could not allocate share token",
    )


def _like_pattern(term: str) -> str:
    """Build LIKE pattern with escapes for % and _ ."""
    escaped = (
        term.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )
    return f"%{escaped}%"


async def _get_owned_notebook(
    db: AsyncSession,
    notebook_id: str,
    user_id: str,
) -> Notebook:
    result = await db.execute(
        select(Notebook).where(
            Notebook.id == notebook_id,
            Notebook.user_id == user_id,
        )
    )
    notebook = result.scalar_one_or_none()
    if notebook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        )
    return notebook


async def publish_notebook(
    db: AsyncSession,
    user_id: str,
    notebook_id: str,
    body: DiscoverPublishBody,
) -> None:
    """Publish owner's notebook to discover (ensures share_token)."""
    notebook = await _get_owned_notebook(db, notebook_id, user_id)
    if notebook.share_token is None:
        notebook.share_token = await _allocate_share_token(db)
        await db.flush()

    profile = await db.get(NotebookDiscoverProfile, notebook_id)
    if profile is None:
        profile = NotebookDiscoverProfile(
            notebook_id=notebook_id,
            category=body.category,
            cover_url=body.cover_url,
            subscriber_count=0,
        )
        db.add(profile)
    else:
        profile.category = body.category
        profile.cover_url = body.cover_url
    await db.flush()


async def unpublish_notebook(
    db: AsyncSession,
    user_id: str,
    notebook_id: str,
) -> None:
    """Remove discover profile; keep subscriptions (spec §6)."""
    await _get_owned_notebook(db, notebook_id, user_id)
    profile = await db.get(NotebookDiscoverProfile, notebook_id)
    if profile is not None:
        await db.delete(profile)
        await db.flush()


async def list_discoverable(
    db: AsyncSession,
    q: str | None,
    category: str | None,
    offset: int,
    limit: int,
) -> tuple[list[DiscoverNotebookListItem], int]:
    """List discoverable notebooks (share_token set + profile row)."""
    source_count_sub = (
        select(
            Source.notebook_id,
            func.count(Source.id).label("source_count"),
        )
        .group_by(Source.notebook_id)
        .subquery()
    )

    filters = [
        Notebook.share_token.isnot(None),
    ]
    if category and category.strip() and category.strip().lower() != "all":
        filters.append(
            NotebookDiscoverProfile.category == category.strip(),
        )
    if q and q.strip():
        term = _like_pattern(q.strip())
        filters.append(
            or_(
                Notebook.title.ilike(term, escape="\\"),
                Notebook.description.ilike(term, escape="\\"),
            )
        )

    count_stmt = (
        select(func.count(Notebook.id))
        .select_from(Notebook)
        .join(
            NotebookDiscoverProfile,
            NotebookDiscoverProfile.notebook_id == Notebook.id,
        )
        .where(*filters)
    )
    count_result = await db.execute(count_stmt)
    total = int(count_result.scalar_one())

    stmt = (
        select(
            Notebook,
            NotebookDiscoverProfile,
            User,
            func.coalesce(source_count_sub.c.source_count, 0),
        )
        .join(
            NotebookDiscoverProfile,
            NotebookDiscoverProfile.notebook_id == Notebook.id,
        )
        .join(User, User.id == Notebook.user_id)
        .outerjoin(
            source_count_sub,
            Notebook.id == source_count_sub.c.notebook_id,
        )
        .where(*filters)
        .order_by(Notebook.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = (await db.execute(stmt)).all()

    items: list[DiscoverNotebookListItem] = []
    for nb, prof, owner, src_count in rows:
        items.append(
            DiscoverNotebookListItem(
                id=nb.id,
                title=nb.title,
                description=nb.description or "",
                category=prof.category,
                cover_url=prof.cover_url,
                subscriber_count=int(prof.subscriber_count),
                source_count=int(src_count),
                owner_display_name=owner_display_name(owner),
            )
        )
    return items, total


async def get_discover_detail(
    db: AsyncSession,
    notebook_id: str,
) -> DiscoverNotebookDetail | None:
    """Return public detail or None if not discoverable."""
    source_count_sub = (
        select(
            Source.notebook_id,
            func.count(Source.id).label("source_count"),
        )
        .group_by(Source.notebook_id)
        .subquery()
    )

    stmt = (
        select(
            Notebook,
            NotebookDiscoverProfile,
            User,
            func.coalesce(source_count_sub.c.source_count, 0),
        )
        .join(
            NotebookDiscoverProfile,
            NotebookDiscoverProfile.notebook_id == Notebook.id,
        )
        .join(User, User.id == Notebook.user_id)
        .outerjoin(
            source_count_sub,
            Notebook.id == source_count_sub.c.notebook_id,
        )
        .where(
            Notebook.id == notebook_id,
            Notebook.share_token.isnot(None),
        )
    )
    row = (await db.execute(stmt)).one_or_none()
    if row is None:
        return None
    nb, prof, owner, src_count = row
    return DiscoverNotebookDetail(
        id=nb.id,
        title=nb.title,
        description=nb.description or "",
        category=prof.category,
        cover_url=prof.cover_url,
        subscriber_count=int(prof.subscriber_count),
        source_count=int(src_count),
        owner_display_name=owner_display_name(owner),
        share_token=nb.share_token,
    )


async def subscribe(
    db: AsyncSession,
    subscriber_id: str,
    notebook_id: str,
) -> None:
    """Subscribe current user to a discoverable notebook."""
    notebook = await db.get(Notebook, notebook_id)
    if notebook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        )
    if notebook.user_id == subscriber_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot subscribe to your own notebook",
        )
    if notebook.share_token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Notebook is not publicly readable",
        )

    profile = await db.get(NotebookDiscoverProfile, notebook_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook is not on discover",
        )

    existing = await db.execute(
        select(NotebookSubscription.id).where(
            NotebookSubscription.subscriber_user_id == subscriber_id,
            NotebookSubscription.notebook_id == notebook_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        return

    db.add(
        NotebookSubscription(
            subscriber_user_id=subscriber_id,
            notebook_id=notebook_id,
        )
    )
    profile.subscriber_count = int(profile.subscriber_count) + 1
    await db.flush()


async def unsubscribe(
    db: AsyncSession,
    subscriber_id: str,
    notebook_id: str,
) -> None:
    """Remove subscription; decrement profile counter when profile exists."""
    result = await db.execute(
        select(NotebookSubscription).where(
            NotebookSubscription.subscriber_user_id == subscriber_id,
            NotebookSubscription.notebook_id == notebook_id,
        )
    )
    sub = result.scalar_one_or_none()
    if sub is None:
        return

    await db.delete(sub)
    profile = await db.get(NotebookDiscoverProfile, notebook_id)
    if profile is not None:
        profile.subscriber_count = max(0, int(profile.subscriber_count) - 1)
    await db.flush()
