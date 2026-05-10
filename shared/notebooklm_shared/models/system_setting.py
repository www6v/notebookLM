"""Key-value settings shared across all app instances."""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from notebooklm_shared.database import Base, TimestampMixin


class SystemSetting(Base, TimestampMixin):
    """Single-row style key/value store (key is primary key)."""

    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
