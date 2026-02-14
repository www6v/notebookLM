"""Pydantic schemas for studio features: MindMap, SlideDeck, Infographic."""

from datetime import datetime

from pydantic import BaseModel


# --- Mind Map ---

class MindMapCreate(BaseModel):
    """Schema for generating a mind map."""

    title: str = "Mind Map"
    source_ids: list[str] | None = None


class MindMapResponse(BaseModel):
    """Schema for mind map response."""

    id: str
    notebook_id: str
    title: str
    graph_data: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Slide Deck ---

class SlideDeckCreate(BaseModel):
    """Schema for generating a slide deck."""

    title: str = "Slide Deck"
    theme: str = "light"
    source_ids: list[str] | None = None
    focus_topic: str | None = None


class SlideDeckUpdate(BaseModel):
    """Schema for updating a slide deck."""

    title: str | None = None
    theme: str | None = None
    slides_data: dict | None = None


class SlideDeckResponse(BaseModel):
    """Schema for slide deck response."""

    id: str
    notebook_id: str
    title: str
    theme: str
    slides_data: dict | None = None
    status: str
    file_path: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Infographic ---

class InfographicCreate(BaseModel):
    """Schema for generating an infographic."""

    title: str = "Infographic"
    template_type: str = "timeline"  # timeline, comparison, process, statistics, hierarchy
    source_ids: list[str] | None = None
    focus_topic: str | None = None


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
    created_at: datetime

    model_config = {"from_attributes": True}
