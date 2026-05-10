from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


def make_mock_user(role="admin", is_active=True):
    user = MagicMock()
    user.id = "test-user-id"
    user.email = "admin@test.com"
    user.username = "admin"
    user.role = role
    user.is_active = is_active
    user.subscription_expires_at = None
    user.subscription_plan = "free"
    user.created_at = "2024-01-01T00:00:00"
    return user


def test_login_non_admin_returns_403():
    with patch("app.api.auth.authenticate_user", new_callable=AsyncMock) as mock_auth:
        mock_auth.return_value = make_mock_user(role="free")
        from app.main import app
        client = TestClient(app)
        response = client.post(
            "/api/auth/login",
            json={"email": "user@test.com", "password": "password"},
        )
    assert response.status_code == 403
    assert "Admin privileges required" in response.json()["detail"]


def test_login_invalid_credentials_returns_401():
    with patch("app.api.auth.authenticate_user", new_callable=AsyncMock) as mock_auth:
        mock_auth.return_value = None
        from app.main import app
        client = TestClient(app)
        response = client.post(
            "/api/auth/login",
            json={"email": "admin@test.com", "password": "wrong"},
        )
    assert response.status_code == 401
