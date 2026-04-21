"""OAuth2 helpers for third-party web login (Google, Weibo, QQ, Alipay)."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import quote, urlencode

import httpx
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.services.security.auth_service import (
    ALGORITHM,
    create_access_token,
    get_user_by_email,
    get_user_by_username,
)

OAUTH_PROVIDERS = frozenset({"google", "weibo", "qq", "alipay"})


def create_oauth_state(provider: str) -> str:
    """Build a short-lived signed JWT used as OAuth state (CSRF)."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=10)
    payload = {"purpose": "oauth", "p": provider, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def verify_oauth_state(token: str) -> str | None:
    """Return provider name if state is valid, else None."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
        )
        if payload.get("purpose") != "oauth":
            return None
        provider = payload.get("p")
        if provider not in OAUTH_PROVIDERS:
            return None
        return str(provider)
    except JWTError:
        return None


async def find_user_by_oauth(
    db: AsyncSession,
    provider: str,
    subject: str,
) -> User | None:
    """Find user by OAuth provider and subject (e.g. Google ``sub``)."""
    result = await db.execute(
        select(User).where(
            User.oauth_provider == provider,
            User.oauth_subject == subject,
        )
    )
    return result.scalar_one_or_none()


def _sanitize_username_base(raw: str) -> str:
    """Keep username safe and within DB length."""
    cleaned = re.sub(r"[^\w\-.]", "_", raw.strip())[:80]
    return cleaned if cleaned else "user"


async def ensure_unique_username(db: AsyncSession, base: str) -> str:
    """Return a username based on ``base`` that is not yet taken."""
    candidate = _sanitize_username_base(base)
    suffix = 0
    while True:
        key = candidate if suffix == 0 else f"{candidate[:88]}_{suffix}"
        existing = await get_user_by_username(db, key)
        if existing is None:
            return key
        suffix += 1


async def exchange_google_code(code: str, redirect_uri: str) -> dict[str, Any]:
    """Exchange authorization code for Google tokens."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30.0,
        )
    response.raise_for_status()
    return response.json()


async def fetch_google_userinfo(access_token: str) -> dict[str, Any]:
    """Fetch Google OpenID userinfo."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30.0,
        )
    response.raise_for_status()
    return response.json()


def build_google_authorize_url(state: str, redirect_uri: str) -> str:
    """Google OAuth2 authorize URL."""
    query = urlencode(
        {
            "client_id": settings.google_oauth_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "online",
        }
    )
    return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"


def oauth_callback_redirect_uri(provider: str) -> str:
    """Absolute callback URL registered with the IdP."""
    base = settings.oauth_api_public_base_url.rstrip("/")
    return f"{base}/api/auth/oauth/{provider}/callback"


def frontend_redirect_success(access_token: str) -> str:
    """Browser redirect back to SPA with JWT in query (HTTPS recommended)."""
    base = settings.frontend_oauth_redirect_base.rstrip("/")
    token_q = quote(access_token, safe="")
    return f"{base}/oauth/callback?token={token_q}"


def frontend_redirect_error(code: str) -> str:
    """Browser redirect back to SPA with error code."""
    base = settings.frontend_oauth_redirect_base.rstrip("/")
    err_q = quote(code, safe="")
    return f"{base}/oauth/callback?error={err_q}"


async def complete_google_oauth(
    db: AsyncSession,
    code: str,
    redirect_uri: str,
) -> str:
    """Create or load user and return JWT access token."""
    token_payload = await exchange_google_code(code, redirect_uri)
    access_token = token_payload.get("access_token")
    if not access_token:
        raise ValueError("google_missing_access_token")
    profile = await fetch_google_userinfo(access_token)
    sub = profile.get("sub")
    if not sub:
        raise ValueError("google_missing_sub")
    email = profile.get("email") or f"google_{sub}@localhost"

    existing_oauth = await find_user_by_oauth(db, "google", sub)
    if existing_oauth:
        return create_access_token(data={"sub": str(existing_oauth.id)})

    existing_email = await get_user_by_email(db, email)
    if existing_email is not None and existing_email.password_hash is not None:
        raise PermissionError("email_conflict")

    username = await ensure_unique_username(db, email.split("@")[0])
    user = User(
        email=email,
        username=username,
        password_hash=None,
        oauth_provider="google",
        oauth_subject=sub,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return create_access_token(data={"sub": str(user.id)})


def build_weibo_authorize_url(state: str, redirect_uri: str) -> str:
    """Weibo OAuth2 authorize URL."""
    query = urlencode(
        {
            "client_id": settings.weibo_oauth_app_key,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "state": state,
        }
    )
    return f"https://api.weibo.com/oauth2/authorize?{query}"


async def exchange_weibo_code(code: str, redirect_uri: str) -> dict[str, Any]:
    """Exchange Weibo authorization code for tokens."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.weibo.com/oauth2/access_token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.weibo_oauth_app_key,
                "client_secret": settings.weibo_oauth_app_secret,
                "redirect_uri": redirect_uri,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30.0,
        )
    response.raise_for_status()
    payload = response.json()
    if "access_token" not in payload or payload.get("error"):
        raise ValueError("weibo_token_error")
    return payload


