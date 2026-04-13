"""Celery tasks for async studio features: mind map, slide deck generation."""

import asyncio
import logging

import httpx
import app.models  # noqa: F401
from app.services.studio_status_service import normalize_generation_error_message
from app.tasks.async_runner import run_async_in_worker
from app.tasks.celery_app import celery_app
from app.services.task_event_service import publish_task_event

logger = logging.getLogger(__name__)
STUDIO_TASK_RETRY_DELAYS = (15, 30)
RETRYABLE_HTTP_STATUS_CODES = {408, 409, 425, 429, 500, 502, 503, 504}


def _is_retryable_studio_exception(exc: Exception) -> bool:
    """Return whether a studio task failure is likely transient."""
    if isinstance(
        exc,
        (
            asyncio.TimeoutError,
            TimeoutError,
            ConnectionError,
            httpx.ConnectError,
            httpx.TimeoutException,
            httpx.ReadError,
            httpx.RemoteProtocolError,
        ),
    ):
        return True
    if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
        return exc.response.status_code in RETRYABLE_HTTP_STATUS_CODES
    return False


def _next_retry_delay(current_retry_count: int) -> int | None:
    """Return the next retry delay in seconds for a worker attempt."""
    if current_retry_count >= len(STUDIO_TASK_RETRY_DELAYS):
        return None
    return STUDIO_TASK_RETRY_DELAYS[current_retry_count]


async def _persist_generation_failure(
    *,
    session,
    record,
    output_kind: str,
    record_id: str,
    reason: str,
    error_message: str,
    mark_generation_as_error,
) -> str:
    """Persist one terminal error state without masking the original failure."""
    normalized_message = normalize_generation_error_message(error_message)
    if record is not None:
        try:
            mark_generation_as_error(
                record,
                reason,
                normalized_message,
            )
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception(
                "Failed to persist %s error state for %s",
                output_kind,
                record_id,
            )
    await publish_task_event(
        output_kind,
        record_id,
        "error",
        normalized_message,
    )
    return normalized_message


@celery_app.task(bind=True, name="generate_mindmap")
def generate_mindmap_task(
    self,
    mindmap_id: str,
    notebook_id: str,
    title: str,
    source_ids: list[str] | None = None,
):
    """Background task to generate a mind map for an existing pending record."""
    from app.database import async_session
    from app.models.studio import MindMap
    from app.services.mindmap_service import run_mindmap_generation_for_existing
    from app.services.studio_status_service import mark_generation_as_error
    from sqlalchemy import select

    async def _run():
        await publish_task_event("mindmap", mindmap_id, "processing")
        async with async_session() as session:
            try:
                await run_mindmap_generation_for_existing(
                    session,
                    mindmap_id,
                    source_ids=source_ids,
                )
                await session.commit()
                result = await session.execute(
                    select(MindMap).where(MindMap.id == mindmap_id)
                )
                mind_map = result.scalar_one_or_none()
                if mind_map is not None:
                    await publish_task_event(
                        "mindmap",
                        mindmap_id,
                        mind_map.status,
                        getattr(mind_map, "error_message", None),
                    )
            except Exception as exc:
                await session.rollback()
                if _is_retryable_studio_exception(exc):
                    retry_delay = _next_retry_delay(self.request.retries)
                    if retry_delay is not None:
                        logger.warning(
                            "Mind map generation retrying for %s in %ss after %s",
                            mindmap_id,
                            retry_delay,
                            type(exc).__name__,
                        )
                        raise self.retry(exc=exc, countdown=retry_delay)
                logger.exception("Mind map generation failed for %s", mindmap_id)
                result = await session.execute(
                    select(MindMap).where(MindMap.id == mindmap_id)
                )
                mind_map = result.scalar_one_or_none()
                await _persist_generation_failure(
                    session=session,
                    record=mind_map,
                    output_kind="mindmap",
                    record_id=mindmap_id,
                    reason="mind map generation failed in worker task",
                    error_message=str(exc),
                    mark_generation_as_error=mark_generation_as_error,
                )
                raise

    run_async_in_worker(_run())


