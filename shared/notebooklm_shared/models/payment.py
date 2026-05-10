"""Payment order database model."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from notebooklm_shared.database import Base, TimestampMixin, UUIDMixin


class PaymentOrder(Base, UUIDMixin, TimestampMixin):
    """A payment order for subscription upgrade."""

    __tablename__ = "payment_orders"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    out_trade_no: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    pay_channel: Mapped[str] = mapped_column(
        String(20), nullable=False
    )
    amount: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )
    plan: Mapped[str] = mapped_column(
        String(20), nullable=False, default="paid"
    )
    duration_months: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )
    trade_no: Mapped[str | None] = mapped_column(
        String(128), nullable=True
    )
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    user = relationship("User", backref="payment_orders")
