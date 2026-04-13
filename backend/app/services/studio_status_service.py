"""Helpers for keeping async studio generation statuses consistent."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Iterable

logger = logging.getLogger(__name__)

PENDING_GENERATION_STATUSES = {"pending", "processing"}
STALE_GENERATION_TIMEOUT = timedelta(minutes=30)
# Keep persisted error messages short enough to fit deployments where the
# database schema may still lag behind the latest Text migration.
MAX_ERROR_MESSAGE_LENGTH = 250


def _as_utc(value: datetime | None) -> datetime | None:
    """Normalize datetimes from the ORM to timezone-aware UTC."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def is_generation_pending(status: str | None) -> bool:
    """Return whether a studio generation is still considered in-flight."""
    return status in PENDING_GENERATION_STATUSES


def normalize_generation_error_message(
    message: str | None,
    fallback: str = "任务生成失败，请稍后重试。",
) -> str:
    """Normalize user-facing error messages before persisting them."""
    normalized = " ".join((message or "").split())
    if not normalized:
        normalized = fallback
    return normalized[:MAX_ERROR_MESSAGE_LENGTH]


def clear_generation_error(record: object) -> None:
    """Clear a persisted generation error message if the model supports it."""
    if hasattr(record, "error_message"):
        record.error_message = None


def mark_generation_as_error(
    record: object,
    reason: str,
    error_message: str | None = None,
) -> bool:
    """Force a generation record into error state."""
    normalized_message = normalize_generation_error_message(error_message)
    changed = False

    if getattr(record, "status", None) != "error":
        record.status = "error"
        changed = True
    if hasattr(record, "error_message") and record.error_message != normalized_message:
        record.error_message = normalized_message
        changed = True
    logger.warning(
        "Marking %s %s as error: %s",
        record.__class__.__name__,
        getattr(record, "id", "<unknown>"),
        reason,
    )
    return changed


def reconcile_stale_generation(record: object) -> bool:
    """Mark very old pending/processing studio records as error."""
    if not is_generation_pending(getattr(record, "status", None)):
        return False

    last_updated_at = _as_utc(getattr(record, "updated_at", None))
    created_at = _as_utc(getattr(record, "created_at", None))
    checkpoint = last_updated_at or created_at
    if checkpoint is None:
        return False

    now = datetime.now(timezone.utc)
    if now - checkpoint < STALE_GENERATION_TIMEOUT:
        return False

    return mark_generation_as_error(
        record,
        "generation exceeded stale timeout",
        (
            "任务处理超时，超过"
            f"{int(STALE_GENERATION_TIMEOUT.total_seconds() // 60)}分钟未完成，"
            "系统已自动结束。请重试。"
        ),
    )


def reconcile_stale_generations(records: Iterable[object]) -> bool:
    """Mark stale studio records in bulk. Returns whether any record changed."""
    changed = False
    for record in records:
        changed = reconcile_stale_generation(record) or changed
    return changed
