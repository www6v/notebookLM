"""Pydantic schemas for sources."""

from datetime import datetime

from pydantic import BaseModel


class SourceCreate(BaseModel):
    """Schema for creating a source via URL."""

    title: str = ""
    type: str  # pdf, web, youtube, docx, txt, markdown
    url: str | None = None


class SourceUpdate(BaseModel):
    """Schema for updating a source."""

    title: str | None = None
    is_active: bool | None = None


class SourceResponse(BaseModel):
    """Schema for source response."""

    id: str
    notebook_id: str
    title: str
    type: str
    original_url: str | None = None
    is_active: bool
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SourceContentResponse(BaseModel):
    """Schema for source content response."""

    id: str
    title: str
    raw_content: str | None = None
    chunk_count: int = 0
