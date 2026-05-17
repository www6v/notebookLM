"""JWT-protected API key management (agent-interface UI flow)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from notebooklm_shared.database import get_db
from notebooklm_shared.models.user import User
from app.open_api.schemas import (
    OpenApiCredentialDeleteResponse,
    OpenApiCredentialRevealResponse,
    OpenApiCredentialStatusResponse,
)
from app.open_api import service as cred_svc

router = APIRouter(prefix="/api/open-api", tags=["open-api-keys"])


@router.get("/credential", response_model=OpenApiCredentialStatusResponse)
async def get_credential_status(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """图2/图3：无 Key 时 has_credential=false；有 Key 时仅返回元数据，不含 api_key。"""
    row = await cred_svc.get_credential_for_user(db, user.id)
    return OpenApiCredentialStatusResponse(
        **cred_svc.credential_status_payload(row)
    )


@router.post(
    "/credential",
    response_model=OpenApiCredentialRevealResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_credential(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """图2「获取 API Key」-> 图1 弹窗：首次生成，明文 api_key 仅本次返回。"""
    existing = await cred_svc.get_credential_for_user(db, user.id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="已存在 API Key，请使用「重新获取」或先删除后再获取",
        )
    row, api_key = await cred_svc.create_credential(db, user)
    return OpenApiCredentialRevealResponse(
        **cred_svc.credential_reveal_payload(row, api_key)
    )


@router.delete("/credential", response_model=OpenApiCredentialDeleteResponse)
async def delete_credential(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """图3「删除 API Key」确认后 -> 回到图2 空态。"""
    removed = await cred_svc.revoke_credential(db, user.id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="尚未创建 API Key",
        )
    return OpenApiCredentialDeleteResponse(has_credential=False)


@router.post(
    "/credential/regenerate",
    response_model=OpenApiCredentialRevealResponse,
)
async def regenerate_credential(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """图3「重新获取」-> 图1 弹窗：轮换密钥，明文 api_key 仅本次返回。"""
    existing = await cred_svc.get_credential_for_user(db, user.id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="尚未创建 API Key，请先点击「获取 API Key」",
        )
    row, api_key = await cred_svc.create_credential(db, user)
    return OpenApiCredentialRevealResponse(
        **cred_svc.credential_reveal_payload(row, api_key)
    )
