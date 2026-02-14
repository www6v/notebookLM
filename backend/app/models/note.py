"""Note database model."""

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin, UUIDMixin


class Note(Base, UUIDMixin, TimestampMixin):
    """A user note within a notebook."""

    __tablename__ = "notes"

    notebook_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("notebooks.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(
        String(255), default="Untitled Note", nullable=False
    )
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    is_pinned: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Relationships
    notebook = relationship("Notebook", back_populates="notes")
