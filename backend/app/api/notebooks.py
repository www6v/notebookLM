"""Notebook CRUD API routes."""

import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from notebooklm_shared.database import get_db
from app.limits import ROLE_LIMITS
from notebooklm_shared.models.notebook import Notebook
from notebooklm_shared.models.notebook_discover_profile import (
    NotebookDiscoverProfile,
)
from notebooklm_shared.models.notebook_subscription import NotebookSubscription
from notebooklm_shared.models.source import Source
from notebooklm_shared.models.user import User
from app.schemas.discover import DiscoverPublishBody
from app.schemas.notebook import (
    NotebookCreate,
    NotebookListResponse,
    NotebookResponse,
    NotebookShareBody,
    NotebookShareLinkResponse,
    NotebookSubscriptionItem,
    NotebookSubscriptionsListResponse,
    NotebookUpdate,
)
from app.services import discover_service as discover_svc

router = APIRouter(prefix="/api/notebooks", tags=["notebooks"])


def _notebook_response(notebook: Notebook, source_count: int = 0) -> NotebookResponse:
    """Build API response including share_enabled (not an ORM column)."""
    return NotebookResponse.model_validate(notebook).model_copy(
        update={
            "source_count": source_count,
            "share_enabled": notebook.share_token is not None,
        }
    )


async def _new_unique_share_token(db: AsyncSession) -> str:
    """Generate a share_token not yet present in notebooks."""
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


