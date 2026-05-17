"""Tests for OpenAPI credential service and status helpers."""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.open_api.errors import AUTH_FAILED, OpenApiBizError
from app.open_api import service as cred_svc
from notebooklm_shared.auth.service import hash_password


def test_credential_status_payload_empty():
    assert cred_svc.credential_status_payload(None) == {
        "has_credential": False,
    }


def test_credential_status_payload_active():
    row = MagicMock()
    row.client_id = "abc"
    row.status = cred_svc.STATUS_ACTIVE
    row.expires_at = cred_svc._expires_at()
    payload = cred_svc.credential_status_payload(row)
    assert payload["has_credential"] is True
    assert payload["client_id"] == "abc"
    assert payload["status"] == cred_svc.STATUS_ACTIVE
    assert payload["status_label"] == "有效"
    assert "api_key" not in payload


def test_credential_status_payload_expired():
    row = MagicMock()
    row.client_id = "abc"
    row.status = cred_svc.STATUS_ACTIVE
    row.expires_at = cred_svc._utcnow() - timedelta(days=1)
    payload = cred_svc.credential_status_payload(row)
    assert payload["status"] == cred_svc.STATUS_EXPIRED
    assert payload["status_label"] == "已过期"


def test_credential_reveal_payload_includes_api_key_once():
    row = MagicMock()
    row.client_id = "cid"
    row.status = cred_svc.STATUS_ACTIVE
    row.expires_at = cred_svc._expires_at()
    payload = cred_svc.credential_reveal_payload(row, "secret-key")
    assert payload["api_key"] == "secret-key"
    assert payload["reveal_once"] is True


@pytest.mark.asyncio
async def test_verify_open_api_auth_missing_headers():
    db = AsyncMock()
    with pytest.raises(OpenApiBizError) as exc:
        await cred_svc.verify_open_api_auth(db, "", "")
    assert exc.value.code == AUTH_FAILED


@pytest.mark.asyncio
async def test_create_credential_rejects_missing_user(monkeypatch):
    db = AsyncMock()
    user = MagicMock()
    user.id = "missing-user"
    monkeypatch.setattr(
        cred_svc,
        "get_user_by_id",
        AsyncMock(return_value=None),
    )

    with pytest.raises(ValueError, match="user not found"):
        await cred_svc.create_credential(db, user)


@pytest.mark.asyncio
async def test_verify_open_api_auth_invalid_key():
    db = AsyncMock()
    cred = MagicMock()
    cred.status = cred_svc.STATUS_ACTIVE
    cred.expires_at = cred_svc._expires_at()
    cred.api_key_hash = hash_password("correct-key")
    cred.user_id = "user-1"

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = cred
    db.execute = AsyncMock(return_value=result_mock)

    user = MagicMock()
    user.is_active = True
    from notebooklm_shared.auth import service as auth_svc

    auth_svc.get_user_by_id = AsyncMock(return_value=user)

    with pytest.raises(OpenApiBizError) as exc:
        await cred_svc.verify_open_api_auth(db, "client", "wrong-key")
    assert exc.value.code == AUTH_FAILED
