"""Pydantic schemas for user authentication."""

from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    username: str
    password: str


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response."""

    id: str
    email: str
    username: str
    role: str = "free"
    is_active: bool = True
    created_at: datetime
    subscription_expires_at: datetime | None = None
    subscription_plan: str = "free"

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for JWT token payload."""

    user_id: str | None = None


# --------------- Admin schemas ---------------


class AdminUserUpdateRequest(BaseModel):
    """Schema for admin updating a user."""

    role: str | None = None
    is_active: bool | None = None


class AdminUserListResponse(BaseModel):
    """Paginated list of users for admin."""

    users: list[UserResponse]
    total: int
    page: int
    page_size: int


class UploadedFileTypeStat(BaseModel):
    """User-uploaded sources (object storage file) aggregated by source.type."""

    source_type: str
    count: int
    size_bytes: int


class NotebookStatsItem(BaseModel):
    """Per-notebook statistics shown in admin user detail."""

    id: str
    title: str
    source_count: int = 0
    mind_map_success_count: int = 0
    mind_map_failed_count: int = 0
    slide_deck_success_count: int = 0
    slide_deck_failed_count: int = 0
    infographic_success_count: int = 0
    infographic_failed_count: int = 0
    report_success_count: int = 0
    report_failed_count: int = 0
    podcast_overview_success_count: int = 0
    podcast_overview_failed_count: int = 0
    created_at: datetime
    uploaded_file_stats: list[UploadedFileTypeStat] = []
    uploaded_file_total_count: int = 0
    uploaded_file_total_bytes: int = 0


class AdminUserDetailResponse(BaseModel):
    """Detailed user view for admin, including per-notebook stats."""

    id: str
    email: str
    username: str
    role: str
    is_active: bool
    created_at: datetime
    notebook_count: int = 0
    notebooks: list[NotebookStatsItem] = []

    model_config = {"from_attributes": True}
