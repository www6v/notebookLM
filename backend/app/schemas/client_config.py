"""Public client configuration payloads."""

from pydantic import BaseModel


class PublicClientConfigResponse(BaseModel):
    """Returned without auth for desktop shells and similar."""

    desktop_backend_url: str | None = None
