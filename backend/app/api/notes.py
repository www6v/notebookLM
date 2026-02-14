"""Notes API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.notebook import Notebook
from app.models.note import Note
from app.models.user import User
from app.schemas.note import NoteCreate, NoteResponse, NoteUpdate

router = APIRouter(tags=["notes"])


@router.post(
    "/api/notebooks/{notebook_id}/notes",
    response_model=NoteResponse,
    status_code=201,
)
async def create_note(
    notebook_id: str,
    body: NoteCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new note in a notebook."""
    await _verify_notebook_access(db, notebook_id, user.id)
    note = Note(
        notebook_id=notebook_id,
        title=body.title,
        content=body.content,
        is_pinned=body.is_pinned,
    )
    db.add(note)
    await db.flush()
    await db.refresh(note)
    return NoteResponse.model_validate(note)


@router.get(
    "/api/notebooks/{notebook_id}/notes",
    response_model=list[NoteResponse],
)
async def list_notes(
    notebook_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all notes in a notebook."""
    await _verify_notebook_access(db, notebook_id, user.id)
    result = await db.execute(
        select(Note)
        .where(Note.notebook_id == notebook_id)
        .order_by(Note.is_pinned.desc(), Note.updated_at.desc())
    )
    return [NoteResponse.model_validate(n) for n in result.scalars().all()]


@router.put("/api/notes/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: str,
    body: NoteUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update a note."""
    note = await _get_note(db, note_id, user.id)
    if body.title is not None:
        note.title = body.title
    if body.content is not None:
        note.content = body.content
    if body.is_pinned is not None:
        note.is_pinned = body.is_pinned
    await db.flush()
    await db.refresh(note)
    return NoteResponse.model_validate(note)


@router.delete("/api/notes/{note_id}", status_code=204)
async def delete_note(
    note_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a note."""
    note = await _get_note(db, note_id, user.id)
    await db.delete(note)


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


async def _get_note(
    db: AsyncSession, note_id: str, user_id: str
) -> Note:
    """Get a note and verify user access through its notebook."""
    result = await db.execute(
        select(Note)
        .join(Notebook, Note.notebook_id == Notebook.id)
        .where(Note.id == note_id, Notebook.user_id == user_id)
    )
    note = result.scalar_one_or_none()
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )
    return note
