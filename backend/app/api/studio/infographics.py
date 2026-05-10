"""Infographic API routes."""

import asyncio
import logging
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from notebooklm_shared.database import get_db
from notebooklm_shared.models.notebook import Notebook
from app.ratelimit import (
    GenerationKind,
    acquire_generation_rate_limit_slot,
    release_generation_rate_limit_on_db_failure,
)
from notebooklm_shared.models.studio import Infographic
from notebooklm_shared.models.user import User
from app.schemas.studio import (
    InfographicCreate,
    InfographicResponse,
    InfographicStatus,
    InfographicUpdate,
)
from app.services.infra.obs_storage import (
    download_file_from_obs,
    generate_presigned_url,
)
from app.services.studio.studio_storage_cleanup import (
    delete_studio_objects_best_effort,
)
from app.services.studio.studio_status_service import (
    clear_generation_error,
    reconcile_stale_generation,
    reconcile_stale_generations,
)
from app.services.task_event_service import publish_task_event
from app.tasks.studio_tasks import generate_infographic_task

logger = logging.getLogger(__name__)
router = APIRouter(tags=["infographics"])


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


async def _get_infographic(
    db: AsyncSession, infographic_id: str, user_id: str
) -> Infographic:
    """Get an infographic and verify user access."""
    result = await db.execute(
        select(Infographic)
        .join(Notebook, Infographic.notebook_id == Notebook.id)
        .where(
            Infographic.id == infographic_id, Notebook.user_id == user_id
        )
    )
    infographic = result.scalar_one_or_none()
    if infographic is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Infographic not found",
        )
    return infographic


