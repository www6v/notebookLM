"""Tests for Deep Research Celery revoke helper."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.services.infra.deep_research_celery_control import (
    revoke_deep_research_task,
)


def test_revoke_skips_when_task_id_missing() -> None:
    with patch("app.tasks.celery_app.celery_app") as m:
        revoke_deep_research_task(None)
        revoke_deep_research_task("")
        m.control.revoke.assert_not_called()


def test_revoke_calls_control_with_terminate() -> None:
    mock_app = MagicMock()
    with patch("app.tasks.celery_app.celery_app", mock_app):
        revoke_deep_research_task("task-uuid-1")
    mock_app.control.revoke.assert_called_once_with(
        "task-uuid-1",
        terminate=True,
    )
