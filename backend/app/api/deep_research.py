"""Deep Research API (DeerFlow integration)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.limits import ROLE_LIMITS
from app.models.notebook import Notebook
from app.models.source import Source
from app.models.studio import DeepResearchReport
from app.models.user import User
from app.ratelimit import (
    GenerationKind,
    acquire_generation_rate_limit_slot,
    release_generation_rate_limit_on_db_failure,
)
from app.schemas.source import SourceResponse
from app.schemas.studio import DeepResearchCreate, DeepResearchResponse
from app.services.infra.deep_research_celery_control import (
    revoke_deep_research_task,
)
from app.services.task_event_service import publish_task_event
from app.tasks.deep_research_tasks import run_deep_research_for_report_task
from app.tasks.source_tasks import process_source_task

router = APIRouter(tags=["deep-research"])

_TERMINAL_DEEP_RESEARCH_STATUSES = frozenset({"ready", "error"})
_CANCELLED_ERROR_MESSAGE = "任务已取消。"


async def _verify_notebook_access(
    db: AsyncSession, notebook_id: str, user_id: str
) -> None:
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


async def _get_report_and_verify(
    db: AsyncSession, report_id: str, user_id: str
) -> DeepResearchReport:
    """Get deep research report and verify user access via notebook."""
    result = await db.execute(
        select(DeepResearchReport)
        .join(Notebook, DeepResearchReport.notebook_id == Notebook.id)
        .where(
            DeepResearchReport.id == report_id,
            Notebook.user_id == user_id,
        )
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deep research report not found",
        )
    return report


@router.post(
    "/api/notebooks/{notebook_id}/deep-research",
    response_model=DeepResearchResponse,
    status_code=202,
)
async def create_deep_research(
    notebook_id: str,
    body: DeepResearchCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Create a deep research task and run it in background via DeerFlow. Returns 202."""
    await _verify_notebook_access(db, notebook_id, str(user.id))
    if not (body.query and body.query.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="query is required",
        )

    rl_redis, acquired, _, dr_daily = await acquire_generation_rate_limit_slot(
        db,
        user_id=str(user.id),
        kind=GenerationKind.DEEP_RESEARCH,
        notebook_id=notebook_id,
        source_ids=None,
        artifact_id=None,
        user_role=user.role,
    )
    report_id: str
    try:
        report = DeepResearchReport(
            notebook_id=notebook_id,
            query=body.query.strip(),
            status="pending",
        )
        db.add(report)
        await db.flush()
        await db.refresh(report)
        report_id = report.id
        await db.commit()
    except Exception:
        await db.rollback()
        await release_generation_rate_limit_on_db_failure(
            rl_redis,
            acquired,
            user_id=str(user.id),
            daily_slide_reserved=False,
            daily_deep_research_reserved=dr_daily,
        )
        raise
    finally:
        await rl_redis.aclose()

    await publish_task_event("deep-research", report_id, "pending")
    async_result = run_deep_research_for_report_task.delay(report_id)
    await db.execute(
        update(DeepResearchReport)
        .where(DeepResearchReport.id == report_id)
        .values(celery_task_id=async_result.id)
    )
    await db.commit()
    result = await db.execute(
        select(DeepResearchReport).where(DeepResearchReport.id == report_id)
    )
    saved = result.scalar_one()
    return DeepResearchResponse.from_orm_report(saved)


@router.get(
    "/api/notebooks/{notebook_id}/deep-research",
    response_model=list[DeepResearchResponse],
)
async def list_deep_research(
    notebook_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """List deep research reports for a notebook."""
    await _verify_notebook_access(db, notebook_id, str(user.id))
    result = await db.execute(
        select(DeepResearchReport)
        .where(DeepResearchReport.notebook_id == notebook_id)
        .order_by(DeepResearchReport.created_at.desc())
    )
    return [
        DeepResearchResponse.from_orm_report(r)
        for r in result.scalars().all()
    ]


@router.get(
    "/api/deep-research/{report_id}",
    response_model=DeepResearchResponse,
)
async def get_deep_research(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get a single deep research report (for polling status and content)."""
    report = await _get_report_and_verify(db, report_id, str(user.id))
    return DeepResearchResponse.from_orm_report(report)


@router.post(
    "/api/deep-research/{report_id}/cancel",
    response_model=DeepResearchResponse,
)
async def cancel_deep_research(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Cancel an in-flight deep research task and mark the report as error."""
    report = await _get_report_and_verify(db, report_id, str(user.id))
    if report.status in _TERMINAL_DEEP_RESEARCH_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="任务已结束，无法取消",
        )
    revoke_deep_research_task(report.celery_task_id)
    report.status = "error"
    report.error_message = _CANCELLED_ERROR_MESSAGE
    await db.commit()
    await db.refresh(report)
    await publish_task_event(
        "deep-research",
        report.id,
        report.status,
        report.error_message,
    )
    return DeepResearchResponse.from_orm_report(report)


@router.delete("/api/deep-research/{report_id}", status_code=204)
async def delete_deep_research(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Delete a deep research report."""
    report = await _get_report_and_verify(db, report_id, str(user.id))
    revoke_deep_research_task(report.celery_task_id)
    await db.delete(report)
    await db.commit()


@router.post(
    "/api/notebooks/{notebook_id}/deep-research/{report_id}/import-source",
    response_model=SourceResponse,
    status_code=201,
)
async def import_deep_research_as_source(
    notebook_id: str,
    report_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a markdown source from a completed deep research report."""
    await _verify_notebook_access(db, notebook_id, str(user.id))
    report = await _get_report_and_verify(db, report_id, str(user.id))
    if report.notebook_id != notebook_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deep research report not found",
        )
    if report.status != "ready":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅已完成的研究可导入为来源",
        )
    if not (report.content and report.content.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="报告内容为空，无法导入",
        )

    limits = ROLE_LIMITS.get(user.role, ROLE_LIMITS["free"])
    count_result = await db.execute(
        select(func.count(Source.id)).where(Source.notebook_id == notebook_id)
    )
    current_count = count_result.scalar_one()
    if current_count >= limits["max_sources_per_notebook"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"该笔记本已达到资源数量上限（{limits['max_sources_per_notebook']}）。"
                "请升级账户以添加更多资源。"
            ),
        )

    title = report.query.strip()
    if len(title) > 255:
        title = title[:252] + "..."

    source = Source(
        notebook_id=notebook_id,
        title=title or "Deep Research",
        type="markdown",
        original_url=None,
        raw_content=report.content,
        status="pending",
    )
    db.add(source)
    await db.flush()
    await db.refresh(source)
    await db.commit()
    await db.refresh(source)

    await publish_task_event("source", source.id, source.status)
    process_source_task.delay(source.id)
    return SourceResponse.model_validate(source)
