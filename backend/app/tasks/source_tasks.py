"""Celery tasks for async source processing."""

import logging

import app.models  # noqa: F401
from app.tasks.async_runner import run_async_in_worker
from app.tasks.celery_app import celery_app
from app.services.task_event_service import publish_task_event

logger = logging.getLogger(__name__)


@celery_app.task(
    name="process_source",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def process_source_task(source_id: str):
    """Background task to process a source document.

    This runs the async process_source function in a sync context
    for Celery compatibility.
    """
    from app.database import async_session
    from app.models.source import Source
    from app.services.source.source_service import (
        finalize_uploaded_audio,
        finalize_uploaded_image,
        finalize_uploaded_video,
        finalize_url_source,
        process_source,
    )
    from app.services.source.source_metadata_skill_service import (
        enrich_source_metadata_with_skill,
    )
    from sqlalchemy import select

    async def _run():
        await publish_task_event("source", source_id, "processing")
        async with async_session() as session:
            try:
                result = await session.execute(
                    select(Source).where(Source.id == source_id)
                )
                source = result.scalar_one_or_none()
                if source is None:
                    return

                if source.type == "video":
                    await finalize_uploaded_video(session, source)
                elif source.type == "audio":
                    await finalize_uploaded_audio(session, source)
                elif source.type == "image":
                    await finalize_uploaded_image(session, source)
                elif source.type in (
                    "web",
                    "youtube",
                    "bilibili",
                ) and source.original_url:
                    await finalize_url_source(session, source)
                else:
                    await process_source(session, source_id)

                if source.file_path and source.status == "ready":
                    try:
                        await enrich_source_metadata_with_skill(session, source)
                    except Exception:
                        logger.exception(
                            "Source metadata enrichment failed for %s",
                            source_id,
                        )
                await session.commit()
                result = await session.execute(
                    select(Source).where(Source.id == source_id)
                )
                source = result.scalar_one_or_none()
                if source is not None:
                    await publish_task_event("source", source_id, source.status)
            except Exception:
                await session.rollback()
                logger.exception("Source processing failed for %s", source_id)
                await publish_task_event("source", source_id, "error")
                raise

    run_async_in_worker(_run())
