"""Pydantic schemas for OpenAPI key management and agent routes."""

from datetime import datetime

from pydantic import BaseModel, Field


class OpenApiCredentialStatusResponse(BaseModel):
    """Agent-interface credential state (图2 空态 / 图3 已生成)."""

    has_credential: bool
    client_id: str | None = None
    status: str | None = None
    status_label: str | None = None
    expires_at: datetime | None = None


class OpenApiCredentialRevealResponse(BaseModel):
    """Shown once in modal after create or regenerate (图1)."""

    client_id: str
    api_key: str
    status: str
    status_label: str
    expires_at: datetime
    reveal_once: bool = True


class OpenApiCredentialDeleteResponse(BaseModel):
    """After delete confirmation (图4 -> 回到图2)."""

    has_credential: bool = False


class OpenApiEnvelope(BaseModel):
    """Standard OpenAPI response wrapper."""

    code: int
    msg: str
    data: dict = Field(default_factory=dict)


class NotebookIdBody(BaseModel):
    notebook_id: str


class NotebookCreateBody(BaseModel):
    title: str
    description: str = ""


class NotebookUpdateBody(BaseModel):
    notebook_id: str
    title: str | None = None
    description: str | None = None


class SourceListBody(BaseModel):
    notebook_id: str


class SourceIdBody(BaseModel):
    source_id: str


class SourceAddBody(BaseModel):
    notebook_id: str
    type: str
    url: str | None = None
    title: str = ""


class NoteListBody(BaseModel):
    notebook_id: str


class NoteIdBody(BaseModel):
    note_id: str


class NoteCreateBody(BaseModel):
    notebook_id: str
    title: str = "Untitled Note"
    content: str = ""


class NoteUpdateBody(BaseModel):
    note_id: str
    title: str | None = None
    content: str | None = None


class NoteAppendBody(BaseModel):
    note_id: str
    content: str


class SkillUpdateCheckBody(BaseModel):
    version: str


class CheckRepeatedNameParam(BaseModel):
    name: str


class CheckRepeatedNamesBody(BaseModel):
    notebook_id: str
    params: list[CheckRepeatedNameParam] = Field(min_length=1, max_length=2000)


class CreateMediaBody(BaseModel):
    notebook_id: str
    file_name: str
    file_size: int = Field(gt=0)
    content_type: str
    file_ext: str = ""


class SourceFileInfoBody(BaseModel):
    cos_key: str
    file_size: int = Field(gt=0)
    file_name: str


class ConfirmSourceUploadBody(BaseModel):
    notebook_id: str
    source_id: str
    title: str
    file_info: SourceFileInfoBody
