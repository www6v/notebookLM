"""Pydantic schemas for user settings."""

from pydantic import BaseModel


class UserSettingsResponse(BaseModel):
    """Schema returned when fetching user settings."""

    output_language: str
    llm_provider: str
    llm_model: str

    model_config = {"from_attributes": True}


class UserSettingsUpdate(BaseModel):
    """Schema for updating user settings (all fields optional)."""

    output_language: str | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
