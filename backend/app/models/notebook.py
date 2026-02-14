"""Notebook database model."""

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin, UUIDMixin


class Notebook(Base, UUIDMixin, TimestampMixin):
    """A notebook is a collection of sources for a specific project."""

    __tablename__ = "notebooks"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    # Relationships
    owner = relationship("User", back_populates="notebooks")
    sources = relationship(
        "Source", back_populates="notebook", cascade="all, delete-orphan"
    )
    chat_sessions = relationship(
        "ChatSession", back_populates="notebook", cascade="all, delete-orphan"
    )
    notes = relationship(
        "Note", back_populates="notebook", cascade="all, delete-orphan"
    )
    mind_maps = relationship(
        "MindMap", back_populates="notebook", cascade="all, delete-orphan"
    )
    slide_decks = relationship(
        "SlideDeck", back_populates="notebook", cascade="all, delete-orphan"
    )
    infographics = relationship(
        "Infographic", back_populates="notebook", cascade="all, delete-orphan"
    )
