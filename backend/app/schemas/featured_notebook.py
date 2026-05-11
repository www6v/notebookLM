"""Schemas for site-curated featured shared notebooks."""

from datetime import datetime

from pydantic import BaseModel


class FeaturedNotebookPublicItem(BaseModel):
    """One featured notebook for anonymous home listing."""

    share_token: str
    title: str
    source_count: int
    created_at: datetime


class FeaturedNotebookPublicListResponse(BaseModel):
    """Wrapper for JSON list consistency with other public endpoints."""

    items: list[FeaturedNotebookPublicItem]
