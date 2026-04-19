"""Admin API routes for user management."""

from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.database import get_db
from app.models.notebook import Notebook
from app.models.source import Source
from app.models.studio import (
    Infographic,
    MindMap,
    PodcastOverview,
    Report,
    SlideDeck,
)
from app.models.user import User
from app.schemas.client_config import (
    AdminClientConfigUpdate,
    PublicClientConfigResponse,
)
from app.schemas.user import (
    AdminUserDetailResponse,
    AdminUserListResponse,
    AdminUserUpdateRequest,
    NotebookStatsItem,
    UploadedFileTypeStat,
    UserResponse,
)
from app.services import system_setting_service as sys_svc

router = APIRouter(prefix="/api/admin", tags=["admin"])

VALID_ROLES = {"free", "paid", "admin"}


def _normalize_desktop_backend_url(raw: str) -> str:
    """Validate and trim trailing slash from an origin URL."""
    t = raw.strip()
    if not t:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL must not be empty",
        )
    parsed = urlparse(t)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only http and https URLs are allowed",
        )
    if not parsed.netloc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL must include host",
        )
    return t.rstrip("/")


async def _count_studio_ready_error(
    db: AsyncSession,
    model: type,
    notebook_id: str,
) -> tuple[int, int]:
    """Return (success_count, failed_count) for status ready vs error."""
    ready_case = case((model.status == "ready", 1), else_=0)
    error_case = case((model.status == "error", 1), else_=0)
    row = (
        await db.execute(
            select(
                func.coalesce(func.sum(ready_case), 0),
                func.coalesce(func.sum(error_case), 0),
            ).where(model.notebook_id == notebook_id)
        )
    ).one()
    return int(row[0]), int(row[1])


@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query("", description="Search by email or username"),
    role: str = Query("", description="Filter by role"),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """List all users with pagination, search, and role filter."""
    base_filter = select(User)
    count_filter = select(func.count(User.id))

    if search:
        like_pattern = f"%{search}%"
        condition = or_(
            User.email.ilike(like_pattern),
            User.username.ilike(like_pattern),
        )
        base_filter = base_filter.where(condition)
        count_filter = count_filter.where(condition)

    if role and role in VALID_ROLES:
        base_filter = base_filter.where(User.role == role)
        count_filter = count_filter.where(User.role == role)

    total_result = await db.execute(count_filter)
    total = total_result.scalar_one()

    offset = (page - 1) * page_size
    query = (
        base_filter
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    users = [UserResponse.model_validate(u) for u in result.scalars().all()]

    return AdminUserListResponse(
        users=users,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/users/{user_id}", response_model=AdminUserDetailResponse)
async def get_user_detail(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """Get detailed user info including per-notebook statistics."""
    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    notebooks_result = await db.execute(
        select(Notebook)
        .where(Notebook.user_id == user_id)
        .order_by(Notebook.created_at.desc())
    )
    notebooks = notebooks_result.scalars().all()

    notebook_stats: list[NotebookStatsItem] = []
    for nb in notebooks:
        nb_id = nb.id
        source_cnt = (
            await db.execute(
                select(func.count(Source.id)).where(
                    Source.notebook_id == nb_id
                )
            )
        ).scalar_one()
        mindmap_ok, mindmap_fail = await _count_studio_ready_error(
            db, MindMap, nb_id
        )
        slide_ok, slide_fail = await _count_studio_ready_error(
            db, SlideDeck, nb_id
        )
        infographic_ok, infographic_fail = await _count_studio_ready_error(
            db, Infographic, nb_id
        )
        report_ok, report_fail = await _count_studio_ready_error(
            db, Report, nb_id
        )
        podcast_ok, podcast_fail = await _count_studio_ready_error(
            db, PodcastOverview, nb_id
        )

        cnt_label = func.count(Source.id).label("upload_cnt")
        size_label = func.coalesce(
            func.sum(Source.file_size_bytes), 0
        ).label("upload_size")
        upload_rows = (
            await db.execute(
                select(Source.type, cnt_label, size_label)
                .where(
                    Source.notebook_id == nb_id,
                    Source.file_path.is_not(None),
                )
                .group_by(Source.type)
                .order_by(size_label.desc(), Source.type)
            )
        ).all()

        uploaded_stats: list[UploadedFileTypeStat] = []
        upload_total_count = 0
        upload_total_bytes = 0
        for row in upload_rows:
            stype, ucnt, usize = row[0], int(row[1]), int(row[2])
            uploaded_stats.append(
                UploadedFileTypeStat(
                    source_type=stype,
                    count=ucnt,
                    size_bytes=usize,
                )
            )
            upload_total_count += ucnt
            upload_total_bytes += usize

        notebook_stats.append(
            NotebookStatsItem(
                id=nb.id,
                title=nb.title,
                source_count=source_cnt,
                mind_map_success_count=mindmap_ok,
                mind_map_failed_count=mindmap_fail,
                slide_deck_success_count=slide_ok,
                slide_deck_failed_count=slide_fail,
                infographic_success_count=infographic_ok,
                infographic_failed_count=infographic_fail,
                report_success_count=report_ok,
                report_failed_count=report_fail,
                podcast_overview_success_count=podcast_ok,
                podcast_overview_failed_count=podcast_fail,
                created_at=nb.created_at,
                uploaded_file_stats=uploaded_stats,
                uploaded_file_total_count=upload_total_count,
                uploaded_file_total_bytes=upload_total_bytes,
            )
        )

    return AdminUserDetailResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        notebook_count=len(notebooks),
        notebooks=notebook_stats,
    )


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    body: AdminUserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Update a user's role or active status."""
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own admin account",
        )

    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if body.role is not None:
        if body.role not in VALID_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {', '.join(sorted(VALID_ROLES))}",
            )
        user.role = body.role

    if body.is_active is not None:
        user.is_active = body.is_active

    await db.flush()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.put(
    "/client-config",
    response_model=PublicClientConfigResponse,
)
async def put_client_config(
    body: AdminClientConfigUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """Set fleet-wide desktop API origin (all desktop clients read via public)."""
    normalized = _normalize_desktop_backend_url(body.desktop_backend_url)
    await sys_svc.set_value(db, sys_svc.DESKTOP_BACKEND_URL_KEY, normalized)
    await db.flush()
    return PublicClientConfigResponse(desktop_backend_url=normalized)
