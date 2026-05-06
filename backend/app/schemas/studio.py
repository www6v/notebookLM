"""Pydantic schemas for studio features: MindMap, SlideDeck, Infographic."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, field_validator, model_validator

from app.services.security.custom_prompt_safety import (
    validate_custom_prompt_text,
)

if TYPE_CHECKING:
    from app.models.studio import DeepResearchReport

VALID_SLIDE_STYLE_VALUES = {
    "blueprint",
    "chalkboard",
    "corporate",
    "minimal",
    "sketch-notes",
    "watercolor",
    "dark-atmospheric",
    "notion",
    "bold-editorial",
    "editorial-infographic",
    "fantasy-animation",
    "intuition-machine",
    "pixel-art",
    "scientific",
    "vector-illustration",
    "vintage",
    "detailed",
    "presentation",
}


def _validate_slide_style_value(value: str | None) -> str | None:
    """Reject unsupported slide style identifiers at the API boundary."""
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        raise ValueError("slide_style cannot be empty")
    if normalized not in VALID_SLIDE_STYLE_VALUES:
        raise ValueError(
            "Unsupported slide_style. Use one of the predefined slide styles."
        )
    return normalized


# --- Mind Map ---


class MindMapStatus(str, Enum):
    """Mind map generation status."""

    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"

class MindMapCreate(BaseModel):
    """Schema for generating a mind map."""

    title: str = "Mind Map"
    source_ids: list[str] | None = None
    output_language: str = "简体中文"


class MindMapResponse(BaseModel):
    """Schema for mind map response."""

    id: str
    notebook_id: str
    title: str
    suggested_filename: str | None = None
    graph_data: dict | None = None
    status: MindMapStatus = MindMapStatus.READY
    error_message: str | None = None
    output_language: str = "简体中文"
    source_count: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Slide Deck ---


class SlideDeckStatus(str, Enum):
    """Slide deck generation status."""

    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class SlideDeckCreate(BaseModel):
    """Schema for generating a slide deck."""

    title: str = "Slide Deck"
    theme: str = "light"
    source_ids: list[str] | None = None
    focus_topic: str | None = None
    slide_style: str = "blueprint"
    slide_audience: str = "general"
    slide_language: str = "简体中文"
    slide_duration: str = "default"
    slide_custom_prompt: str | None = None

    @field_validator("slide_style")
    @classmethod
    def validate_slide_style(cls, value: str) -> str:
        """Validate slide style identifiers accepted by the backend."""
        validated = _validate_slide_style_value(value)
        return validated or "blueprint"

    @field_validator("slide_custom_prompt")
    @classmethod
    def validate_slide_custom_prompt(cls, value: str | None) -> str | None:
        """Validate and normalize user custom prompt text."""
        return validate_custom_prompt_text(
            value,
            field_name="slide_custom_prompt",
        )


class SlideDeckUpdate(BaseModel):
    """Schema for updating a slide deck."""

    title: str | None = None
    theme: str | None = None
    slides_data: dict | None = None
    slide_style: str | None = None
    slide_audience: str | None = None
    slide_language: str | None = None
    slide_duration: str | None = None
    slide_custom_prompt: str | None = None

    @field_validator("slide_style")
    @classmethod
    def validate_slide_style(cls, value: str | None) -> str | None:
        """Validate slide style identifiers accepted by the backend."""
        return _validate_slide_style_value(value)

    @field_validator("slide_custom_prompt")
    @classmethod
    def validate_slide_custom_prompt(cls, value: str | None) -> str | None:
        """Validate and normalize user custom prompt text."""
        return validate_custom_prompt_text(
            value,
            field_name="slide_custom_prompt",
        )


class SlideDeckSlideEdit(BaseModel):
    """One slide page revision (0-based index, same order as images manifest)."""

    slide_index: int = Field(ge=0)
    prompt: str = Field(min_length=1, max_length=4000)


class SlideDeckReviseRequest(BaseModel):
    """Batch per-slide image edits; duplicate indices keep the last prompt."""

    edits: list[SlideDeckSlideEdit] = Field(min_length=1)

    @model_validator(mode="after")
    def dedupe_by_slide(self) -> SlideDeckReviseRequest:
        by_index: dict[int, str] = {}
        for item in self.edits:
            stripped = item.prompt.strip()
            if not stripped:
                raise ValueError("Prompt cannot be empty or whitespace-only")
            by_index[item.slide_index] = stripped
        self.edits = [
            SlideDeckSlideEdit(slide_index=i, prompt=p)
            for i, p in sorted(by_index.items())
        ]
        return self


class SlideDeckResponse(BaseModel):
    """Schema for slide deck response."""

    id: str
    notebook_id: str
    title: str
    suggested_filename: str | None = None
    theme: str
    slides_data: dict | None = None
    status: SlideDeckStatus = SlideDeckStatus.PENDING
    error_message: str | None = None
    file_path: str | None = None
    slide_style: str = "blueprint"
    slide_audience: str = "general"
    slide_language: str = "简体中文"
    slide_duration: str = "default"
    slide_custom_prompt: str | None = None
    source_count: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("slide_audience", mode="before")
    @classmethod
    def default_slide_audience(cls, value: str | None) -> str:
        """Keep older slide rows with NULL audience API-compatible."""
        if value is None:
            return "general"
        normalized = value.strip()
        return normalized or "general"


# --- Infographic ---


class InfographicStatus(str, Enum):
    """Infographic generation status."""

    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class InfographicCreate(BaseModel):
    """Schema for generating an infographic."""

    title: str = "Infographic"
    source_ids: list[str] | None = None
    infographic_style: str = "标准"
    infographic_language: str = "简体中文"
    infographic_direction: str = "横向"
    infographic_visual_style: str = "craft-handmade"
    infographic_custom_prompt: str | None = None

    @field_validator("infographic_custom_prompt")
    @classmethod
    def validate_infographic_custom_prompt(
        cls, value: str | None
    ) -> str | None:
        """Validate and normalize user custom prompt text."""
        return validate_custom_prompt_text(
            value,
            field_name="infographic_custom_prompt",
        )


class InfographicUpdate(BaseModel):
    """Schema for updating an infographic."""

    title: str | None = None
    infographic_style: str | None = None
    infographic_language: str | None = None
    infographic_direction: str | None = None
    infographic_visual_style: str | None = None
    infographic_custom_prompt: str | None = None

    @field_validator("infographic_custom_prompt")
    @classmethod
    def validate_infographic_custom_prompt(
        cls, value: str | None
    ) -> str | None:
        """Validate and normalize user custom prompt text."""
        return validate_custom_prompt_text(
            value,
            field_name="infographic_custom_prompt",
        )


class InfographicResponse(BaseModel):
    """Schema for infographic response."""

    id: str
    notebook_id: str
    title: str
    suggested_filename: str | None = None
    layout_data: dict | None = None
    file_path: str | None = None
    status: InfographicStatus = InfographicStatus.PENDING
    error_message: str | None = None
    infographic_style: str = "标准"
    infographic_language: str = "简体中文"
    infographic_direction: str = "横向"
    infographic_visual_style: str = "craft-handmade"
    infographic_custom_prompt: str | None = None
    source_count: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("infographic_visual_style", mode="before")
    @classmethod
    def default_visual_style(cls, value: str | None) -> str:
        """Keep older infographic rows with NULL visual style API-compatible."""
        if value is None:
            return "craft-handmade"
        normalized = value.strip()
        return normalized or "craft-handmade"


# --- Report ---


class ReportStatus(str, Enum):
    """Report generation status."""

    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class ReportCreate(BaseModel):
    """Schema for generating a report."""

    title: str = "Report"
    source_ids: list[str] | None = None
    report_format: str = "briefing_doc"
    report_language: str = "简体中文"
    report_custom_prompt: str | None = None


class ReportUpdate(BaseModel):
    """Schema for updating a report."""

    title: str | None = None
    report_format: str | None = None
    report_language: str | None = None
    report_custom_prompt: str | None = None


class ReportResponse(BaseModel):
    """Schema for report response."""

    id: str
    notebook_id: str
    title: str
    suggested_filename: str | None = None
    report_format: str = "briefing_doc"
    report_language: str = "简体中文"
    report_custom_prompt: str | None = None
    content: str | None = None
    status: ReportStatus = ReportStatus.PENDING
    error_message: str | None = None
    source_count: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Podcast (audio overview) ---


class PodcastStatus(str, Enum):
    """Podcast / audio overview generation status."""

    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class PodcastCreate(BaseModel):
    """Schema for generating a podcast-style audio overview."""

    title: str = "音频概览"
    source_ids: list[str] | None = None
    audio_format: str = "deep_dive"
    audio_language: str = "简体中文"
    audio_length: str = "default"
    audio_focus_prompt: str | None = None

    @field_validator("audio_focus_prompt")
    @classmethod
    def validate_audio_focus_prompt(cls, value: str | None) -> str | None:
        """Validate and normalize user custom prompt text."""
        return validate_custom_prompt_text(
            value,
            field_name="audio_focus_prompt",
        )


class PodcastResponse(BaseModel):
    """Schema for podcast overview API responses."""

    id: str
    notebook_id: str
    title: str
    suggested_filename: str | None = None
    audio_format: str = "deep_dive"
    audio_language: str = "简体中文"
    audio_length: str = "default"
    audio_focus_prompt: str | None = None
    file_path: str | None = None
    transcript: str | None = None
    status: PodcastStatus = PodcastStatus.PENDING
    error_message: str | None = None
    source_count: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Deep Research (DeerFlow) ---


class DeepResearchStatus(str, Enum):
    """Deep research report status."""

    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class DeepResearchCreate(BaseModel):
    """Schema for creating a deep research task."""

    query: str


class DeepResearchResponse(BaseModel):
    """Schema for deep research report (matches frontend DeepResearchReport)."""

    id: str
    query: str
    sourceCount: int = 0
    popularCount: int = 0
    content: str | None = None
    status: str = "pending"
    error_message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": False}

    @classmethod
    def from_orm_report(cls, r: "DeepResearchReport") -> "DeepResearchResponse":
        """Build from DeepResearchReport model (with camelCase for frontend)."""
        return cls(
            id=r.id,
            query=r.query,
            sourceCount=r.source_count,
            popularCount=r.popular_count,
            content=r.content,
            status=r.status,
            error_message=r.error_message,
            created_at=r.created_at,
        )
