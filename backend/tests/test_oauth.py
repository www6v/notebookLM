"""OAuth state signing and verification.

Manual acceptance (after configuring providers and running migrations):
- Google: redirect URI {OAUTH_API_PUBLIC_BASE_URL}/api/auth/oauth/google/callback
- Weibo: same pattern …/api/auth/oauth/weibo/callback
- QQ Connect: same pattern …/api/auth/oauth/qq/callback
- Alipay: …/api/auth/oauth/alipay/callback (ALIPAY_* env or ``oauth:`` in config.yaml)
- From /login, use each provider; expect redirect to /app with session.
- Email/password login still works for existing users.
"""

import pytest

from app.services.security.oauth_service import (
    create_oauth_state,
    verify_oauth_state,
)


def test_oauth_state_roundtrip() -> None:
    for provider in ("google", "weibo", "qq", "alipay"):
        token = create_oauth_state(provider)
        assert verify_oauth_state(token) == provider


def test_oauth_state_rejects_wrong_purpose(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services.security import oauth_service
    from jose import jwt
    from app.services.security.auth_service import ALGORITHM

    bad = jwt.encode(
        {"purpose": "other", "p": "google"},
        oauth_service.settings.secret_key,
        algorithm=ALGORITHM,
    )
    assert verify_oauth_state(bad) is None


def test_oauth_state_rejects_invalid_token() -> None:
    assert verify_oauth_state("not-a-jwt") is None
