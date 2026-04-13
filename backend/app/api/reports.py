"""Reports API routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.notebook import Notebook
from app.ratelimit import (
    GenerationKind,
    acquire_generation_rate_limit_slot,
    release_generation_rate_limit_on_db_failure,
)
from app.models.studio import Report
from app.models.user import User
from app.schemas.studio import (
    ReportCreate,
    ReportResponse,
    ReportStatus,
    ReportUpdate,
)
from app.services.studio_status_service import (
    clear_generation_error,
    reconcile_stale_generation,
    reconcile_stale_generations,
)
from app.services.task_event_service import publish_task_event
from app.tasks.studio_tasks import generate_report_task

logger = logging.getLogger(__name__)
router = APIRouter(tags=["reports"])

@router.post(
    "/api/notebooks/{notebook_id}/reports",
    response_model=ReportResponse,
    status_code=202,
)
async def generate_report(
    notebook_id: str,
    body: ReportCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a pending report and run generation in background. Returns 202."""
    await _verify_notebook_access(db, notebook_id, user.id)
    rl_redis, acquired, _, _ = await acquire_generation_rate_limit_slot(
        db,
        user_id=user.id,
        kind=GenerationKind.REPORT,
        notebook_id=notebook_id,
        source_ids=body.source_ids,
        artifact_id=None,
    )
    try:
        source_count = len(body.source_ids) if body.source_ids else 0
        report = Report(
            notebook_id=notebook_id,
            title=body.title,
            report_format=body.report_format or "briefing_doc",
            report_language=body.report_language or "简体中文",
            report_custom_prompt=body.report_custom_prompt,
            content=None,
            status=ReportStatus.PENDING.value,
            error_message=None,
            source_count=source_count if source_count > 0 else None,
        )
        db.add(report)
        await db.flush()
        await db.refresh(report)
        await db.commit()
    except Exception:
        await db.rollback()
        await release_generation_rate_limit_on_db_failure(
            rl_redis,
            acquired,
            user_id=user.id,
            daily_slide_reserved=False,
            daily_deep_research_reserved=False,
        )
        raise
    finally:
        await rl_redis.aclose()

    await publish_task_event("report", report.id, report.status)
    generate_report_task.delay(report.id, body.source_ids)
    return ReportResponse.model_validate(report)


@router.get(
    "/api/notebooks/{notebook_id}/reports",
    response_model=list[ReportResponse],
)
async def list_reports(
    notebook_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List reports in a notebook."""
    await _verify_notebook_access(db, notebook_id, user.id)
    result = await db.execute(
        select(Report)
        .where(Report.notebook_id == notebook_id)
        .order_by(Report.created_at.desc())
    )
    reports = result.scalars().all()
    if reconcile_stale_generations(reports):
        await db.flush()
    return [ReportResponse.model_validate(r) for r in reports]


@router.get(
    "/api/reports/{report_id}",
    response_model=ReportResponse,
)
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a report by ID."""
    report = await _get_report(db, report_id, user.id)
    if reconcile_stale_generation(report):
        await db.flush()
    return ReportResponse.model_validate(report)


@router.put(
    "/api/reports/{report_id}",
    response_model=ReportResponse,
)
async def update_report(
    report_id: str,
    body: ReportUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update a report's options."""
    report = await _get_report(db, report_id, user.id)
    if body.title is not None:
        report.title = body.title
    if body.report_format is not None:
        report.report_format = body.report_format
    if body.report_language is not None:
        report.report_language = body.report_language
    if body.report_custom_prompt is not None:
        report.report_custom_prompt = body.report_custom_prompt
    await db.flush()
    await db.refresh(report)
    return ReportResponse.model_validate(report)


@router.post(
    "/api/reports/{report_id}/regenerate",
    response_model=ReportResponse,
    status_code=202,
)
async def regenerate_report(
    report_id: str,
    body: ReportUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update report options and re-run generation in background. Returns 202."""
    report = await _get_report(db, report_id, user.id)
    rl_redis, acquired, _, _ = await acquire_generation_rate_limit_slot(
        db,
        user_id=user.id,
        kind=GenerationKind.REPORT,
        notebook_id=report.notebook_id,
        source_ids=None,
        artifact_id=report.id,
    )
    try:
        if body.title is not None:
            report.title = body.title
        if body.report_format is not None:
            report.report_format = body.report_format
        if body.report_language is not None:
            report.report_language = body.report_language
        if body.report_custom_prompt is not None:
            report.report_custom_prompt = body.report_custom_prompt
        report.status = ReportStatus.PENDING.value
        report.content = None
        clear_generation_error(report)
        await db.flush()
        await db.refresh(report)
        await db.commit()
    except Exception:
        await db.rollback()
        await release_generation_rate_limit_on_db_failure(
            rl_redis,
            acquired,
            user_id=user.id,
            daily_slide_reserved=False,
            daily_deep_research_reserved=False,
        )
        raise
    finally:
        await rl_redis.aclose()
    await publish_task_event("report", report.id, report.status)
    generate_report_task.delay(report.id, None)
    return ReportResponse.model_validate(report)


@router.delete("/api/reports/{report_id}", status_code=204)
async def delete_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a report (content is DB only; no object storage)."""
    report = await _get_report(db, report_id, user.id)
    await db.delete(report)


# ── Helpers ─────────────────────────────────────────────────────────────

async def _verify_notebook_access(
    db: AsyncSession, notebook_id: str, user_id: str
):
    """Verify the user has access to the notebook."""
    result = await db.execute(
        select(Notebook).where(
            Notebook.id == notebook_id, Notebook.user_id == user_id
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        )


async def _get_report(
    db: AsyncSession, report_id: str, user_id: str
) -> Report:
    """Get a report and verify user access."""
    result = await db.execute(
        select(Report)
        .join(Notebook, Report.notebook_id == Notebook.id)
        .where(Report.id == report_id, Notebook.user_id == user_id)
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    return report
