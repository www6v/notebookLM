"""OpenAPI file-upload helpers (IMA-aligned create_media / confirm flow)."""

from __future__ import annotations

import time
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.sources import ALLOWED_EXTENSIONS, FILE_TYPE_MAP
from app.limits import ROLE_LIMITS
from app.open_api.errors import FORBIDDEN, OpenApiBizError, PARAM_ERROR, SERVICE_ERROR
from app.services.infra.obs_storage import (
    _cos_configured,
    build_upload_object_key,
    cos_bucket_region,
    cos_object_exists,
    generate_presigned_put_url,
    get_file_url,
)
from app.services.source.source_service import (
    PDF_SOURCE_PENDING_PLACEHOLDER,
    verify_notebook_access,
)
from notebooklm_shared.config import settings
from notebooklm_shared.models.source import Source
from notebooklm_shared.models.user import User


@dataclass(frozen=True)
class ParsedUploadFile:
    """Validated upload metadata from create_media."""

    file_name: str
    file_ext: str
    file_size: int
    content_type: str
    source_type: str


def parse_upload_file(
    file_name: str,
    file_size: int,
    content_type: str,
    file_ext: str,
) -> ParsedUploadFile:
    """Validate file metadata for OpenAPI uploads."""
    name = (file_name or "").strip()
    if not name:
        raise OpenApiBizError(PARAM_ERROR, "file_name 不能为空")
    if file_size <= 0:
        raise OpenApiBizError(PARAM_ERROR, "file_size 必须大于 0")

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if file_size > max_bytes:
        raise OpenApiBizError(
            PARAM_ERROR,
            f"文件大小超过限制（{settings.max_upload_size_mb} MB）",
        )

    ext = (file_ext or "").strip().lower().lstrip(".")
    if not ext and "." in name:
        ext = name.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise OpenApiBizError(
            PARAM_ERROR,
            f"不支持的文件类型 .{ext or '?'}，"
            f"允许：{', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    mime = (content_type or "application/octet-stream").strip()
    source_type = FILE_TYPE_MAP.get(ext, "txt")
    return ParsedUploadFile(
        file_name=name,
        file_ext=ext,
        file_size=file_size,
        content_type=mime,
        source_type=source_type,
    )


async def assert_source_quota(
    db: AsyncSession,
    notebook_id: str,
    user: User,
) -> None:
    """Enforce per-notebook source count for OpenAPI uploads."""
    limits = ROLE_LIMITS.get(user.role, ROLE_LIMITS["free"])
    count_result = await db.execute(
        select(func.count(Source.id)).where(
            Source.notebook_id == notebook_id
        )
    )
    if count_result.scalar_one() >= limits["max_sources_per_notebook"]:
        raise OpenApiBizError(
            FORBIDDEN,
            f"该笔记本已达到资源数量上限（{limits['max_sources_per_notebook']}）",
        )


def require_cos_for_upload() -> None:
    if not _cos_configured():
        raise OpenApiBizError(
            SERVICE_ERROR,
            "对象存储（COS）未配置，无法上传文件。请配置 config.yaml 中的 cos 段。",
        )


def build_cos_credential(
    object_key: str,
    content_type: str,
    expiration_seconds: int = 3600,
) -> dict:
    """Build COS upload credential payload (IMA-compatible field names)."""
    now = int(time.time())
    expired = now + expiration_seconds
    bucket, region = cos_bucket_region()
    presigned_put_url = generate_presigned_put_url(
        object_key,
        content_type,
        expiration=expiration_seconds,
    )
    return {
        "token": "",
        "secret_id": "",
        "secret_key": "",
        "presigned_put_url": presigned_put_url,
        "appid": "",
        "bucket_name": bucket,
        "region": region,
        "custom_domain": "",
        "cos_key": object_key,
        "start_time": now,
        "expired_time": expired,
    }


def initial_raw_content(source_type: str) -> str | None:
    if source_type == "pdf":
        return PDF_SOURCE_PENDING_PLACEHOLDER
    if source_type in ("txt", "markdown", "docx", "csv", "pptx", "image"):
        return ""
    return None


async def check_title_repeated(
    db: AsyncSession,
    notebook_id: str,
    names: list[str],
) -> list[dict]:
    """Return is_repeated per file name (title match in notebook)."""
    results = []
    for name in names:
        trimmed = (name or "").strip()
        if not trimmed:
            results.append({"name": name, "is_repeated": False})
            continue
        count_result = await db.execute(
            select(func.count(Source.id)).where(
                Source.notebook_id == notebook_id,
                Source.title == trimmed,
            )
        )
        repeated = count_result.scalar_one() > 0
        results.append({"name": trimmed, "is_repeated": repeated})
    return results


async def get_owned_pending_source(
    db: AsyncSession,
    source_id: str,
    notebook_id: str,
    user_id: str,
) -> Source:
    await verify_notebook_access(db, notebook_id, user_id)
    result = await db.execute(
        select(Source).where(
            Source.id == source_id,
            Source.notebook_id == notebook_id,
        )
    )
    source = result.scalar_one_or_none()
    if source is None:
        from app.open_api.errors import NOT_FOUND

        raise OpenApiBizError(NOT_FOUND, "资料不存在")
    if not source.file_path:
        raise OpenApiBizError(
            PARAM_ERROR,
            "该资料不是 OpenAPI 文件上传流程创建的条目",
        )
    return source


def verify_cos_object_uploaded(cos_key: str) -> None:
    """Ensure object exists in COS before confirming upload."""
    key = (cos_key or "").strip().lstrip("/")
    if not key:
        raise OpenApiBizError(PARAM_ERROR, "cos_key 不能为空")
    if not cos_object_exists(key):
        raise OpenApiBizError(
            PARAM_ERROR,
            "COS 上未找到已上传的文件，请先完成 COS 上传再确认",
        )
