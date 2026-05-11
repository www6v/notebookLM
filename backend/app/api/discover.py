"""Authenticated discover subscription endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from notebooklm_shared.database import get_db
from notebooklm_shared.models.user import User
from app.services import discover_service as discover_svc

router = APIRouter(prefix="/api/discover", tags=["discover"])


@router.post(
    "/notebooks/{notebook_id}/subscribe",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def subscribe_to_discover_notebook(
    notebook_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Subscribe the current user to a discoverable notebook."""
    await discover_svc.subscribe(db, user.id, notebook_id)


@router.delete(
    "/notebooks/{notebook_id}/subscribe",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unsubscribe_from_discover_notebook(
    notebook_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Remove the current user's subscription to a notebook."""
    await discover_svc.unsubscribe(db, user.id, notebook_id)
