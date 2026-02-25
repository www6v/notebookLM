"""Studio models: MindMap, SlideDeck, Infographic."""

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin, UUIDMixin


class MindMap(Base, UUIDMixin, TimestampMixin):
    """An AI-generated mind map from notebook sources."""

    __tablename__ = "mind_maps"

    notebook_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("notebooks.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    graph_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="ready", nullable=False
    )

    # Relationships
    notebook = relationship("Notebook", back_populates="mind_maps")


class SlideDeck(Base, UUIDMixin, TimestampMixin):
    """An AI-generated slide deck from notebook sources."""

    __tablename__ = "slide_decks"

    notebook_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("notebooks.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    theme: Mapped[str] = mapped_column(
        String(50), default="light", nullable=False
    )
    slides_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    notebook = relationship("Notebook", back_populates="slide_decks")


class Infographic(Base, UUIDMixin, TimestampMixin):
    """An AI-generated infographic from notebook sources."""

    __tablename__ = "infographics"

    notebook_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("notebooks.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    template_type: Mapped[str] = mapped_column(
        String(50), default="timeline", nullable=False
    )
    layout_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )

    # Relationships
    notebook = relationship("Notebook", back_populates="infographics")
