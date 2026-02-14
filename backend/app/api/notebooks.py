"""Notebook CRUD API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.notebook import Notebook
from app.models.source import Source
from app.models.user import User
from app.schemas.notebook import (
    NotebookCreate,
    NotebookListResponse,
    NotebookResponse,
    NotebookUpdate,
)

router = APIRouter(prefix="/api/notebooks", tags=["notebooks"])


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

    notebooks = []
    for notebook, count in rows:
        resp = NotebookResponse.model_validate(notebook)
        resp.source_count = count
        notebooks.append(resp)

    return NotebookListResponse(notebooks=notebooks, total=len(notebooks))


@router.post("", response_model=NotebookResponse, status_code=201)
async def create_notebook(
    body: NotebookCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new notebook."""
    notebook = Notebook(
        user_id=user.id,
        title=body.title,
        description=body.description,
    )
    db.add(notebook)
    await db.flush()
    await db.refresh(notebook)
    return NotebookResponse.model_validate(notebook)


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
    resp = NotebookResponse.model_validate(notebook)
    resp.source_count = source_count_result.scalar_one()
    return resp


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
    return NotebookResponse.model_validate(notebook)


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