@celery_app.task(bind=True, name="generate_slide_deck")
def generate_slide_deck_task(
    self,
    slide_deck_id: str,
    source_ids: list[str] | None = None,
    focus_topic: str | None = None,
):
    """Background task to generate a slide deck for an existing pending record."""
    from app.database import async_session
    from app.models.studio import SlideDeck
    from app.services.slide_service import run_slide_deck_generation_for_existing
    from app.services.studio_status_service import mark_generation_as_error
    from sqlalchemy import select

    async def _run():
        await publish_task_event("slide", slide_deck_id, "processing")
        async with async_session() as session:
            try:
                await run_slide_deck_generation_for_existing(
                    session,
                    slide_deck_id,
                    source_ids=source_ids,
                    focus_topic=focus_topic,
                )
                await session.commit()
                result = await session.execute(
                    select(SlideDeck).where(SlideDeck.id == slide_deck_id)
                )
                slide_deck = result.scalar_one_or_none()
                if slide_deck is not None:
                    await publish_task_event(
                        "slide",
                        slide_deck_id,
                        slide_deck.status,
                        getattr(slide_deck, "error_message", None),
                    )
            except Exception as exc:
                await session.rollback()
                if _is_retryable_studio_exception(exc):
                    retry_delay = _next_retry_delay(self.request.retries)
                    if retry_delay is not None:
                        logger.warning(
                            "Slide deck generation retrying for %s in %ss after %s",
                            slide_deck_id,
                            retry_delay,
                            type(exc).__name__,
                        )
                        raise self.retry(exc=exc, countdown=retry_delay)
                logger.exception(
                    "Slide deck generation failed for %s",
                    slide_deck_id,
                )
                result = await session.execute(
                    select(SlideDeck).where(SlideDeck.id == slide_deck_id)
                )
                slide_deck = result.scalar_one_or_none()
                await _persist_generation_failure(
                    session=session,
                    record=slide_deck,
                    output_kind="slide",
                    record_id=slide_deck_id,
                    reason="slide deck generation failed in worker task",
                    error_message=str(exc),
                    mark_generation_as_error=mark_generation_as_error,
                )
                raise

    run_async_in_worker(_run())


@celery_app.task(bind=True, name="generate_infographic")
def generate_infographic_task(
    self,
    infographic_id: str,
    source_ids: list[str] | None = None,
):
    """Background task to generate an infographic for an existing record."""
    from app.database import async_session
    from app.models.studio import Infographic
    from app.services.infographic_service import (
        run_infographic_generation_for_existing,
    )
    from app.services.studio_status_service import mark_generation_as_error
    from sqlalchemy import select

    async def _run():
        await publish_task_event("infographic", infographic_id, "processing")
        async with async_session() as session:
            try:
                await run_infographic_generation_for_existing(
                    session,
                    infographic_id,
                    source_ids=source_ids,
                )
                await session.commit()
                result = await session.execute(
                    select(Infographic).where(Infographic.id == infographic_id)
                )
                infographic = result.scalar_one_or_none()
                if infographic is not None:
                    await publish_task_event(
                        "infographic",
                        infographic_id,
                        infographic.status,
                        getattr(infographic, "error_message", None),
                    )
            except Exception as exc:
                await session.rollback()
                if _is_retryable_studio_exception(exc):
                    retry_delay = _next_retry_delay(self.request.retries)
                    if retry_delay is not None:
                        logger.warning(
                            "Infographic generation retrying for %s in %ss after %s",
                            infographic_id,
                            retry_delay,
                            type(exc).__name__,
                        )
                        raise self.retry(exc=exc, countdown=retry_delay)
                logger.exception(
                    "Infographic generation failed for %s",
                    infographic_id,
                )
                result = await session.execute(
                    select(Infographic).where(Infographic.id == infographic_id)
                )
                infographic = result.scalar_one_or_none()
                await _persist_generation_failure(
                    session=session,
                    record=infographic,
                    output_kind="infographic",
                    record_id=infographic_id,
                    reason="infographic generation failed in worker task",
                    error_message=str(exc),
                    mark_generation_as_error=mark_generation_as_error,
                )
                raise

    run_async_in_worker(_run())


