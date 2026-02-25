"""Celery tasks for async studio features: mind map, slide deck generation."""

import asyncio

from app.tasks.celery_app import celery_app


@celery_app.task(name="generate_mindmap")
def generate_mindmap_task(
    mindmap_id: str,
    notebook_id: str,
    title: str,
    source_ids: list[str] | None = None,
):
    """Background task to generate a mind map for an existing pending record."""
    from app.database import async_session
    from app.services.mindmap_service import run_mindmap_generation_for_existing

    async def _run():
        async with async_session() as session:
            try:
                await run_mindmap_generation_for_existing(
                    session,
                    mindmap_id,
                    source_ids=source_ids,
                )
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    asyncio.run(_run())


@celery_app.task(name="generate_slide_deck")
def generate_slide_deck_task(
    slide_deck_id: str,
    source_ids: list[str] | None = None,
    focus_topic: str | None = None,
):
    """Background task to generate a slide deck for an existing pending record."""
    from app.database import async_session
    from app.services.slide_service import run_slide_deck_generation_for_existing

    async def _run():
        async with async_session() as session:
            try:
                await run_slide_deck_generation_for_existing(
                    session,
                    slide_deck_id,
                    source_ids=source_ids,
                    focus_topic=focus_topic,
                )
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    asyncio.run(_run())
