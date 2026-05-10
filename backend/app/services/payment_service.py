"""Payment service for Alipay and WeChat Pay integration."""

import logging
import time
import uuid
from datetime import datetime, timezone

from dateutil.relativedelta import relativedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from notebooklm_shared.config import settings
from notebooklm_shared.models.payment import PaymentOrder
from notebooklm_shared.models.user import User

logger = logging.getLogger(__name__)


def generate_out_trade_no() -> str:
    """Generate a unique merchant order number."""
    ts = int(time.time() * 1000)
    short_uuid = uuid.uuid4().hex[:8]
    return f"NLM{ts}{short_uuid}"


async def create_alipay_order(
    db: AsyncSession,
    user: User,
    amount: int,
    duration_months: int,
) -> dict:
    """Create an Alipay Native QR-code payment order.

    Uses alipay.trade.precreate to get a QR code URL.
    """
    from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
    from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient
    from alipay.aop.api.request.AlipayTradePrecreateRequest import (
        AlipayTradePrecreateRequest,
    )
    from alipay.aop.api.domain.AlipayTradePrecreateModel import (
        AlipayTradePrecreateModel,
    )

    out_trade_no = generate_out_trade_no()

    order = PaymentOrder(
        user_id=str(user.id),
        out_trade_no=out_trade_no,
        pay_channel="alipay",
        amount=amount,
        status="pending",
        plan="paid",
        duration_months=duration_months,
    )
    db.add(order)
    await db.flush()
    await db.refresh(order)

    alipay_config = AlipayClientConfig()
    settings.validate_alipay_public_key_config()
    alipay_config.server_url = settings.alipay_gateway
    alipay_config.app_id = settings.alipay_app_id
    alipay_config.app_private_key = settings.alipay_private_key
    alipay_config.alipay_public_key = settings.alipay_public_key

    client = DefaultAlipayClient(alipay_client_config=alipay_config)

    model = AlipayTradePrecreateModel()
    model.out_trade_no = out_trade_no
    model.total_amount = str(amount / 100)
    model.subject = f"NoteWorks Plus - {duration_months}个月订阅"

    request = AlipayTradePrecreateRequest(biz_model=model)
    request.notify_url = settings.alipay_notify_url

    response = client.execute(request)

    qr_code = ""
    if hasattr(response, "qr_code"):
        qr_code = response.qr_code
    elif isinstance(response, dict):
        qr_code = response.get("qr_code", "")

    return {
        "order_id": str(order.id),
        "out_trade_no": out_trade_no,
        "qr_code_url": qr_code,
        "amount": amount,
        "pay_channel": "alipay",
    }


async def create_wechat_order(
    db: AsyncSession,
    user: User,
    amount: int,
    duration_months: int,
) -> dict:
    """Create a WeChat Pay Native QR-code payment order.

    Uses the V3 API to get a code_url for QR display.
    """
    from wechatpayv3 import WeChatPay, WeChatPayType

    out_trade_no = generate_out_trade_no()

    order = PaymentOrder(
        user_id=str(user.id),
        out_trade_no=out_trade_no,
        pay_channel="wechat",
        amount=amount,
        status="pending",
        plan="paid",
        duration_months=duration_months,
    )
    db.add(order)
    await db.flush()
    await db.refresh(order)

    private_key_content = ""
    try:
        with open(settings.wechat_private_key_path, "r") as f:
            private_key_content = f.read()
    except FileNotFoundError:
        logger.warning("WeChat private key file not found: %s", settings.wechat_private_key_path)

    wxpay = WeChatPay(
        wechatpay_type=WeChatPayType.NATIVE,
        mchid=settings.wechat_mch_id,
        private_key=private_key_content,
        cert_serial_no=settings.wechat_cert_serial_no,
        appid=settings.wechat_app_id,
        apiv3_key=settings.wechat_api_key,
        notify_url=settings.wechat_notify_url,
    )

    code, result = wxpay.pay(
        description=f"NoteWorks Plus - {duration_months}个月订阅",
        out_trade_no=out_trade_no,
        amount={"total": amount, "currency": "CNY"},
    )

    qr_code_url = ""
    if code == 200 and isinstance(result, dict):
        qr_code_url = result.get("code_url", "")

    return {
        "order_id": str(order.id),
        "out_trade_no": out_trade_no,
        "qr_code_url": qr_code_url,
        "amount": amount,
        "pay_channel": "wechat",
    }


async def activate_subscription(
    db: AsyncSession,
    order: PaymentOrder,
    trade_no: str,
) -> None:
    """Mark order as paid and activate the user subscription."""
    order.status = "paid"
    order.trade_no = trade_no
    order.paid_at = datetime.now(timezone.utc)
    db.add(order)

    result = await db.execute(
        select(User).where(User.id == order.user_id)
    )
    user = result.scalar_one()

    now = datetime.now(timezone.utc)
    if (
        user.subscription_expires_at is not None
        and user.subscription_expires_at > now
    ):
        base = user.subscription_expires_at
    else:
        base = now

    user.subscription_expires_at = base + relativedelta(
        months=order.duration_months
    )
    user.role = "paid"
    user.subscription_plan = "paid"
    db.add(user)
    await db.flush()


def verify_alipay_callback(params: dict) -> bool:
    """Verify Alipay asynchronous notification signature."""
    try:
        from alipay.aop.api.util.SignatureUtils import verify_with_rsa
    except ImportError:
        logger.error("alipay-sdk-python not installed, cannot verify callback")
        return False

    sign = params.pop("sign", "")
    params.pop("sign_type", None)
    settings.validate_alipay_public_key_config()

    sorted_params = sorted(params.items())
    unsigned_str = "&".join(f"{k}={v}" for k, v in sorted_params if v)

    return verify_with_rsa(
        settings.alipay_public_key,
        unsigned_str.encode("utf-8"),
        sign,
    )


def verify_wechat_callback(headers: dict, body: bytes) -> dict | None:
    """Verify WeChat Pay V3 callback and return parsed resource data."""
    try:
        from wechatpayv3 import WeChatPay, WeChatPayType
    except ImportError:
        logger.error("wechatpayv3 not installed, cannot verify callback")
        return None

    private_key_content = ""
    try:
        with open(settings.wechat_private_key_path, "r") as f:
            private_key_content = f.read()
    except FileNotFoundError:
        logger.warning("WeChat private key file not found")
        return None

    wxpay = WeChatPay(
        wechatpay_type=WeChatPayType.NATIVE,
        mchid=settings.wechat_mch_id,
        private_key=private_key_content,
        cert_serial_no=settings.wechat_cert_serial_no,
        appid=settings.wechat_app_id,
        apiv3_key=settings.wechat_api_key,
        notify_url=settings.wechat_notify_url,
    )

    result = wxpay.callback(headers=headers, body=body.decode("utf-8"))
    if result and isinstance(result, dict):
        return result
    return None
