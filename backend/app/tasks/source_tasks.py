"""Celery tasks for async source processing."""

import asyncio

from app.tasks.celery_app import celery_app


@celery_app.task(name="process_source")
def process_source_task(source_id: str):
    """Background task to process a source document.

    This runs the async process_source function in a sync context
    for Celery compatibility.
    """
    from app.database import async_session
    from app.services.source_service import process_source

    async def _run():
        async with async_session() as session:
            try:
                await process_source(session, source_id)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    asyncio.run(_run())
