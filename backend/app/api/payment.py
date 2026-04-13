"""Payment API routes for subscription management."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings as config
from app.database import async_session, get_db
from app.models.payment import PaymentOrder
from app.models.user import User
from app.schemas.payment import (
    CreateOrderRequest,
    CreateOrderResponse,
    OrderStatusResponse,
)
from app.services.payment_service import (
    activate_subscription,
    create_alipay_order,
    create_wechat_order,
    verify_alipay_callback,
    verify_wechat_callback,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payment", tags=["payment"])


@router.post("/create", response_model=CreateOrderResponse)
async def create_order(
    body: CreateOrderRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a payment order and return a QR code URL."""
    if body.duration_months < 1 or body.duration_months > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="订阅时长需在 1-12 个月之间",
        )

    amount = config.subscription_price_monthly * body.duration_months

    if body.pay_channel == "alipay":
        result = await create_alipay_order(
            db, user, amount, body.duration_months
        )
    else:
        result = await create_wechat_order(
            db, user, amount, body.duration_months
        )

    return CreateOrderResponse(**result)


@router.get("/status/{order_id}", response_model=OrderStatusResponse)
async def get_order_status(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Query the status of a payment order."""
    result = await db.execute(
        select(PaymentOrder).where(
            PaymentOrder.id == order_id,
            PaymentOrder.user_id == str(user.id),
        )
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在",
        )
    return OrderStatusResponse(
        order_id=str(order.id),
        status=order.status,
        pay_channel=order.pay_channel,
        amount=order.amount,
        paid_at=order.paid_at,
        created_at=order.created_at,
    )


@router.post("/callback/alipay")
async def alipay_callback(request: Request):
    """Handle Alipay asynchronous payment notification."""
    form_data = await request.form()
    params = dict(form_data)

    if not verify_alipay_callback(params):
        logger.warning("Alipay callback signature verification failed")
        return PlainTextResponse("fail")

    out_trade_no = params.get("out_trade_no", "")
    trade_status = params.get("trade_status", "")
    trade_no = params.get("trade_no", "")

    if trade_status not in ("TRADE_SUCCESS", "TRADE_FINISHED"):
        return PlainTextResponse("success")

    async with async_session() as db:
        try:
            result = await db.execute(
                select(PaymentOrder).where(
                    PaymentOrder.out_trade_no == out_trade_no
                )
            )
            order = result.scalar_one_or_none()
            if order is None:
                logger.warning("Alipay callback: order %s not found", out_trade_no)
                return PlainTextResponse("fail")

            if order.status == "paid":
                return PlainTextResponse("success")

            await activate_subscription(db, order, trade_no)
            await db.commit()
        except Exception:
            await db.rollback()
            raise

    return PlainTextResponse("success")


@router.post("/callback/wechat")
async def wechat_callback(request: Request):
    """Handle WeChat Pay V3 asynchronous payment notification."""
    headers = dict(request.headers)
    body = await request.body()

    result = verify_wechat_callback(headers, body)
    if result is None:
        logger.warning("WeChat callback verification failed")
        return {"code": "FAIL", "message": "签名验证失败"}

    out_trade_no = result.get("out_trade_no", "")
    trade_state = result.get("trade_state", "")
    transaction_id = result.get("transaction_id", "")

    if trade_state != "SUCCESS":
        return {"code": "SUCCESS", "message": "OK"}

    async with async_session() as db:
        try:
            query_result = await db.execute(
                select(PaymentOrder).where(
                    PaymentOrder.out_trade_no == out_trade_no
                )
            )
            order = query_result.scalar_one_or_none()
            if order is None:
                logger.warning("WeChat callback: order %s not found", out_trade_no)
                return {"code": "FAIL", "message": "订单不存在"}

            if order.status == "paid":
                return {"code": "SUCCESS", "message": "OK"}

            await activate_subscription(db, order, transaction_id)
            await db.commit()
        except Exception:
            await db.rollback()
            raise

    return {"code": "SUCCESS", "message": "OK"}
