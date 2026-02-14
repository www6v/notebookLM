"""Pydantic schemas for notebooks."""

from datetime import datetime

from pydantic import BaseModel


class NotebookCreate(BaseModel):
    """Schema for creating a notebook."""

    title: str
    description: str = ""


class NotebookUpdate(BaseModel):
    """Schema for updating a notebook."""

    title: str | None = None
    description: str | None = None


class NotebookResponse(BaseModel):
    """Schema for notebook response."""

    id: str
    user_id: str
    title: str
    description: str
    created_at: datetime
    updated_at: datetime
    source_count: int = 0

    model_config = {"from_attributes": True}


class NotebookListResponse(BaseModel):
    """Schema for notebook list response."""

    notebooks: list[NotebookResponse]
    total: int
