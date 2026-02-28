"""User settings database model."""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin, UUIDMixin


class UserSettings(Base, UUIDMixin, TimestampMixin):
    """Per-user global settings."""

    __tablename__ = "user_settings"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    output_language: Mapped[str] = mapped_column(
        String(50), nullable=False, default="简体中文"
    )
    llm_provider: Mapped[str] = mapped_column(
        String(50), nullable=False, default="openai"
    )
    llm_model: Mapped[str] = mapped_column(
        String(100), nullable=False, default="gpt-4o"
    )

    # Relationship back to User
    user = relationship("User", back_populates="settings")
