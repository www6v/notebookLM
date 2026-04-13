"""Celery control helpers for Deep Research tasks."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def revoke_deep_research_task(task_id: str | None) -> None:
    """Revoke a Deep Research Celery task if task_id is set.

    terminate=True may SIGTERM the worker child process handling the task.
    """
    if not task_id:
        return
    try:
        from app.tasks.celery_app import celery_app

        celery_app.control.revoke(task_id, terminate=True)
    except Exception:
        logger.exception("Failed to revoke deep research task %s", task_id)
