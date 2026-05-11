"""User subscription to another user's discoverable notebook."""

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from notebooklm_shared.database import Base, TimestampMixin, UUIDMixin


class NotebookSubscription(Base, UUIDMixin, TimestampMixin):
    """Maps a subscriber user to a notebook they follow."""

    __tablename__ = "notebook_subscriptions"
    __table_args__ = (
        UniqueConstraint(
            "subscriber_user_id",
            "notebook_id",
            name="uq_sub_notebook",
        ),
    )

    subscriber_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    notebook_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("notebooks.id", ondelete="CASCADE"),
        nullable=False,
    )

    subscriber = relationship(
        "User",
        foreign_keys=[subscriber_user_id],
    )
    notebook = relationship(
        "Notebook",
        foreign_keys=[notebook_id],
    )