@router.post(
    "/api/notebooks/{notebook_id}/infographics",
    response_model=InfographicResponse,
    status_code=202,
)
async def generate_infographic(
    notebook_id: str,
    body: InfographicCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a pending infographic and run generation in background. Returns 202."""
    await _verify_notebook_access(db, notebook_id, user.id)
    rl_redis, acquired, _, _ = await acquire_generation_rate_limit_slot(
        db,
        user_id=user.id,
        kind=GenerationKind.INFOGRAPHIC,
        notebook_id=notebook_id,
        source_ids=body.source_ids,
        artifact_id=None,
    )
    try:
        source_count = len(body.source_ids) if body.source_ids else 0
        infographic = Infographic(
            notebook_id=notebook_id,
            title=body.title,
            layout_data=None,
            status=InfographicStatus.PENDING.value,
            error_message=None,
            file_path=None,
            infographic_style=body.infographic_style or "标准",
            infographic_language=body.infographic_language or "简体中文",
            infographic_direction=body.infographic_direction or "横向",
            infographic_visual_style=(
                body.infographic_visual_style or "craft-handmade"
            ),
            infographic_custom_prompt=body.infographic_custom_prompt,
            source_count=source_count if source_count > 0 else None,
        )
        db.add(infographic)
        await db.flush()
        await db.refresh(infographic)
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

    await publish_task_event("infographic", infographic.id, infographic.status)
    generate_infographic_task.delay(infographic.id, body.source_ids)
    return InfographicResponse.model_validate(infographic)


@router.get(
    "/api/notebooks/{notebook_id}/infographics",
    response_model=list[InfographicResponse],
)
async def list_infographics(
    notebook_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List infographics in a notebook."""
    await _verify_notebook_access(db, notebook_id, user.id)
    result = await db.execute(
        select(Infographic)
        .where(Infographic.notebook_id == notebook_id)
        .order_by(Infographic.created_at.desc())
    )
    infographics = result.scalars().all()
    if reconcile_stale_generations(infographics):
        await db.flush()
    return [
        InfographicResponse.model_validate(i)
        for i in infographics
    ]


@router.get(
    "/api/infographics/{infographic_id}",
    response_model=InfographicResponse,
)
async def get_infographic(
    infographic_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get an infographic by ID."""
    infographic = await _get_infographic(db, infographic_id, user.id)
    if reconcile_stale_generation(infographic):
        await db.flush()
    return InfographicResponse.model_validate(infographic)


@router.get("/api/infographics/{infographic_id}/image-url")
async def get_infographic_image_url(
    infographic_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a presigned URL for the infographic image stored in OSS."""
    infographic = await _get_infographic(db, infographic_id, user.id)
    if not infographic.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not available for this infographic",
        )
    url = generate_presigned_url(infographic.file_path, expiration=3600)
    return {"url": url}


@router.get("/api/infographics/{infographic_id}/image")
async def get_infographic_image(
    infographic_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Stream the infographic image through the API (same-origin, avoids storage CORS)."""
    infographic = await _get_infographic(db, infographic_id, user.id)
    if not infographic.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not available for this infographic",
        )
    try:
        image_bytes = await asyncio.to_thread(
            download_file_from_obs,
            infographic.file_path,
        )
    except RuntimeError as exc:
        logger.exception("Infographic image download failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to load infographic image from storage",
        ) from exc
    display_base = (
        infographic.suggested_filename or infographic.title or "infographic"
    ).replace('"', "")
    if not display_base.lower().endswith(".png"):
        display_base = f"{display_base}.png"
    ascii_name = "infographic.png"
    utf8_quoted = quote(display_base, safe="")
    content_disposition = (
        f'inline; filename="{ascii_name}"; filename*=UTF-8\'\'{utf8_quoted}'
    )
    return Response(
        content=image_bytes,
        media_type="image/png",
        headers={
            "Content-Disposition": content_disposition,
            "Cache-Control": "private, max-age=300",
        },
    )


@router.put(
    "/api/infographics/{infographic_id}",
    response_model=InfographicResponse,
)
async def update_infographic(
    infographic_id: str,
    body: InfographicUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update an infographic's options (no regeneration)."""
    infographic = await _get_infographic(db, infographic_id, user.id)
    if body.title is not None:
        infographic.title = body.title
    if body.infographic_style is not None:
        infographic.infographic_style = body.infographic_style
    if body.infographic_language is not None:
        infographic.infographic_language = body.infographic_language
    if body.infographic_direction is not None:
        infographic.infographic_direction = body.infographic_direction
    if body.infographic_visual_style is not None:
        infographic.infographic_visual_style = body.infographic_visual_style
    if body.infographic_custom_prompt is not None:
        infographic.infographic_custom_prompt = body.infographic_custom_prompt
    await db.flush()
    await db.refresh(infographic)
    return InfographicResponse.model_validate(infographic)


@router.post(
    "/api/infographics/{infographic_id}/regenerate",
    response_model=InfographicResponse,
    status_code=202,
)
async def regenerate_infographic(
    infographic_id: str,
    body: InfographicUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update infographic options and re-run generation in background. Returns 202."""
    infographic = await _get_infographic(db, infographic_id, user.id)
    rl_redis, acquired, _, _ = await acquire_generation_rate_limit_slot(
        db,
        user_id=user.id,
        kind=GenerationKind.INFOGRAPHIC,
        notebook_id=infographic.notebook_id,
        source_ids=None,
        artifact_id=infographic.id,
    )
    try:
        if body.title is not None:
            infographic.title = body.title
        if body.infographic_style is not None:
            infographic.infographic_style = body.infographic_style
        if body.infographic_language is not None:
            infographic.infographic_language = body.infographic_language
        if body.infographic_direction is not None:
            infographic.infographic_direction = body.infographic_direction
        if body.infographic_visual_style is not None:
            infographic.infographic_visual_style = body.infographic_visual_style
        if body.infographic_custom_prompt is not None:
            infographic.infographic_custom_prompt = body.infographic_custom_prompt
        infographic.status = InfographicStatus.PENDING.value
        infographic.layout_data = None
        infographic.file_path = None
        clear_generation_error(infographic)
        await db.flush()
        await db.refresh(infographic)
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
    await publish_task_event("infographic", infographic.id, infographic.status)
    generate_infographic_task.delay(infographic.id, None)
    return InfographicResponse.model_validate(infographic)


@router.delete("/api/infographics/{infographic_id}", status_code=204)
async def delete_infographic(
    infographic_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete an infographic and its image from object storage."""
    infographic = await _get_infographic(db, infographic_id, user.id)
    delete_studio_objects_best_effort([infographic.file_path])
    await db.delete(infographic)
