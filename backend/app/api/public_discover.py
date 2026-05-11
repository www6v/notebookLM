"""Public discover catalog endpoints (no authentication)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from notebooklm_shared.database import get_db
from app.schemas.discover import DiscoverNotebookDetail, DiscoverNotebookListResponse
from app.services import discover_service as discover_svc

router = APIRouter(prefix="/api/public/discover", tags=["public-discover"])

_MAX_PAGE = 50


@router.get("/notebooks", response_model=DiscoverNotebookListResponse)
async def list_public_discover_notebooks(
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(None, max_length=200),
    category: str | None = Query(None, max_length=64),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=_MAX_PAGE),
):
    """List notebooks published to discover (metadata only)."""
    items, total = await discover_svc.list_discoverable(
        db,
        q=q,
        category=category,
        offset=offset,
        limit=limit,
    )
    return DiscoverNotebookListResponse(items=items, total=total)


@router.get(
    "/notebooks/{notebook_id}",
    response_model=DiscoverNotebookDetail,
)
async def get_public_discover_notebook_detail(
    notebook_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Return discover detail for one notebook or 404."""
    detail = await discover_svc.get_discover_detail(db, notebook_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        )
    return detail
