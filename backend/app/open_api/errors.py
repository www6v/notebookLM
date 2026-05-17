"""OpenAPI response codes (IMA-compatible envelope)."""

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


class OpenApiBizError(Exception):
    """Business error returned as code/msg in JSON body."""

    def __init__(self, code: int, msg: str, data: Any = None):
        self.code = code
        self.msg = msg
        self.data = data
        super().__init__(msg)


OK = 0
PARAM_ERROR = 210001
AUTH_FAILED = 20004
NOT_FOUND = 210035
FORBIDDEN = 210011
SERVICE_ERROR = 210003
RATE_LIMIT = 20002


def success(data: Any = None, msg: str = "ok") -> dict[str, Any]:
    """Build a successful OpenAPI envelope."""
    return {"code": OK, "msg": msg, "data": data or {}}


def fail(code: int, msg: str, data: Any = None) -> dict[str, Any]:
    """Build a failed OpenAPI envelope."""
    return {"code": code, "msg": msg, "data": data or {}}


async def open_api_biz_exception_handler(
    _request: Request, exc: OpenApiBizError
) -> JSONResponse:
    """Map OpenApiBizError to IMA-style JSON with HTTP status."""
    status = 400
    if exc.code == AUTH_FAILED:
        status = 401
    elif exc.code == NOT_FOUND:
        status = 404
    elif exc.code == FORBIDDEN:
        status = 403
    elif exc.code == RATE_LIMIT:
        status = 429
    return JSONResponse(
        status_code=status,
        content=fail(exc.code, exc.msg, exc.data),
    )
