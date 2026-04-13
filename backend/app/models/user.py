"""User database model."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    """Application user."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    username: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    password: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )    
    password_hash: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )
    oauth_provider: Mapped[str | None] = mapped_column(
        String(32), nullable=True, default=None
    )
    oauth_subject: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="free"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    subscription_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=None
    )
    subscription_plan: Mapped[str] = mapped_column(
        String(20), nullable=False, default="free"
    )

    # Relationships
    notebooks = relationship(
        "Notebook", back_populates="owner", cascade="all, delete-orphan"
    )
    settings = relationship(
        "UserSettings",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
