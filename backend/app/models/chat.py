"""Chat session and message database models."""

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin, UUIDMixin


class ChatSession(Base, UUIDMixin, TimestampMixin):
    """A conversation session within a notebook."""

    __tablename__ = "chat_sessions"

    notebook_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("notebooks.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(
        String(255), default="New Chat", nullable=False
    )
    settings: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    notebook = relationship("Notebook", back_populates="chat_sessions")
    messages = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base, UUIDMixin, TimestampMixin):
    """A single message in a chat session."""

    __tablename__ = "messages"

    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chat_sessions.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")
