"""Celery tasks for Deep Research generation."""

import logging

import app.models  # noqa: F401
from app.tasks.async_runner import run_async_in_worker
from app.tasks.celery_app import celery_app
from app.services.task_event_service import publish_task_event

logger = logging.getLogger(__name__)


@celery_app.task(
    name="run_deep_research",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=2,
)
def run_deep_research_for_report_task(report_id: str):
    """Run Deep Research asynchronously via Celery."""
    from app.services.infra.deep_research_service import (
        run_deep_research_for_report,
    )

    async def _run():
        await publish_task_event("deep-research", report_id, "processing")
        try:
            report = await run_deep_research_for_report(report_id)
            if report is not None:
                await publish_task_event(
                    "deep-research",
                    report_id,
                    report.status,
                    report.error_message,
                )
        except Exception:
            logger.exception("Deep research failed for %s", report_id)
            await publish_task_event("deep-research", report_id, "error")
            raise

    run_async_in_worker(_run())
