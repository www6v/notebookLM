"""Shared API dependencies (e.g. current user)."""

from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from notebooklm_shared.database import get_db
from notebooklm_shared.models.user import User
from notebooklm_shared.auth.service import (
    decode_access_token,
    get_user_by_id,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate the current user from the JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    if (
        user.role == "paid"
        and user.subscription_expires_at is not None
        and user.subscription_expires_at < datetime.now(timezone.utc)
    ):
        user.role = "free"
        user.subscription_plan = "free"
        db.add(user)
        await db.flush()

    return user


async def get_current_admin(
    user: User = Depends(get_current_user),
) -> User:
    """Require the current user to be an admin."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user
