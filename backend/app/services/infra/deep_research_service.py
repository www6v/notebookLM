"""Deep Research service: orchestrate DeerFlow and persist reports."""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.deer_flow_client import run_deep_research
from notebooklm_shared.config import settings
from notebooklm_shared.database import async_session
from notebooklm_shared.models.studio import DeepResearchReport
from app.services.studio.studio_status_service import (
    normalize_generation_error_message,
)

logger = logging.getLogger(__name__)

PROCESSING = "processing"
READY = "ready"
ERROR = "error"
PENDING = "pending"

DEEP_RESEARCH_WALL_CLOCK_TIMEOUT_SEC = 1800
TIMEOUT_ERROR_MESSAGE = "研究超过 30 分钟未完成，已中断。"


async def _persist_terminal_state(
    db: AsyncSession,
    report_id: str,
    *,
    status: str,
    error_message: str | None,
    content: str | None = None,
    source_count: int | None = None,
    popular_count: int | None = None,
) -> None:
    """Load report by id and apply terminal fields; no-op if row is gone."""
    result = await db.execute(
        select(DeepResearchReport).where(DeepResearchReport.id == report_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        return
    row.status = status
    row.error_message = error_message
    if content is not None:
        row.content = content
    if source_count is not None:
        row.source_count = source_count
    if popular_count is not None:
        row.popular_count = popular_count
    await db.flush()


async def run_deep_research_for_report(report_id: str) -> DeepResearchReport | None:
    """Run DeerFlow deep research for an existing DeepResearchReport record.

    Commits status=PROCESSING before the long DeerFlow call so the DB
    connection is not held (avoiding idle timeouts and row lock contention
    during retries). Opens a new session to persist the final state.
    """
    async with async_session() as db:
        result = await db.execute(
            select(DeepResearchReport).where(DeepResearchReport.id == report_id)
        )
        report = result.scalar_one_or_none()
        if report is None:
            logger.warning("DeepResearchReport not found: %s", report_id)
            return None

        query_text = report.query
        report.status = PROCESSING
        report.error_message = None
        await db.flush()
        await db.commit()

    try:
        content, source_count, popular_count = await asyncio.wait_for(
            run_deep_research(
                query_text,
                base_url=settings.deer_flow_base_url,
                timeout_seconds=settings.deer_flow_timeout_seconds,
            ),
            timeout=DEEP_RESEARCH_WALL_CLOCK_TIMEOUT_SEC,
        )
    except asyncio.TimeoutError:
        logger.warning("Deep research wall-clock timeout for %s", report_id)
        async with async_session() as db:
            await _persist_terminal_state(
                db,
                report_id,
                status=ERROR,
                error_message=TIMEOUT_ERROR_MESSAGE,
            )
            await db.commit()
            out = await db.execute(
                select(DeepResearchReport).where(DeepResearchReport.id == report_id)
            )
            return out.scalar_one_or_none()
    except Exception as exc:
        logger.exception("Deep research failed for report %s: %s", report_id, exc)
        msg = normalize_generation_error_message(str(exc))
        async with async_session() as db:
            await _persist_terminal_state(
                db,
                report_id,
                status=ERROR,
                error_message=msg,
            )
            await db.commit()
            out = await db.execute(
                select(DeepResearchReport).where(DeepResearchReport.id == report_id)
            )
            return out.scalar_one_or_none()

    async with async_session() as db:
        fresh_result = await db.execute(
            select(DeepResearchReport).where(DeepResearchReport.id == report_id)
        )
        fresh = fresh_result.scalar_one_or_none()
        if fresh is None:
            return None
        if fresh.status == ERROR:
            logger.info(
                "Skip marking ready for %s; report already in error state",
                report_id,
            )
            return fresh

        await _persist_terminal_state(
            db,
            report_id,
            status=READY,
            error_message=None,
            content=content or "",
            source_count=source_count,
            popular_count=popular_count,
        )
        await db.commit()
        out = await db.execute(
            select(DeepResearchReport).where(DeepResearchReport.id == report_id)
        )
        return out.scalar_one_or_none()
