"""Public and admin client configuration payloads."""

from pydantic import BaseModel, Field


class PublicClientConfigResponse(BaseModel):
    """Returned without auth for desktop shells and similar."""

    desktop_backend_url: str | None = None


class AdminClientConfigUpdate(BaseModel):
    """Admin-only update for fleet-wide desktop API origin."""

    desktop_backend_url: str = Field(
        ...,
        min_length=1,
        max_length=512,
        description="Origin only, e.g. https://api.example.com",
    )
