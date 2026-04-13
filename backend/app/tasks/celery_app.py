"""Celery application configuration."""

from celery import Celery
from kombu import Queue

import app.models
from app.config import settings


def _resolve_celery_broker_url() -> str:
    """Resolve the broker URL with backwards-compatible fallbacks."""
    return settings.celery_broker_url or settings.redis_url


def _resolve_celery_result_backend_url() -> str:
    """Resolve the result backend URL with backwards-compatible fallbacks."""
    return settings.celery_result_backend_url or settings.redis_url


celery_app = Celery(
    "notebooklm",
    broker=_resolve_celery_broker_url(),
    backend=_resolve_celery_result_backend_url(),
    include=[
        "app.tasks.source_tasks",
        "app.tasks.studio_tasks",
        "app.tasks.deep_research_tasks",
    ],
)

celery_app.conf.update(
    worker_hijack_root_logger=False,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_default_queue="general",
    task_queues=(
        Queue("general"),
        Queue("ingestion"),
        Queue("studio"),
        Queue("research"),
    ),
    task_routes={
        "process_source": {"queue": "ingestion"},
        "generate_mindmap": {"queue": "studio"},
        "generate_slide_deck": {"queue": "studio"},
        "generate_infographic": {"queue": "studio"},
        "generate_report": {"queue": "studio"},
        "run_deep_research": {"queue": "research"},
    },
)

from app.logging_setup import configure_logging

configure_logging()

# Import task modules so workers started from this module always register them.
from app.tasks import deep_research_tasks, source_tasks, studio_tasks  # noqa: F401
