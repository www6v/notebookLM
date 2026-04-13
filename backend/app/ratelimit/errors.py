"""Rate limit errors for Studio generation."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, status


@dataclass
class GenerationRateLimited(Exception):
    """User-visible generation rate limit (maps to HTTP 429)."""

    code: str
    message: str
    retry_after_seconds: int | None = None


def http_exception_from_generation(exc: GenerationRateLimited) -> HTTPException:
    """Build FastAPI 429 with optional Retry-After header."""
    headers = {}
    if exc.retry_after_seconds is not None:
        headers["Retry-After"] = str(exc.retry_after_seconds)
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=exc.message,
        headers=headers if headers else None,
    )
