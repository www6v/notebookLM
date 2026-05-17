"""OpenAPI credential for OpenClaw / agent integrations."""

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from notebooklm_shared.database import Base, TimestampMixin, UUIDMixin


class OpenApiCredential(Base, UUIDMixin, TimestampMixin):
    """Per-user Client ID + API Key pair for OpenAPI access.

    Intentionally no DB-level foreign keys (MySQL charset/collation parity;
    referential integrity is enforced in application code).
    """

    __tablename__ = "open_api_credentials"

    user_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        index=True,
    )
    client_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    api_key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user = relationship(
        "User",
        back_populates="open_api_credential",
        primaryjoin="OpenApiCredential.user_id == User.id",
        foreign_keys=[user_id],
    )