async def fetch_weibo_user_profile(access_token: str, uid: str) -> dict[str, Any]:
    """Fetch Weibo user profile (``users/show``)."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.weibo.com/2/users/show.json",
            params={"access_token": access_token, "uid": uid},
            timeout=30.0,
        )
    response.raise_for_status()
    body = response.json()
    if body.get("error_code"):
        raise ValueError("weibo_api_error")
    return body


async def complete_weibo_oauth(
    db: AsyncSession,
    code: str,
    redirect_uri: str,
) -> str:
    """Create or load user and return JWT after Weibo OAuth."""
    token_payload = await exchange_weibo_code(code, redirect_uri)
    access_token = token_payload.get("access_token")
    uid = token_payload.get("uid")
    if not access_token or uid is None:
        raise ValueError("weibo_missing_token")
    uid_str = str(uid)
    profile = await fetch_weibo_user_profile(access_token, uid_str)
    sub = str(profile.get("id") or uid_str)
    email = profile.get("email") or f"weibo_{sub}@localhost"

    existing_oauth = await find_user_by_oauth(db, "weibo", sub)
    if existing_oauth:
        return create_access_token(data={"sub": str(existing_oauth.id)})

    existing_email = await get_user_by_email(db, email)
    if existing_email is not None and existing_email.password_hash is not None:
        raise PermissionError("email_conflict")

    name_hint = profile.get("screen_name") or email.split("@")[0]
    username = await ensure_unique_username(db, name_hint)
    user = User(
        email=email,
        username=username,
        password_hash=None,
        oauth_provider="weibo",
        oauth_subject=sub,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return create_access_token(data={"sub": str(user.id)})


def build_qq_authorize_url(state: str, redirect_uri: str) -> str:
    """QQ Connect OAuth2 authorize URL."""
    query = urlencode(
        {
            "response_type": "code",
            "client_id": settings.qq_oauth_app_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": "get_user_info",
        }
    )
    return f"https://graph.qq.com/oauth2.0/authorize?{query}"


async def exchange_qq_code(code: str, redirect_uri: str) -> dict[str, Any]:
    """Exchange QQ authorization code for an access token (JSON)."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://graph.qq.com/oauth2.0/token",
            params={
                "grant_type": "authorization_code",
                "client_id": settings.qq_oauth_app_id,
                "client_secret": settings.qq_oauth_app_key,
                "code": code,
                "redirect_uri": redirect_uri,
                "fmt": "json",
            },
            timeout=30.0,
        )
    response.raise_for_status()
    data = response.json()
    if "access_token" not in data or data.get("error"):
        raise ValueError("qq_token_error")
    return data


async def fetch_qq_openid(access_token: str) -> str:
    """Resolve QQ openid for the given access token."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://graph.qq.com/oauth2.0/me",
            params={"access_token": access_token, "fmt": "json"},
            timeout=30.0,
        )
    response.raise_for_status()
    data = response.json()
    if data.get("error"):
        raise ValueError("qq_openid_error")
    openid = data.get("openid")
    if not openid:
        raise ValueError("qq_missing_openid")
    return str(openid)


async def fetch_qq_user_profile(
    access_token: str,
    openid: str,
) -> dict[str, Any]:
    """Fetch QQ user info (nickname, etc.)."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://graph.qq.com/user/get_user_info",
            params={
                "access_token": access_token,
                "oauth_consumer_key": settings.qq_oauth_app_id,
                "openid": openid,
                "fmt": "json",
            },
            timeout=30.0,
        )
    response.raise_for_status()
    data = response.json()
    ret = data.get("ret")
    try:
        ret_ok = int(ret) == 0
    except (TypeError, ValueError):
        ret_ok = False
    if not ret_ok:
        raise ValueError("qq_userinfo_error")
    return data


