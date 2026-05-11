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
    share_enabled: bool = False

    model_config = {"from_attributes": True}


class NotebookShareBody(BaseModel):
    """Enable or rotate public share link."""

    regenerate: bool = False


class NotebookShareLinkResponse(BaseModel):
    """Returned when creating or rotating a share token."""

    share_token: str


class SharedNotebookView(BaseModel):
    """Notebook metadata exposed to anonymous share viewers."""

    id: str
    title: str
    description: str
    created_at: datetime
    updated_at: datetime
    source_count: int = 0


class NotebookListResponse(BaseModel):
    """Schema for notebook list response."""

    notebooks: list[NotebookResponse]
    total: int


class NotebookSubscriptionItem(BaseModel):
    """Subscribed notebook row for the home subscriptions tab."""

    notebook: NotebookResponse
    read_available: bool
    share_token: str | None = None


class NotebookSubscriptionsListResponse(BaseModel):
    """List of notebooks the current user subscribed to."""

    items: list[NotebookSubscriptionItem]
    total: int
