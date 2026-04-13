"""Langfuse client for optional tracing. When keys are not set, returns None."""

import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

_LANGFUSE_CLIENT: Any = None


def get_langfuse_client() -> Any:
    """Return Langfuse client when LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are set.

    Otherwise return None so callers can skip instrumentation. Client is a singleton.
    """
    global _LANGFUSE_CLIENT
    if _LANGFUSE_CLIENT is not None:
        return _LANGFUSE_CLIENT
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None
    try:
        from langfuse import Langfuse

        _LANGFUSE_CLIENT = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            base_url=settings.langfuse_base_url,
        )
        return _LANGFUSE_CLIENT
    except Exception as e:
        logger.warning("Langfuse client init failed, tracing disabled: %s", e)
        return None
