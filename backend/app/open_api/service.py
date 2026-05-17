"""OpenAPI credential lifecycle and verification."""

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from notebooklm_shared.auth.service import (
    get_user_by_id,
    hash_password,
    verify_password,
)
from notebooklm_shared.models.open_api_credential import OpenApiCredential
from notebooklm_shared.models.user import User

CREDENTIAL_TTL_DAYS = 30
STATUS_ACTIVE = "active"
STATUS_EXPIRED = "expired"
STATUS_REVOKED = "revoked"

STATUS_LABELS = {
    STATUS_ACTIVE: "有效",
    STATUS_EXPIRED: "已过期",
    STATUS_REVOKED: "已失效",
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _is_expired(row: OpenApiCredential) -> bool:
    return row.expires_at < _utcnow()


def effective_status(row: OpenApiCredential) -> str:
    """UI status: active keys past expiry show as expired."""
    if row.status != STATUS_ACTIVE:
        return row.status
    if _is_expired(row):
        return STATUS_EXPIRED
    return STATUS_ACTIVE


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status)


def credential_status_payload(row: OpenApiCredential | None) -> dict:
    """Build GET response for agent-interface (never includes api_key)."""
    if row is None:
        return {"has_credential": False}

    status = effective_status(row)
    return {
        "has_credential": True,
        "client_id": row.client_id,
        "status": status,
        "status_label": status_label(status),
        "expires_at": row.expires_at,
    }


def credential_reveal_payload(
    row: OpenApiCredential, api_key: str
) -> dict:
    """Build create/regenerate response (api_key shown once)."""
    status = effective_status(row)
    return {
        "client_id": row.client_id,
        "api_key": api_key,
        "status": status,
        "status_label": status_label(status),
        "expires_at": row.expires_at,
        "reveal_once": True,
    }


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


async def _ensure_user_exists(db: AsyncSession, user_id: str) -> User:
    """Referential integrity: user_id must reference an existing user."""
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise ValueError(f"user not found: {user_id}")
    return user


async def delete_credentials_for_user(
    db: AsyncSession, user_id: str
) -> int:
    """Delete all credentials for a user (CASCADE equivalent)."""
    row = await get_credential_for_user(db, user_id)
    if row is None:
        return 0
    await db.delete(row)
    await db.flush()
    return 1


async def create_credential(
    db: AsyncSession, user: User
) -> tuple[OpenApiCredential, str]:
    """Create a new credential; returns row and plaintext api_key."""
    await _ensure_user_exists(db, user.id)
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

    if _is_expired(cred):
        raise OpenApiBizError(AUTH_FAILED, "API Key 已过期，请重新获取")

    if not verify_password(api_key, cred.api_key_hash):
        raise OpenApiBizError(AUTH_FAILED, "apiKey 鉴权失败")

    user = await get_user_by_id(db, cred.user_id)
    if user is None or not user.is_active:
        raise OpenApiBizError(AUTH_FAILED, "用户不可用")
    return user
