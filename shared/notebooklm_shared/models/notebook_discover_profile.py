"""Discover catalog metadata for a notebook (owner-published)."""

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from notebooklm_shared.database import Base, TimestampMixin


class NotebookDiscoverProfile(Base, TimestampMixin):
    """Public discover listing metadata for a notebook."""

    __tablename__ = "notebook_discover_profiles"

    notebook_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("notebooks.id", ondelete="CASCADE"),
        primary_key=True,
    )
    category: Mapped[str] = mapped_column(
        String(64), default="general", nullable=False
    )
    cover_url: Mapped[str] = mapped_column(
        String(512), default="", nullable=False
    )
    subscriber_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    notebook = relationship("Notebook", back_populates="discover_profile")
