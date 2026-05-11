"""Pydantic schemas for discover listing, detail, and publish body."""

from pydantic import BaseModel, Field


class DiscoverPublishBody(BaseModel):
    """Owner payload when publishing a notebook to the discover catalog."""

    category: str = Field(default="general", max_length=64)
    cover_url: str = Field(default="", max_length=512)


class DiscoverNotebookListItem(BaseModel):
    """One row in the public discover notebook grid."""

    id: str
    title: str
    description: str
    category: str
    cover_url: str
    subscriber_count: int
    source_count: int
    owner_display_name: str


class DiscoverNotebookListResponse(BaseModel):
    """Paginated discover list."""

    items: list[DiscoverNotebookListItem]
    total: int


class DiscoverNotebookDetail(BaseModel):
    """Public detail for a discoverable notebook (DTO for API responses)."""

    id: str
    title: str
    description: str
    category: str
    cover_url: str
    subscriber_count: int
    source_count: int
    owner_display_name: str
    share_token: str | None
