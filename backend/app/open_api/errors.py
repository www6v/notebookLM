"""OpenAPI response codes (IMA-compatible envelope)."""

from typing import Any


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
