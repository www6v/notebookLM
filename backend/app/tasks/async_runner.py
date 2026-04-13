"""Helpers for running async code inside Celery worker processes."""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any

_worker_loop: asyncio.AbstractEventLoop | None = None


def run_async_in_worker(coro: Coroutine[Any, Any, Any]) -> Any:
    """Run a coroutine on a process-local event loop.

    Celery prefork workers execute synchronous task functions. Reusing one
    event loop per worker process avoids cross-loop reuse issues with async
    database and Redis clients.
    """
    global _worker_loop

    if _worker_loop is None or _worker_loop.is_closed():
        _worker_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_worker_loop)

    return _worker_loop.run_until_complete(coro)
