"""Celery application configuration."""

from celery import Celery

from app.config import settings

celery_app = Celery(
    "notebooklm",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)
