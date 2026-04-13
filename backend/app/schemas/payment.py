"""Pydantic schemas for payment and subscription."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class PayChannel(str, Enum):
    """Supported payment channels."""

    ALIPAY = "alipay"
    WECHAT = "wechat"


class CreateOrderRequest(BaseModel):
    """Request body for creating a payment order."""

    pay_channel: PayChannel
    duration_months: int = 1


class CreateOrderResponse(BaseModel):
    """Response after creating a payment order."""

    order_id: str
    out_trade_no: str
    qr_code_url: str
    amount: int
    pay_channel: str


class OrderStatusResponse(BaseModel):
    """Response for order status query."""

    order_id: str
    status: str
    pay_channel: str
    amount: int
    paid_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
