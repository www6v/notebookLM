"""OAuth2 routes for Google, Weibo, QQ, and Alipay web login."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from notebooklm_shared.database import get_db
from app.services.security.oauth_service import (
    build_alipay_authorize_url,
    build_google_authorize_url,
    build_qq_authorize_url,
    build_weibo_authorize_url,
    complete_alipay_oauth,
    complete_google_oauth,
    complete_qq_oauth,
    complete_weibo_oauth,
    create_oauth_state,
    frontend_redirect_error,
    frontend_redirect_success,
    oauth_callback_redirect_uri,
    verify_oauth_state,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth/oauth", tags=["oauth"])


def _require_google_config() -> None:
    from notebooklm_shared.config import settings

    if not settings.google_oauth_client_id or not settings.google_oauth_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured",
        )


def _require_weibo_config() -> None:
    from notebooklm_shared.config import settings

    if not settings.weibo_oauth_app_key or not settings.weibo_oauth_app_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Weibo OAuth is not configured",
        )


def _require_qq_config() -> None:
    from notebooklm_shared.config import settings

    if not settings.qq_oauth_app_id or not settings.qq_oauth_app_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="QQ OAuth is not configured",
        )


def _require_alipay_oauth_config() -> None:
    from notebooklm_shared.config import settings

    if (
        not settings.alipay_app_id
        or not settings.alipay_private_key
        or not settings.alipay_public_key
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Alipay OAuth is not configured",
        )


@router.get("/google/start")
async def oauth_google_start() -> RedirectResponse:
    """Redirect browser to Google consent screen."""
    _require_google_config()
    state = create_oauth_state("google")
    redirect_uri = oauth_callback_redirect_uri("google")
    url = build_google_authorize_url(state, redirect_uri)
    return RedirectResponse(url=url, status_code=302)


@router.get("/google/callback")
async def oauth_google_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Handle Google redirect: exchange code, issue JWT, redirect to SPA."""
    if error:
        return RedirectResponse(
            frontend_redirect_error("oauth_denied"),
            status_code=302,
        )
    if not code or not state:
        return RedirectResponse(
            frontend_redirect_error("invalid_request"),
            status_code=302,
        )
    if verify_oauth_state(state) != "google":
        return RedirectResponse(
            frontend_redirect_error("invalid_state"),
            status_code=302,
        )
    redirect_uri = oauth_callback_redirect_uri("google")
    try:
        token = await complete_google_oauth(db, code, redirect_uri)
        return RedirectResponse(
            frontend_redirect_success(token),
            status_code=302,
        )
    except PermissionError:
        return RedirectResponse(
            frontend_redirect_error("email_conflict"),
            status_code=302,
        )
    except Exception as exc:
        logger.exception("Google OAuth callback failed: %s", exc)
        return RedirectResponse(
            frontend_redirect_error("oauth_failed"),
            status_code=302,
        )


@router.get("/weibo/start")
async def oauth_weibo_start() -> RedirectResponse:
    """Redirect browser to Weibo consent screen."""
    _require_weibo_config()
    state = create_oauth_state("weibo")
    redirect_uri = oauth_callback_redirect_uri("weibo")
    url = build_weibo_authorize_url(state, redirect_uri)
    return RedirectResponse(url=url, status_code=302)


@router.get("/weibo/callback")
async def oauth_weibo_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Handle Weibo redirect: exchange code, issue JWT, redirect to SPA."""
    if error:
        logger.warning(
            "Weibo OAuth error: %s %s",
            error,
            error_description or "",
        )
        return RedirectResponse(
            frontend_redirect_error("oauth_denied"),
            status_code=302,
        )
    if not code or not state:
        return RedirectResponse(
            frontend_redirect_error("invalid_request"),
            status_code=302,
        )
    if verify_oauth_state(state) != "weibo":
        return RedirectResponse(
            frontend_redirect_error("invalid_state"),
            status_code=302,
        )
    redirect_uri = oauth_callback_redirect_uri("weibo")
    try:
        token = await complete_weibo_oauth(db, code, redirect_uri)
        return RedirectResponse(
            frontend_redirect_success(token),
            status_code=302,
        )
    except PermissionError:
        return RedirectResponse(
            frontend_redirect_error("email_conflict"),
            status_code=302,
        )
    except Exception as exc:
        logger.exception("Weibo OAuth callback failed: %s", exc)
        return RedirectResponse(
            frontend_redirect_error("oauth_failed"),
            status_code=302,
        )


@router.get("/qq/start")
async def oauth_qq_start() -> RedirectResponse:
    """Redirect browser to QQ Connect consent screen."""
    _require_qq_config()
    state = create_oauth_state("qq")
    redirect_uri = oauth_callback_redirect_uri("qq")
    url = build_qq_authorize_url(state, redirect_uri)
    return RedirectResponse(url=url, status_code=302)


@router.get("/qq/callback")
async def oauth_qq_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Handle QQ redirect: exchange code, issue JWT, redirect to SPA."""
    if error:
        logger.warning(
            "QQ OAuth error: %s %s",
            error,
            error_description or "",
        )
        return RedirectResponse(
            frontend_redirect_error("oauth_denied"),
            status_code=302,
        )
    if not code or not state:
        return RedirectResponse(
            frontend_redirect_error("invalid_request"),
            status_code=302,
        )
    if verify_oauth_state(state) != "qq":
        return RedirectResponse(
            frontend_redirect_error("invalid_state"),
            status_code=302,
        )
    redirect_uri = oauth_callback_redirect_uri("qq")
    try:
        token = await complete_qq_oauth(db, code, redirect_uri)
        return RedirectResponse(
            frontend_redirect_success(token),
            status_code=302,
        )
    except PermissionError:
        return RedirectResponse(
            frontend_redirect_error("email_conflict"),
            status_code=302,
        )
    except Exception as exc:
        logger.exception("QQ OAuth callback failed: %s", exc)
        return RedirectResponse(
            frontend_redirect_error("oauth_failed"),
            status_code=302,
        )


@router.get("/alipay/start")
async def oauth_alipay_start() -> RedirectResponse:
    """Redirect browser to Alipay consent screen (``auth_user``)."""
    _require_alipay_oauth_config()
    state = create_oauth_state("alipay")
    redirect_uri = oauth_callback_redirect_uri("alipay")
    url = build_alipay_authorize_url(state, redirect_uri)
    return RedirectResponse(url=url, status_code=302)


@router.get("/alipay/callback")
async def oauth_alipay_callback(
    auth_code: str | None = None,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Handle Alipay redirect: exchange auth_code, issue JWT, redirect to SPA."""
    if error:
        logger.warning("Alipay OAuth error: %s", error)
        return RedirectResponse(
            frontend_redirect_error("oauth_denied"),
            status_code=302,
        )
    resolved_code = auth_code or code
    if not resolved_code or not state:
        return RedirectResponse(
            frontend_redirect_error("invalid_request"),
            status_code=302,
        )
    if verify_oauth_state(state) != "alipay":
        return RedirectResponse(
            frontend_redirect_error("invalid_state"),
            status_code=302,
        )
    redirect_uri = oauth_callback_redirect_uri("alipay")
    try:
        token = await complete_alipay_oauth(db, resolved_code, redirect_uri)
        return RedirectResponse(
            frontend_redirect_success(token),
            status_code=302,
        )
    except PermissionError:
        return RedirectResponse(
            frontend_redirect_error("email_conflict"),
            status_code=302,
        )
    except Exception as exc:
        logger.exception("Alipay OAuth callback failed: %s", exc)
        return RedirectResponse(
            frontend_redirect_error("oauth_failed"),
            status_code=302,
        )
