"""Source and SourceChunk database models."""

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin, UUIDMixin


class Source(Base, UUIDMixin, TimestampMixin):
    """An uploaded source document within a notebook."""

    __tablename__ = "sources"

    notebook_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("notebooks.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # pdf, web, youtube, docx, txt, markdown
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    original_url: Mapped[str | None] = mapped_column(
        String(2000), nullable=True
    )
    raw_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )  # pending, processing, ready, error

    # Relationships
    notebook = relationship("Notebook", back_populates="sources")
    chunks = relationship(
        "SourceChunk", back_populates="source", cascade="all, delete-orphan"
    )


class SourceChunk(Base, UUIDMixin):
    """A chunk of a source document with its embedding vector."""

    __tablename__ = "source_chunks"

    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sources.id"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Text, nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSON, nullable=True
    )

    # Relationships
    source = relationship("Source", back_populates="chunks")
