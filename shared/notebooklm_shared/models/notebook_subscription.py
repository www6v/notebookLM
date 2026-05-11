"""User subscription to another user's discoverable notebook."""

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from notebooklm_shared.database import Base, TimestampMixin, UUIDMixin


class NotebookSubscription(Base, UUIDMixin, TimestampMixin):
    """Maps a subscriber user to a notebook they follow.

    Intentionally no DB-level foreign keys (MySQL charset/collation parity;
    referential integrity is enforced in application code).
    """

    __tablename__ = "notebook_subscriptions"
    __table_args__ = (
        UniqueConstraint(
            "subscriber_user_id",
            "notebook_id",
            name="uq_sub_notebook",
        ),
    )

    subscriber_user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    notebook_id: Mapped[str] = mapped_column(String(36), nullable=False)

    subscriber = relationship(
        "User",
        primaryjoin="NotebookSubscription.subscriber_user_id == User.id",
        foreign_keys=[subscriber_user_id],
    )
    notebook = relationship(
        "Notebook",
        back_populates="subscriptions",
        primaryjoin="NotebookSubscription.notebook_id == Notebook.id",
        foreign_keys=[notebook_id],
    )