@router.get("", response_model=NotebookListResponse)
async def list_notebooks(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all notebooks for the current user."""
    # Sub-query for source count
    source_count_sub = (
        select(
            Source.notebook_id,
            func.count(Source.id).label("source_count"),
        )
        .group_by(Source.notebook_id)
        .subquery()
    )

    query = (
        select(Notebook, func.coalesce(source_count_sub.c.source_count, 0))
        .outerjoin(
            source_count_sub,
            Notebook.id == source_count_sub.c.notebook_id,
        )
        .where(Notebook.user_id == user.id)
        .order_by(Notebook.updated_at.desc())
    )
    result = await db.execute(query)
    rows = result.all()

    notebooks = [_notebook_response(nb, count) for nb, count in rows]

    return NotebookListResponse(notebooks=notebooks, total=len(notebooks))


@router.get("/published", response_model=NotebookListResponse)
async def list_published_notebooks(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List current user's notebooks that are on discover."""
    source_count_sub = (
        select(
            Source.notebook_id,
            func.count(Source.id).label("source_count"),
        )
        .group_by(Source.notebook_id)
        .subquery()
    )
    query = (
        select(Notebook, func.coalesce(source_count_sub.c.source_count, 0))
        .outerjoin(
            source_count_sub,
            Notebook.id == source_count_sub.c.notebook_id,
        )
        .join(
            NotebookDiscoverProfile,
            NotebookDiscoverProfile.notebook_id == Notebook.id,
        )
        .where(Notebook.user_id == user.id)
        .order_by(Notebook.updated_at.desc())
    )
    result = await db.execute(query)
    rows = result.all()
    notebooks = [_notebook_response(nb, int(count)) for nb, count in rows]
    return NotebookListResponse(notebooks=notebooks, total=len(notebooks))


@router.get("/subscriptions", response_model=NotebookSubscriptionsListResponse)
async def list_subscribed_notebooks(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List notebooks the current user subscribed to (read via share_token)."""
    source_count_sub = (
        select(
            Source.notebook_id,
            func.count(Source.id).label("source_count"),
        )
        .group_by(Source.notebook_id)
        .subquery()
    )
    stmt = (
        select(Notebook, func.coalesce(source_count_sub.c.source_count, 0))
        .select_from(NotebookSubscription)
        .join(Notebook, NotebookSubscription.notebook_id == Notebook.id)
        .outerjoin(
            source_count_sub,
            Notebook.id == source_count_sub.c.notebook_id,
        )
        .where(NotebookSubscription.subscriber_user_id == user.id)
        .order_by(NotebookSubscription.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    items: list[NotebookSubscriptionItem] = []
    for nb, count in rows:
        read_available = nb.share_token is not None
        items.append(
            NotebookSubscriptionItem(
                notebook=_notebook_response(nb, int(count)),
                read_available=read_available,
                share_token=nb.share_token,
            )
        )
    return NotebookSubscriptionsListResponse(items=items, total=len(items))


@router.post("", response_model=NotebookResponse, status_code=201)
async def create_notebook(
    body: NotebookCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new notebook."""
    limits = ROLE_LIMITS.get(user.role, ROLE_LIMITS["free"])
    count_result = await db.execute(
        select(func.count(Notebook.id)).where(Notebook.user_id == user.id)
    )
    current_count = count_result.scalar_one()
    if current_count >= limits["max_notebooks"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"已达到笔记本数量上限（{limits['max_notebooks']}）。"
                "请升级账户以创建更多笔记本。"
            ),
        )

    notebook = Notebook(
        user_id=user.id,
        title=body.title,
        description=body.description,
    )
    db.add(notebook)
    await db.flush()
    await db.refresh(notebook)
    return _notebook_response(notebook)


@router.get("/{notebook_id}", response_model=NotebookResponse)
async def get_notebook(
    notebook_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a single notebook by ID."""
    notebook = await _get_user_notebook(db, notebook_id, user.id)
    source_count_result = await db.execute(
        select(func.count(Source.id)).where(Source.notebook_id == notebook.id)
    )
    return _notebook_response(
        notebook, source_count=source_count_result.scalar_one()
    )


@router.post(
    "/{notebook_id}/share",
    response_model=NotebookShareLinkResponse,
)
async def enable_or_rotate_notebook_share(
    notebook_id: str,
    body: NotebookShareBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a public read-only link or rotate its token."""
    notebook = await _get_user_notebook(db, notebook_id, user.id)
    if body.regenerate or notebook.share_token is None:
        notebook.share_token = await _new_unique_share_token(db)
        await db.flush()
        await db.refresh(notebook)
    assert notebook.share_token is not None
    return NotebookShareLinkResponse(share_token=notebook.share_token)


@router.delete("/{notebook_id}/share", status_code=204)
async def disable_notebook_share(
    notebook_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Revoke the public share link."""
    notebook = await _get_user_notebook(db, notebook_id, user.id)
    notebook.share_token = None
    await db.flush()


@router.post(
    "/{notebook_id}/discover/publish",
    status_code=204,
)
async def publish_notebook_to_discover(
    notebook_id: str,
    body: DiscoverPublishBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Publish this notebook to the discover catalog (owner only)."""
    await discover_svc.publish_notebook(db, user.id, notebook_id, body)


@router.delete(
    "/{notebook_id}/discover/publish",
    status_code=204,
)
async def unpublish_notebook_from_discover(
    notebook_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Remove this notebook from discover; subscriptions are kept."""
    await discover_svc.unpublish_notebook(db, user.id, notebook_id)


@router.put("/{notebook_id}", response_model=NotebookResponse)
async def update_notebook(
    notebook_id: str,
    body: NotebookUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update a notebook."""
    notebook = await _get_user_notebook(db, notebook_id, user.id)
    if body.title is not None:
        notebook.title = body.title
    if body.description is not None:
        notebook.description = body.description
    await db.flush()
    await db.refresh(notebook)
    return _notebook_response(notebook)


@router.delete("/{notebook_id}", status_code=204)
async def delete_notebook(
    notebook_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a notebook and all its contents."""
    notebook = await _get_user_notebook(db, notebook_id, user.id)
    await db.delete(notebook)


async def _get_user_notebook(
    db: AsyncSession, notebook_id: str, user_id: str
) -> Notebook:
    """Helper to fetch a notebook owned by the given user."""
    result = await db.execute(
        select(Notebook).where(
            Notebook.id == notebook_id, Notebook.user_id == user_id
        )
    )
    notebook = result.scalar_one_or_none()
    if notebook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        )
    return notebook
