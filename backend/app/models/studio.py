"""Studio models: MindMap, SlideDeck, Infographic."""

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin, UUIDMixin


class MindMap(Base, UUIDMixin, TimestampMixin):
    """An AI-generated mind map from notebook sources."""

    __tablename__ = "mind_maps"

    notebook_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("notebooks.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    suggested_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    graph_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="ready", nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_language: Mapped[str] = mapped_column(
        String(50), default="简体中文", nullable=False
    )
    source_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    notebook = relationship("Notebook", back_populates="mind_maps")


class SlideDeck(Base, UUIDMixin, TimestampMixin):
    """An AI-generated slide deck from notebook sources."""

    __tablename__ = "slide_decks"

    notebook_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("notebooks.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    suggested_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    theme: Mapped[str] = mapped_column(
        String(50), default="light", nullable=False
    )
    slides_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    slide_style: Mapped[str] = mapped_column(
        String(100), default="blueprint", nullable=False
    )
    slide_audience: Mapped[str] = mapped_column(
        String(50), default="general", nullable=False
    )
    slide_language: Mapped[str] = mapped_column(
        String(50), default="简体中文", nullable=False
    )
    slide_duration: Mapped[str] = mapped_column(
        String(50), default="default", nullable=False
    )
    slide_custom_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    notebook = relationship("Notebook", back_populates="slide_decks")


class Infographic(Base, UUIDMixin, TimestampMixin):
    """An AI-generated infographic (single image) from notebook sources."""

    __tablename__ = "infographics"

    notebook_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("notebooks.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    suggested_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    layout_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    infographic_style: Mapped[str] = mapped_column(
        String(100), default="标准", nullable=False
    )
    infographic_language: Mapped[str] = mapped_column(
        String(50), default="简体中文", nullable=False
    )
    infographic_direction: Mapped[str] = mapped_column(
        String(50), default="横向", nullable=False
    )
    infographic_visual_style: Mapped[str] = mapped_column(
        String(50), default="craft-handmade", nullable=False
    )
    infographic_custom_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    notebook = relationship("Notebook", back_populates="infographics")


class Report(Base, UUIDMixin, TimestampMixin):
    """An AI-generated report from notebook sources."""

    __tablename__ = "reports"

    notebook_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("notebooks.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    suggested_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    report_format: Mapped[str] = mapped_column(
        String(100), default="briefing_doc", nullable=False
    )
    report_language: Mapped[str] = mapped_column(
        String(50), default="简体中文", nullable=False
    )
    report_custom_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    notebook = relationship("Notebook", back_populates="reports")


class PodcastOverview(Base, UUIDMixin, TimestampMixin):
    """AI-generated podcast-style audio overview from notebook sources."""

    __tablename__ = "podcast_overviews"

    notebook_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("notebooks.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    suggested_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    audio_format: Mapped[str] = mapped_column(
        String(50), default="deep_dive", nullable=False
    )
    audio_language: Mapped[str] = mapped_column(
        String(50), default="简体中文", nullable=False
    )
    audio_length: Mapped[str] = mapped_column(
        String(50), default="default", nullable=False
    )
    audio_focus_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    notebook = relationship("Notebook", back_populates="podcast_overviews")


class DeepResearchReport(Base, UUIDMixin, TimestampMixin):
    """Deep Research report from DeerFlow (web research + synthesis)."""

    __tablename__ = "deep_research_reports"

    notebook_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("notebooks.id"), nullable=False
    )
    query: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    popular_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deer_flow_thread_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    celery_task_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    notebook = relationship("Notebook", back_populates="deep_research_reports")
