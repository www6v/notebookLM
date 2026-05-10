"""Schemas for site-curated featured shared notebooks."""

from datetime import datetime

from pydantic import BaseModel, Field


class FeaturedNotebookPublicItem(BaseModel):
    """One featured notebook for anonymous home listing."""

    share_token: str
    title: str
    source_count: int
    created_at: datetime


class FeaturedNotebookPublicListResponse(BaseModel):
    """Wrapper for JSON list consistency with other public endpoints."""

    items: list[FeaturedNotebookPublicItem]


class FeaturedNotebookEntryInput(BaseModel):
    """Single row when replacing the curated list."""

    share_token: str = Field(..., min_length=1, max_length=64)
    custom_title: str | None = Field(default=None, max_length=2000)


class FeaturedNotebooksReplaceRequest(BaseModel):
    """Replace entire curated list (order preserved)."""

    items: list[FeaturedNotebookEntryInput] = Field(default_factory=list)


class FeaturedNotebookAdminItem(BaseModel):
    """Admin view including rows whose token no longer resolves."""

    share_token: str
    custom_title: str | None
    sort_order: int
    notebook_found: bool
    resolved_title: str | None = None
    source_count: int | None = None
    notebook_created_at: datetime | None = None


class FeaturedNotebooksAdminListResponse(BaseModel):
    """All configured links for the admin editor."""

    items: list[FeaturedNotebookAdminItem]
