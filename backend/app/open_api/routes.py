"""OpenAPI POST endpoints for notebooks, sources, and notes."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.limits import ROLE_LIMITS
from app.open_api.deps import get_open_api_user
from app.open_api.errors import (
    FORBIDDEN,
    NOT_FOUND,
    OpenApiBizError,
    PARAM_ERROR,
    success,
)
from app.open_api.schemas import (
    CheckRepeatedNamesBody,
    ConfirmSourceUploadBody,
    CreateMediaBody,
    NoteAppendBody,
    NoteCreateBody,
    NoteIdBody,
    NoteListBody,
    NoteUpdateBody,
    NotebookCreateBody,
    NotebookIdBody,
    NotebookUpdateBody,
    SkillUpdateCheckBody,
    SourceAddBody,
    SourceIdBody,
    SourceListBody,
)
from app.open_api.source_upload import (
    assert_source_quota,
    build_cos_credential,
    check_title_repeated,
    get_owned_pending_source,
    initial_raw_content,
    parse_upload_file,
    require_cos_for_upload,
    verify_cos_object_uploaded,
)
from app.services.infra.obs_storage import build_upload_object_key, get_file_url
from app.commons.url_validation import validate_web_source_url
from app.services.source.source_service import verify_notebook_access
from app.tasks.source_tasks import process_source_task
from notebooklm_shared.database import get_db
from notebooklm_shared.models.note import Note
from notebooklm_shared.models.notebook import Notebook
from notebooklm_shared.models.source import Source, SourceChunk
from notebooklm_shared.models.user import User
from app.services.task_event_service import publish_task_event

router = APIRouter(prefix="/openapi/notebook/v1", tags=["open-api"])

LATEST_SKILL_VERSION = "1.1.0"


@router.post("/check_skill_update")
async def check_skill_update(body: SkillUpdateCheckBody):
    """Skill version check for OpenClaw auto-update."""
    current = (body.version or "").strip()
    latest = LATEST_SKILL_VERSION
    if current and current != latest:
        return success(
            {
                "latest_version": latest,
                "release_desc": "NotebookLM OpenClaw skill",
                "instruction": (
                    "请从 NotebookLM 控制台重新下载并安装最新版 "
                    "notebooklm-skills 压缩包，然后重启 OpenClaw。"
                ),
            }
        )
    return success(
        {
            "latest_version": latest,
            "release_desc": "",
            "instruction": "",
        }
    )


@router.post("/list_notebooks")
async def list_notebooks(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_open_api_user),
):
    """List notebooks owned by the credential user."""
    source_count_sub = (
        select(
            Source.notebook_id,
            func.count(Source.id).label("source_count"),
        )
        .group_by(Source.notebook_id)
        .subquery()
    )
    result = await db.execute(
        select(Notebook, func.coalesce(source_count_sub.c.source_count, 0))
        .outerjoin(
            source_count_sub,
            Notebook.id == source_count_sub.c.notebook_id,
        )
        .where(Notebook.user_id == user.id)
        .order_by(Notebook.updated_at.desc())
    )
    items = []
    for nb, count in result.all():
        items.append(
            {
                "id": nb.id,
                "title": nb.title,
                "description": nb.description,
                "source_count": int(count),
                "created_at": nb.created_at.isoformat(),
                "updated_at": nb.updated_at.isoformat(),
            }
        )
    return success({"notebooks": items, "total": len(items)})


@router.post("/get_notebook")
async def get_notebook(
    body: NotebookIdBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_open_api_user),
):
    nb = await _get_notebook(db, body.notebook_id, user.id)
    count_result = await db.execute(
        select(func.count(Source.id)).where(Source.notebook_id == nb.id)
    )
    return success(
        {
            "id": nb.id,
            "title": nb.title,
            "description": nb.description,
            "source_count": count_result.scalar_one(),
            "created_at": nb.created_at.isoformat(),
            "updated_at": nb.updated_at.isoformat(),
        }
    )


@router.post("/create_notebook")
async def create_notebook(
    body: NotebookCreateBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_open_api_user),
):
    if not body.title.strip():
        raise OpenApiBizError(PARAM_ERROR, "title 不能为空")
    limits = ROLE_LIMITS.get(user.role, ROLE_LIMITS["free"])
    count_result = await db.execute(
        select(func.count(Notebook.id)).where(Notebook.user_id == user.id)
    )
    if count_result.scalar_one() >= limits["max_notebooks"]:
        raise OpenApiBizError(
            FORBIDDEN,
            f"已达到笔记本数量上限（{limits['max_notebooks']}）",
        )
    notebook = Notebook(
        user_id=user.id,
        title=body.title.strip(),
        description=body.description or "",
    )
    db.add(notebook)
    await db.flush()
    await db.refresh(notebook)
    return success({"notebook_id": notebook.id})


@router.post("/update_notebook")
async def update_notebook(
    body: NotebookUpdateBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_open_api_user),
):
    nb = await _get_notebook(db, body.notebook_id, user.id)
    if body.title is not None:
        nb.title = body.title
    if body.description is not None:
        nb.description = body.description
    await db.flush()
    return success({"notebook_id": nb.id})


@router.post("/delete_notebook")
async def delete_notebook(
    body: NotebookIdBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_open_api_user),
):
    nb = await _get_notebook(db, body.notebook_id, user.id)
    await db.delete(nb)
    return success({"notebook_id": body.notebook_id})


@router.post("/list_sources")
async def list_sources(
    body: SourceListBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_open_api_user),
):
    await verify_notebook_access(db, body.notebook_id, user.id)
    result = await db.execute(
        select(Source)
        .where(Source.notebook_id == body.notebook_id)
        .order_by(Source.created_at.desc())
    )
    sources = []
    for s in result.scalars().all():
        sources.append(
            {
                "id": s.id,
                "notebook_id": s.notebook_id,
                "title": s.title,
                "type": s.type,
                "status": s.status,
                "original_url": s.original_url,
                "is_active": s.is_active,
                "created_at": s.created_at.isoformat(),
            }
        )
    return success({"sources": sources})


@router.post("/get_source_content")
async def get_source_content(
    body: SourceIdBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_open_api_user),
):
    from app.services.source.source_service import get_source

    source = await get_source(db, body.source_id, user.id)
    chunk_count_result = await db.execute(
        select(func.count(SourceChunk.id)).where(
            SourceChunk.source_id == source.id
        )
    )
    return success(
        {
            "id": source.id,
            "title": source.title,
            "type": source.type,
            "summary": source.summary,
            "raw_content": source.raw_content,
            "chunk_count": chunk_count_result.scalar_one(),
        }
    )


@router.post("/check_repeated_names")
async def check_repeated_names(
    body: CheckRepeatedNamesBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_open_api_user),
):
    """Check duplicate source titles in a notebook (IMA-aligned)."""
    await verify_notebook_access(db, body.notebook_id, user.id)
    names = [p.name for p in body.params]
    results = await check_title_repeated(db, body.notebook_id, names)
    return success({"results": results})


@router.post("/create_media")
async def create_media(
    body: CreateMediaBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_open_api_user),
):
    """Reserve a source and return COS upload credentials (presigned PUT)."""
    await verify_notebook_access(db, body.notebook_id, user.id)
    require_cos_for_upload()
    await assert_source_quota(db, body.notebook_id, user)

    parsed = parse_upload_file(
        body.file_name,
        body.file_size,
        body.content_type,
        body.file_ext,
    )
    object_key = build_upload_object_key(parsed.file_name)
    cos_credential = build_cos_credential(object_key, parsed.content_type)

    source = Source(
        notebook_id=body.notebook_id,
        title=parsed.file_name,
        type=parsed.source_type,
        file_path=object_key,
        file_size_bytes=parsed.file_size,
        original_url="",
        raw_content=initial_raw_content(parsed.source_type),
        status="pending",
    )
    db.add(source)
    await db.flush()
    await db.refresh(source)
    await db.commit()

    return success(
        {
            "media_id": source.id,
            "source_id": source.id,
            "url": get_file_url(object_key),
            "cos_credential": cos_credential,
        }
    )


@router.post("/confirm_source_upload")
async def confirm_source_upload(
    body: ConfirmSourceUploadBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_open_api_user),
):
    """Finalize OpenAPI file upload after COS PUT (IMA add_knowledge equivalent)."""
    source = await get_owned_pending_source(
        db, body.source_id, body.notebook_id, user.id
    )
    file_name = (body.file_info.file_name or "").strip()
    title = (body.title or "").strip()
    if not file_name:
        raise OpenApiBizError(PARAM_ERROR, "file_info.file_name 不能为空")
    if title != file_name:
        raise OpenApiBizError(
            PARAM_ERROR,
            "title 必须与 file_name（含扩展名）一致",
        )
    cos_key = (body.file_info.cos_key or "").strip()
    if cos_key != source.file_path:
        raise OpenApiBizError(PARAM_ERROR, "cos_key 与 create_media 返回不一致")
    verify_cos_object_uploaded(cos_key)

    source.title = title
    source.file_size_bytes = body.file_info.file_size
    source.original_url = get_file_url(cos_key)
    await db.flush()
    await db.commit()
    await db.refresh(source)

    if source.type in ("video", "image", "audio", "pdf") or (
        source.raw_content and str(source.raw_content).strip()
    ):
        await publish_task_event("source", source.id, source.status)
        process_source_task.delay(source.id)

    return success({"source_id": source.id, "media_id": source.id})


@router.post("/add_source")
async def add_source(
    body: SourceAddBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_open_api_user),
):
    await verify_notebook_access(db, body.notebook_id, user.id)
    if body.type == "web":
        if not (body.url and body.url.strip()):
            raise OpenApiBizError(PARAM_ERROR, "网页来源需要有效的 URL")
        try:
            validate_web_source_url(body.url)
        except ValueError as exc:
            raise OpenApiBizError(PARAM_ERROR, str(exc)) from exc

    limits = ROLE_LIMITS.get(user.role, ROLE_LIMITS["free"])
    count_result = await db.execute(
        select(func.count(Source.id)).where(
            Source.notebook_id == body.notebook_id
        )
    )
    if count_result.scalar_one() >= limits["max_sources_per_notebook"]:
        raise OpenApiBizError(
            FORBIDDEN,
            f"该笔记本已达到资源数量上限（{limits['max_sources_per_notebook']}）",
        )

    source = Source(
        notebook_id=body.notebook_id,
        title=body.title or body.url or "Untitled Source",
        type=body.type,
        original_url=body.url,
        status="pending",
    )
    db.add(source)
    await db.flush()
    await db.refresh(source)
    await db.commit()
    await db.refresh(source)

    if source.type in ("web", "youtube", "bilibili") and source.original_url:
        await publish_task_event("source", source.id, source.status)
        process_source_task.delay(source.id)

    return success({"source_id": source.id})


@router.post("/list_notes")
async def list_notes(
    body: NoteListBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_open_api_user),
):
    await verify_notebook_access(db, body.notebook_id, user.id)
    result = await db.execute(
        select(Note)
        .where(Note.notebook_id == body.notebook_id)
        .order_by(Note.is_pinned.desc(), Note.updated_at.desc())
    )
    notes = []
    for n in result.scalars().all():
        notes.append(
            {
                "id": n.id,
                "notebook_id": n.notebook_id,
                "title": n.title,
                "is_pinned": n.is_pinned,
                "created_at": n.created_at.isoformat(),
                "updated_at": n.updated_at.isoformat(),
            }
        )
    return success({"notes": notes})


@router.post("/get_note_content")
async def get_note_content(
    body: NoteIdBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_open_api_user),
):
    note = await _get_note(db, body.note_id, user.id)
    return success(
        {
            "note_id": note.id,
            "notebook_id": note.notebook_id,
            "title": note.title,
            "content": note.content,
        }
    )


@router.post("/create_note")
async def create_note(
    body: NoteCreateBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_open_api_user),
):
    await verify_notebook_access(db, body.notebook_id, user.id)
    note = Note(
        notebook_id=body.notebook_id,
        title=body.title,
        content=body.content,
    )
    db.add(note)
    await db.flush()
    await db.refresh(note)
    return success({"note_id": note.id})


@router.post("/update_note")
async def update_note(
    body: NoteUpdateBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_open_api_user),
):
    note = await _get_note(db, body.note_id, user.id)
    if body.title is not None:
        note.title = body.title
    if body.content is not None:
        note.content = body.content
    await db.flush()
    return success({"note_id": note.id})


@router.post("/append_note")
async def append_note(
    body: NoteAppendBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_open_api_user),
):
    if not body.content:
        raise OpenApiBizError(PARAM_ERROR, "content 不能为空")
    note = await _get_note(db, body.note_id, user.id)
    note.content = (note.content or "") + body.content
    await db.flush()
    return success({"note_id": note.id})


async def _get_notebook(
    db: AsyncSession, notebook_id: str, user_id: str
) -> Notebook:
    result = await db.execute(
        select(Notebook).where(
            Notebook.id == notebook_id, Notebook.user_id == user_id
        )
    )
    nb = result.scalar_one_or_none()
    if nb is None:
        raise OpenApiBizError(NOT_FOUND, "笔记本不存在")
    return nb


async def _get_note(db: AsyncSession, note_id: str, user_id: str) -> Note:
    result = await db.execute(
        select(Note)
        .join(Notebook, Note.notebook_id == Notebook.id)
        .where(Note.id == note_id, Notebook.user_id == user_id)
    )
    note = result.scalar_one_or_none()
    if note is None:
        raise OpenApiBizError(NOT_FOUND, "笔记不存在")
    return note
