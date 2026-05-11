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
