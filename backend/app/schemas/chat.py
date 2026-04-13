"""Pydantic schemas for chat sessions and messages."""

from datetime import datetime

from pydantic import BaseModel


class ChatSessionCreate(BaseModel):
    """Schema for creating a chat session."""

    title: str = "New Chat"
    settings: dict | None = None


class ChatSessionResponse(BaseModel):
    """Schema for chat session response."""

    id: str
    notebook_id: str
    title: str
    settings: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    """Schema for sending a chat message."""

    content: str
    source_ids: list[str] | None = None
    conversation_style: str | None = None
    custom_prompt: str | None = None
    answer_length: str | None = None


class CitationDetail(BaseModel):
    """Schema for a single citation reference."""

    source_id: str
    source_title: str
    chunk_id: str
    chunk_index: int
    page_number: int | None = None
    paragraph_index: int | None = None
    content: str
    highlight_text: str | None = None


class MessageResponse(BaseModel):
    """Schema for message response."""

    id: str
    session_id: str
    role: str
    content: str
    citations: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatStreamRequest(BaseModel):
    """Schema for chat stream request via WebSocket."""

    content: str
    source_ids: list[str] | None = None
    settings: dict | None = None
    conversation_style: str | None = None
    custom_prompt: str | None = None
    answer_length: str | None = None
