"""Discover catalog metadata for a notebook (owner-published)."""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from notebooklm_shared.database import Base, TimestampMixin


class NotebookDiscoverProfile(Base, TimestampMixin):
    """Public discover listing metadata for a notebook.

    No DB-level FK to notebooks (see NotebookSubscription model note).
    """

    __tablename__ = "notebook_discover_profiles"

    notebook_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    category: Mapped[str] = mapped_column(
        String(64), default="general", nullable=False
    )
    cover_url: Mapped[str] = mapped_column(
        String(512), default="", nullable=False
    )
    subscriber_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    notebook = relationship(
        "Notebook",
        back_populates="discover_profile",
        primaryjoin="NotebookDiscoverProfile.notebook_id == Notebook.id",
        foreign_keys=[notebook_id],
    )
