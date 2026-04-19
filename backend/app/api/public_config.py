"""Unauthenticated endpoints for client bootstrap (desktop, etc.)."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.client_config import PublicClientConfigResponse
from app.services import system_setting_service as sys_svc

router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/client-config", response_model=PublicClientConfigResponse)
async def get_public_client_config(
    db: AsyncSession = Depends(get_db),
):
    """Fleet-wide hints for native clients (no auth)."""
    raw = await sys_svc.get_value(db, sys_svc.DESKTOP_BACKEND_URL_KEY)
    return PublicClientConfigResponse(desktop_backend_url=raw)
