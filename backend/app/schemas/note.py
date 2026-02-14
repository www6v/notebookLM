"""Pydantic schemas for notes."""

from datetime import datetime

from pydantic import BaseModel


class NoteCreate(BaseModel):
    """Schema for creating a note."""

    title: str = "Untitled Note"
    content: str = ""
    is_pinned: bool = False


class NoteUpdate(BaseModel):
    """Schema for updating a note."""

    title: str | None = None
    content: str | None = None
    is_pinned: bool | None = None


class NoteResponse(BaseModel):
    """Schema for note response."""

    id: str
    notebook_id: str
    title: str
    content: str
    is_pinned: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
