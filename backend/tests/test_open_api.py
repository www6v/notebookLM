"""Tests for OpenAPI credential service."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.open_api.errors import AUTH_FAILED, OpenApiBizError
from app.open_api import service as cred_svc
from notebooklm_shared.auth.service import hash_password


@pytest.mark.asyncio
async def test_verify_open_api_auth_missing_headers():
    db = AsyncMock()
    with pytest.raises(OpenApiBizError) as exc:
        await cred_svc.verify_open_api_auth(db, "", "")
    assert exc.value.code == AUTH_FAILED


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