async def complete_qq_oauth(
    db: AsyncSession,
    code: str,
    redirect_uri: str,
) -> str:
    """Create or load user and return JWT after QQ Connect OAuth."""
    token_payload = await exchange_qq_code(code, redirect_uri)
    access_token = token_payload["access_token"]
    openid = await fetch_qq_openid(access_token)
    profile = await fetch_qq_user_profile(access_token, openid)
    sub = openid
    email = f"qq_{sub}@localhost"

    existing_oauth = await find_user_by_oauth(db, "qq", sub)
    if existing_oauth:
        return create_access_token(data={"sub": str(existing_oauth.id)})

    existing_email = await get_user_by_email(db, email)
    if existing_email is not None and existing_email.password_hash is not None:
        raise PermissionError("email_conflict")

    name_hint = profile.get("nickname") or f"qq_{sub[:16]}"
    username = await ensure_unique_username(db, name_hint)
    user = User(
        email=email,
        username=username,
        password_hash=None,
        oauth_provider="qq",
        oauth_subject=sub,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return create_access_token(data={"sub": str(user.id)})


def alipay_oauth_authorize_base_url() -> str:
    """OpenAuth host for web login; align with ``alipay_gateway`` (prod vs dev)."""
    gateway = settings.alipay_gateway.lower()
    if "alipaydev" in gateway or "sandbox" in gateway:
        return "https://openauth.alipaydev.com"
    return "https://openauth.alipay.com"


def build_alipay_authorize_url(state: str, redirect_uri: str) -> str:
    """Alipay OAuth2 authorize URL (``scope=auth_user``)."""
    query = urlencode(
        {
            "app_id": settings.alipay_app_id,
            "scope": "auth_user",
            "redirect_uri": redirect_uri,
            "state": state,
        }
    )
    base = alipay_oauth_authorize_base_url().rstrip("/")
    return f"{base}/oauth2/publicAppAuthorize.htm?{query}"


def _alipay_oauth_client():
    """Shared Alipay SDK client (same credentials as payment)."""
    from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
    from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient

    settings.validate_alipay_public_key_config()

    alipay_config = AlipayClientConfig()
    alipay_config.server_url = settings.alipay_gateway
    alipay_config.app_id = settings.alipay_app_id
    alipay_config.app_private_key = settings.alipay_private_key
    alipay_config.alipay_public_key = settings.alipay_public_key
    return DefaultAlipayClient(alipay_client_config=alipay_config)


def exchange_alipay_auth_code(auth_code: str) -> dict[str, Any]:
    """Exchange Alipay ``auth_code`` for token payload (``user_id``, etc.)."""
    from alipay.aop.api.request.AlipaySystemOauthTokenRequest import (
        AlipaySystemOauthTokenRequest,
    )

    client = _alipay_oauth_client()
    request = AlipaySystemOauthTokenRequest()
    request.grant_type = "authorization_code"
    request.code = auth_code
    raw = client.execute(request)
    if isinstance(raw, str):
        data = json.loads(raw)
    else:
        data = raw
    if not isinstance(data, dict):
        raise ValueError("alipay_token_error")
    uid = data.get("user_id") or data.get("open_id")
    if data.get("sub_code") and not uid:
        raise ValueError("alipay_token_error")
    if not uid:
        raise ValueError("alipay_missing_user_id")
    return data


def fetch_alipay_user_nickname(access_token: str) -> str | None:
    """Optional: ``alipay.user.userinfo.share`` for display name."""
    from alipay.aop.api.request.AlipayUserUserinfoShareRequest import (
        AlipayUserUserinfoShareRequest,
    )

    try:
        client = _alipay_oauth_client()
        request = AlipayUserUserinfoShareRequest()
        request.add_other_text_param("auth_token", access_token)
        raw = client.execute(request)
        if isinstance(raw, str):
            data = json.loads(raw)
        else:
            data = raw
        if not isinstance(data, dict):
            return None
        if data.get("sub_code"):
            return None
        nick = data.get("nick_name") or data.get("nickname")
        return str(nick).strip() if nick else None
    except Exception:
        return None


async def complete_alipay_oauth(
    db: AsyncSession,
    auth_code: str,
    _redirect_uri: str,
) -> str:
    """Create or load user and return JWT after Alipay OAuth (``auth_user``)."""
    token_payload = exchange_alipay_auth_code(auth_code)
    access_token = token_payload.get("access_token")
    sub = str(token_payload.get("user_id") or token_payload.get("open_id"))
    email = f"alipay_{sub}@localhost"

    existing_oauth = await find_user_by_oauth(db, "alipay", sub)
    if existing_oauth:
        return create_access_token(data={"sub": str(existing_oauth.id)})

    existing_email = await get_user_by_email(db, email)
    if existing_email is not None and existing_email.password_hash is not None:
        raise PermissionError("email_conflict")

    name_hint = None
    if access_token:
        name_hint = fetch_alipay_user_nickname(access_token)
    if not name_hint:
        name_hint = f"alipay_{sub[:16]}"
    username = await ensure_unique_username(db, name_hint)
    user = User(
        email=email,
        username=username,
        password_hash=None,
        oauth_provider="alipay",
        oauth_subject=sub,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return create_access_token(data={"sub": str(user.id)})
