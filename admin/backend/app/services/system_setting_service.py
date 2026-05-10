"""Persistence helpers for system_settings rows."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from notebooklm_shared.models.system_setting import SystemSetting

DESKTOP_BACKEND_URL_KEY = "desktop_backend_url"


async def get_value(db: AsyncSession, key: str) -> Optional[str]:
    """Return stored value or None when missing or null."""
    result = await db.execute(
        select(SystemSetting.value).where(SystemSetting.key == key)
    )
    row = result.scalar_one_or_none()
    if row is None:
        return None
    return row


async def set_value(db: AsyncSession, key: str, value: str) -> None:
    """Insert or update a key."""
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == key)
    )
    existing = result.scalar_one_or_none()
    if existing is None:
        db.add(SystemSetting(key=key, value=value))
    else:
        existing.value = value
    await db.flush()
