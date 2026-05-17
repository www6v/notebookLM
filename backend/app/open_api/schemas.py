"""Pydantic schemas for OpenAPI key management and agent routes."""

from datetime import datetime

from pydantic import BaseModel, Field


class OpenApiCredentialView(BaseModel):
    """Credential metadata exposed to the agent-interface UI."""

    client_id: str
    status: str
    expires_at: datetime
    has_api_key: bool = True


class OpenApiCredentialCreateResponse(BaseModel):
    """Returned once when a credential is created or regenerated."""

    client_id: str
    api_key: str
    status: str
    expires_at: datetime


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
