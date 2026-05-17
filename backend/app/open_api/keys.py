"""JWT-protected API key management (agent-interface)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from notebooklm_shared.database import get_db
from notebooklm_shared.models.user import User
from app.open_api.schemas import (
    OpenApiCredentialCreateResponse,
    OpenApiCredentialView,
)
from app.open_api import service as cred_svc

router = APIRouter(prefix="/api/open-api", tags=["open-api-keys"])


def _view(row) -> OpenApiCredentialView:
    return OpenApiCredentialView(
        client_id=row.client_id,
        status=row.status,
        expires_at=row.expires_at,
        has_api_key=True,
    )


@router.get("/credential", response_model=OpenApiCredentialView)
async def get_credential(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return current Client ID and metadata (never returns api_key)."""
    row = await cred_svc.get_credential_for_user(db, user.id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="尚未创建 API Key",
        )
    return _view(row)


@router.post(
    "/credential",
    response_model=OpenApiCredentialCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_credential(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate Client ID and API Key (replaces existing if present)."""
    existing = await cred_svc.get_credential_for_user(db, user.id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="已存在 API Key，请删除后重新获取或使用重新获取接口",
        )
    row, api_key = await cred_svc.create_credential(db, user)
    return OpenApiCredentialCreateResponse(
        client_id=row.client_id,
        api_key=api_key,
        status=row.status,
        expires_at=row.expires_at,
    )


@router.delete("/credential", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Revoke and delete the current API Key."""
    removed = await cred_svc.revoke_credential(db, user.id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="尚未创建 API Key",
        )


@router.post(
    "/credential/regenerate",
    response_model=OpenApiCredentialCreateResponse,
)
async def regenerate_credential(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete old key and issue a new Client ID + API Key pair."""
    row, api_key = await cred_svc.create_credential(db, user)
    return OpenApiCredentialCreateResponse(
        client_id=row.client_id,
        api_key=api_key,
        status=row.status,
        expires_at=row.expires_at,
    )
