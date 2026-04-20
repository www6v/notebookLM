"""Podcast (audio overview) API routes."""

import asyncio
import logging
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
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
from app.models.studio import PodcastOverview
from app.models.user import User
from app.schemas.studio import PodcastCreate, PodcastResponse, PodcastStatus
from app.services.infra.obs_storage import (
    download_file_from_obs,
    generate_presigned_url,
)
from app.services.studio.studio_storage_cleanup import (
    delete_studio_objects_best_effort,
)
from app.services.studio.studio_status_service import (
    reconcile_stale_generation,
    reconcile_stale_generations,
)
from app.services.task_event_service import publish_task_event
from app.tasks.studio_tasks import generate_podcast_task

logger = logging.getLogger(__name__)
router = APIRouter(tags=["podcasts"])


async def _verify_notebook_access(
    db: AsyncSession, notebook_id: str, user_id: str
) -> None:
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


async def _get_podcast(
    db: AsyncSession, podcast_id: str, user_id: str
) -> PodcastOverview:
    result = await db.execute(
        select(PodcastOverview)
        .join(Notebook, PodcastOverview.notebook_id == Notebook.id)
        .where(
            PodcastOverview.id == podcast_id,
            Notebook.user_id == user_id,
        )
    )
    podcast = result.scalar_one_or_none()
    if podcast is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Podcast not found",
        )
    return podcast


@router.post(
    "/api/notebooks/{notebook_id}/podcasts",
    response_model=PodcastResponse,
    status_code=202,
)
async def create_podcast(
    notebook_id: str,
    body: PodcastCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a pending podcast overview and run generation in the background."""
    await _verify_notebook_access(db, notebook_id, user.id)
    rl_redis, acquired, _, _ = await acquire_generation_rate_limit_slot(
        db,
        user_id=user.id,
        kind=GenerationKind.PODCAST,
        notebook_id=notebook_id,
        source_ids=body.source_ids,
        artifact_id=None,
    )
    try:
        source_count = len(body.source_ids) if body.source_ids else 0
        podcast = PodcastOverview(
            notebook_id=notebook_id,
            title=body.title,
            suggested_filename=None,
            audio_format=body.audio_format or "deep_dive",
            audio_language=body.audio_language or "简体中文",
            audio_length=body.audio_length or "default",
            audio_focus_prompt=body.audio_focus_prompt,
            file_path=None,
            transcript=None,
            status=PodcastStatus.PENDING.value,
            error_message=None,
            source_count=source_count if source_count > 0 else None,
        )
        db.add(podcast)
        await db.flush()
        await db.refresh(podcast)
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

    await publish_task_event("podcast", podcast.id, podcast.status)
    generate_podcast_task.delay(podcast.id, body.source_ids)
    return PodcastResponse.model_validate(podcast)


@router.get(
    "/api/notebooks/{notebook_id}/podcasts",
    response_model=list[PodcastResponse],
)
async def list_podcasts(
    notebook_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _verify_notebook_access(db, notebook_id, user.id)
    result = await db.execute(
        select(PodcastOverview)
        .where(PodcastOverview.notebook_id == notebook_id)
        .order_by(PodcastOverview.created_at.desc())
    )
    rows = result.scalars().all()
    if reconcile_stale_generations(rows):
        await db.flush()
    return [PodcastResponse.model_validate(p) for p in rows]


@router.get(
    "/api/podcasts/{podcast_id}",
    response_model=PodcastResponse,
)
async def get_podcast(
    podcast_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    podcast = await _get_podcast(db, podcast_id, user.id)
    if reconcile_stale_generation(podcast):
        await db.flush()
    return PodcastResponse.model_validate(podcast)


@router.get("/api/podcasts/{podcast_id}/audio-url")
async def get_podcast_audio_url(
    podcast_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    podcast = await _get_podcast(db, podcast_id, user.id)
    if not podcast.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio not available for this podcast",
        )
    url = generate_presigned_url(podcast.file_path, expiration=3600)
    return {"url": url}


@router.get("/api/podcasts/{podcast_id}/audio")
async def get_podcast_audio(
    podcast_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Stream WAV through the API (same-origin playback, avoids storage CORS)."""
    podcast = await _get_podcast(db, podcast_id, user.id)
    if not podcast.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio not available for this podcast",
        )
    try:
        audio_bytes = await asyncio.to_thread(
            download_file_from_obs,
            podcast.file_path,
        )
    except RuntimeError as exc:
        logger.exception("Podcast audio download failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to load podcast audio from storage",
        ) from exc
    display_base = (
        podcast.suggested_filename or podcast.title or "podcast"
    ).replace('"', "")
    if not display_base.lower().endswith(".wav"):
        display_base = f"{display_base}.wav"
    ascii_name = "podcast.wav"
    utf8_quoted = quote(display_base, safe="")
    content_disposition = (
        f'inline; filename="{ascii_name}"; filename*=UTF-8\'\'{utf8_quoted}'
    )
    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={
            "Content-Disposition": content_disposition,
            "Cache-Control": "private, max-age=300",
        },
    )


@router.delete("/api/podcasts/{podcast_id}", status_code=204)
async def delete_podcast(
    podcast_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a podcast overview and its audio file from object storage."""
    podcast = await _get_podcast(db, podcast_id, user.id)
    delete_studio_objects_best_effort([podcast.file_path])
    await db.delete(podcast)
