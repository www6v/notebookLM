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
