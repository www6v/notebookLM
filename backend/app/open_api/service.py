"""OpenAPI credential lifecycle and verification."""

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from notebooklm_shared.auth.service import hash_password, verify_password
from notebooklm_shared.models.open_api_credential import OpenApiCredential
from notebooklm_shared.models.user import User

CREDENTIAL_TTL_DAYS = 30
STATUS_ACTIVE = "active"
STATUS_REVOKED = "revoked"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _new_client_id() -> str:
    return secrets.token_hex(16)


def _new_api_key() -> str:
    return secrets.token_urlsafe(32)


def _expires_at() -> datetime:
    return _utcnow() + timedelta(days=CREDENTIAL_TTL_DAYS)


async def get_credential_for_user(
    db: AsyncSession, user_id: str
) -> OpenApiCredential | None:
    """Return active credential row for user, if any."""
    result = await db.execute(
        select(OpenApiCredential).where(OpenApiCredential.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_credential_by_client_id(
    db: AsyncSession, client_id: str
) -> OpenApiCredential | None:
    result = await db.execute(
        select(OpenApiCredential).where(
            OpenApiCredential.client_id == client_id
        )
    )
    return result.scalar_one_or_none()


async def create_credential(
    db: AsyncSession, user: User
) -> tuple[OpenApiCredential, str]:
    """Create a new credential; returns row and plaintext api_key."""
    existing = await get_credential_for_user(db, user.id)
    if existing is not None:
        await db.delete(existing)
        await db.flush()

    api_key = _new_api_key()
    row = OpenApiCredential(
        user_id=user.id,
        client_id=_new_client_id(),
        api_key_hash=hash_password(api_key),
        status=STATUS_ACTIVE,
        expires_at=_expires_at(),
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row, api_key


async def revoke_credential(db: AsyncSession, user_id: str) -> bool:
    """Delete credential for user. Returns True if one existed."""
    row = await get_credential_for_user(db, user_id)
    if row is None:
        return False
    await db.delete(row)
    await db.flush()
    return True


async def verify_open_api_auth(
    db: AsyncSession, client_id: str, api_key: str
) -> User:
    """Validate headers and return the owning user."""
    from app.open_api.errors import AUTH_FAILED, OpenApiBizError

    if not client_id or not api_key:
        raise OpenApiBizError(AUTH_FAILED, "缺少 Client ID 或 API Key")

    cred = await get_credential_by_client_id(db, client_id)
    if cred is None or cred.status != STATUS_ACTIVE:
        raise OpenApiBizError(AUTH_FAILED, "apiKey 鉴权失败")

    if cred.expires_at < _utcnow():
        raise OpenApiBizError(AUTH_FAILED, "API Key 已过期，请重新获取")

    if not verify_password(api_key, cred.api_key_hash):
        raise OpenApiBizError(AUTH_FAILED, "apiKey 鉴权失败")

    from notebooklm_shared.auth.service import get_user_by_id

    user = await get_user_by_id(db, cred.user_id)
    if user is None or not user.is_active:
        raise OpenApiBizError(AUTH_FAILED, "用户不可用")
    return user
