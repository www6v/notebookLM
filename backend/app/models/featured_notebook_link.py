"""Curated share links shown on the home Featured tab."""

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, TimestampMixin, UUIDMixin


class FeaturedNotebookLink(Base, UUIDMixin, TimestampMixin):
    """Ordered list of public notebook share tokens for marketing / demos."""

    __tablename__ = "featured_notebook_links"

    share_token: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    custom_title: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
