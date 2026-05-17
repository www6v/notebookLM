"""OpenAPI for OpenClaw / agent integrations."""

from fastapi import FastAPI

from app.open_api.errors import OpenApiBizError, open_api_biz_exception_handler
from app.open_api.router import router


def register_exception_handlers(app: FastAPI) -> None:
    """Register OpenAPI-specific exception handlers on the app."""
    app.exception_handler(OpenApiBizError)(open_api_biz_exception_handler)


__all__ = ["router", "register_exception_handlers"]
