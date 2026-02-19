"""Studio API routes: Slide Deck, Infographic, Reports."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.notebook import Notebook
from app.models.studio import Infographic
from app.models.user import User
from app.schemas.studio import (
    InfographicCreate,
    InfographicResponse,
    InfographicUpdate,
)

router = APIRouter(tags=["studio"])


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