@celery_app.task(bind=True, name="generate_report")
def generate_report_task(
    self,
    report_id: str,
    source_ids: list[str] | None = None,
):
    """Background task to generate a report for an existing record."""
    from app.database import async_session
    from app.models.studio import Report
    from app.services.report_service import run_report_generation_for_existing
    from app.services.studio_status_service import mark_generation_as_error
    from sqlalchemy import select

    async def _run():
        await publish_task_event("report", report_id, "processing")
        async with async_session() as session:
            try:
                await run_report_generation_for_existing(
                    session,
                    report_id,
                    source_ids=source_ids,
                )
                await session.commit()
                result = await session.execute(
                    select(Report).where(Report.id == report_id)
                )
                report = result.scalar_one_or_none()
                if report is not None:
                    await publish_task_event(
                        "report",
                        report_id,
                        report.status,
                        getattr(report, "error_message", None),
                    )
            except Exception as exc:
                await session.rollback()
                if _is_retryable_studio_exception(exc):
                    retry_delay = _next_retry_delay(self.request.retries)
                    if retry_delay is not None:
                        logger.warning(
                            "Report generation retrying for %s in %ss after %s",
                            report_id,
                            retry_delay,
                            type(exc).__name__,
                        )
                        raise self.retry(exc=exc, countdown=retry_delay)
                logger.exception("Report generation failed for %s", report_id)
                result = await session.execute(
                    select(Report).where(Report.id == report_id)
                )
                report = result.scalar_one_or_none()
                await _persist_generation_failure(
                    session=session,
                    record=report,
                    output_kind="report",
                    record_id=report_id,
                    reason="report generation failed in worker task",
                    error_message=str(exc),
                    mark_generation_as_error=mark_generation_as_error,
                )
                raise

    run_async_in_worker(_run())


@celery_app.task(bind=True, name="generate_podcast")
def generate_podcast_task(
    self,
    podcast_id: str,
    source_ids: list[str] | None = None,
):
    """Background task: podcast-generation skill workflow + Qwen TTS."""
    from app.database import async_session
    from app.models.studio import PodcastOverview
    from app.services.podcast_service import run_podcast_generation_for_existing
    from app.services.studio_status_service import mark_generation_as_error
    from sqlalchemy import select

    async def _run():
        await publish_task_event("podcast", podcast_id, "processing")
        async with async_session() as session:
            try:
                await run_podcast_generation_for_existing(
                    session,
                    podcast_id,
                    source_ids=source_ids,
                )
                await session.commit()
                result = await session.execute(
                    select(PodcastOverview).where(PodcastOverview.id == podcast_id)
                )
                podcast = result.scalar_one_or_none()
                if podcast is not None:
                    await publish_task_event(
                        "podcast",
                        podcast_id,
                        podcast.status,
                        getattr(podcast, "error_message", None),
                    )
            except Exception as exc:
                await session.rollback()
                if _is_retryable_studio_exception(exc):
                    retry_delay = _next_retry_delay(self.request.retries)
                    if retry_delay is not None:
                        logger.warning(
                            "Podcast generation retrying for %s in %ss after %s",
                            podcast_id,
                            retry_delay,
                            type(exc).__name__,
                        )
                        raise self.retry(exc=exc, countdown=retry_delay)
                logger.exception("Podcast generation failed for %s", podcast_id)
                result = await session.execute(
                    select(PodcastOverview).where(PodcastOverview.id == podcast_id)
                )
                podcast = result.scalar_one_or_none()
                await _persist_generation_failure(
                    session=session,
                    record=podcast,
                    output_kind="podcast",
                    record_id=podcast_id,
                    reason="podcast generation failed in worker task",
                    error_message=str(exc),
                    mark_generation_as_error=mark_generation_as_error,
                )
                raise

    run_async_in_worker(_run())
