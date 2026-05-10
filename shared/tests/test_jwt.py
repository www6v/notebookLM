import os
from unittest.mock import MagicMock

# Import the auth service module first (triggers module-level engine creation
# using the real settings loaded from config.yaml / .env).
# Then replace auth_svc.settings with a mock for the actual test functions.
from notebooklm_shared.auth import service as auth_svc

# Override settings on the module so JWT functions use the test secret key.
mock_settings = MagicMock()
mock_settings.secret_key = "test-secret-key-for-unit-tests-minimum-length"
mock_settings.access_token_expire_minutes = 60
auth_svc.settings = mock_settings


def test_hash_and_verify_password():
    hashed = auth_svc.hash_password("mypassword123")
    assert hashed != "mypassword123"
    assert auth_svc.verify_password("mypassword123", hashed)
    assert not auth_svc.verify_password("wrongpassword", hashed)


def test_create_and_decode_token():
    token = auth_svc.create_access_token({"sub": "user-abc-123"})
    assert isinstance(token, str)
    payload = auth_svc.decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "user-abc-123"


def test_decode_invalid_token_returns_none():
    result = auth_svc.decode_access_token("not.a.valid.token")
    assert result is None

