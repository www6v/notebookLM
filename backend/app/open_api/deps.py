"""Dependencies for OpenAPI routes."""

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from notebooklm_shared.database import get_db
from notebooklm_shared.models.user import User
from app.open_api.service import verify_open_api_auth


async def get_open_api_user(
    notebooklm_openapi_clientid: str | None = Header(
        None, alias="notebooklm-openapi-clientid"
    ),
    notebooklm_openapi_apikey: str | None = Header(
        None, alias="notebooklm-openapi-apikey"
    ),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve user from OpenAPI headers."""
    return await verify_open_api_auth(
        db,
        (notebooklm_openapi_clientid or "").strip(),
        (notebooklm_openapi_apikey or "").strip(),
    )
