"""User settings API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.limits import DEFAULT_LLM_MODEL, DEFAULT_LLM_PROVIDER
from app.models.user import User
from app.schemas.user_settings import UserSettingsResponse, UserSettingsUpdate
from app.services.settings_service import get_or_create_settings, update_settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=UserSettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve settings for the authenticated user."""
    settings = await get_or_create_settings(db, str(current_user.id))
    return settings


@router.patch("", response_model=UserSettingsResponse)
async def patch_settings(
    body: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Partially update settings for the authenticated user."""
    if current_user.role == "free":
        wants_custom_provider = (
            body.llm_provider is not None
            and body.llm_provider != DEFAULT_LLM_PROVIDER
        )
        wants_custom_model = (
            body.llm_model is not None
            and body.llm_model != DEFAULT_LLM_MODEL
        )
        if wants_custom_provider or wants_custom_model:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="免费用户仅可使用默认大模型，请升级为付费用户以选择其他模型。",
            )

    settings = await update_settings(db, str(current_user.id), body)
    return settings
