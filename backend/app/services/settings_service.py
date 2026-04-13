"""Service layer for user settings CRUD operations."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_settings import UserSettings
from app.schemas.user_settings import UserSettingsUpdate

logger = logging.getLogger(__name__)


async def get_or_create_settings(db: AsyncSession, user_id: str) -> UserSettings:
    """Return the UserSettings row for the given user, creating it if absent."""
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()
    if settings is None:
        settings = UserSettings(user_id=user_id)
        db.add(settings)
        await db.flush()
        await db.refresh(settings)
    return settings


async def update_settings(
    db: AsyncSession,
    user_id: str,
    data: UserSettingsUpdate,
) -> UserSettings:
    """Partially update user settings and return the refreshed instance."""
    settings = await get_or_create_settings(db, user_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)
    await db.flush()
    await db.refresh(settings)
    return settings
