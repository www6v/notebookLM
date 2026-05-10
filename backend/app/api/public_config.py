"""Unauthenticated endpoints for client bootstrap (desktop, etc.)."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from notebooklm_shared.database import get_db
from app.schemas.client_config import PublicClientConfigResponse
from app.schemas.featured_notebook import FeaturedNotebookPublicListResponse
from app.services import featured_notebook_service as featured_svc
from app.services import system_setting_service as sys_svc

router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/client-config", response_model=PublicClientConfigResponse)
async def get_public_client_config(
    db: AsyncSession = Depends(get_db),
):
    """Fleet-wide hints for native clients (no auth)."""
    raw = await sys_svc.get_value(db, sys_svc.DESKTOP_BACKEND_URL_KEY)
    return PublicClientConfigResponse(desktop_backend_url=raw)


@router.get(
    "/featured-notebooks",
    response_model=FeaturedNotebookPublicListResponse,
)
async def get_public_featured_notebooks(
    db: AsyncSession = Depends(get_db),
):
    """Curated shared notebooks for the home Featured tab (no auth)."""
    items = await featured_svc.get_public_items(db)
    return FeaturedNotebookPublicListResponse(items=items)
