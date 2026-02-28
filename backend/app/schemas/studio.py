"""Pydantic schemas for studio features: MindMap, SlideDeck, Infographic."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


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
    graph_data: dict | None = None
    status: MindMapStatus = MindMapStatus.READY
    output_language: str = "简体中文"
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
    slide_style: str = "detailed"
    slide_language: str = "简体中文"
    slide_duration: str = "default"
    slide_custom_prompt: str | None = None


class SlideDeckUpdate(BaseModel):
    """Schema for updating a slide deck."""

    title: str | None = None
    theme: str | None = None
    slides_data: dict | None = None
    slide_style: str | None = None
    slide_language: str | None = None
    slide_duration: str | None = None
    slide_custom_prompt: str | None = None


class SlideDeckResponse(BaseModel):
    """Schema for slide deck response."""

    id: str
    notebook_id: str
    title: str
    theme: str
    slides_data: dict | None = None
    status: SlideDeckStatus = SlideDeckStatus.PENDING
    file_path: str | None = None
    slide_style: str = "detailed"
    slide_language: str = "简体中文"
    slide_duration: str = "default"
    slide_custom_prompt: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Infographic ---

class InfographicCreate(BaseModel):
    """Schema for generating an infographic."""

    title: str = "Infographic"
    template_type: str = "timeline"  # timeline, comparison, process, statistics, hierarchy
    source_ids: list[str] | None = None
    focus_topic: str | None = None
    output_language: str = "简体中文"


class InfographicUpdate(BaseModel):
    """Schema for updating an infographic."""

    title: str | None = None
    template_type: str | None = None
    layout_data: dict | None = None


class InfographicResponse(BaseModel):
    """Schema for infographic response."""

    id: str
    notebook_id: str
    title: str
    template_type: str
    layout_data: dict | None = None
    file_path: str | None = None
    status: str
    output_language: str = "简体中文"
    created_at: datetime

    model_config = {"from_attributes": True}
