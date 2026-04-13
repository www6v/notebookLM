"""Observability utilities (e.g. Langfuse tracing)."""

from app.observability.langfuse_client import get_langfuse_client

__all__ = ["get_langfuse_client"]
