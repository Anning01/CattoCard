"""支付 API"""

import asyncio
import time

from fastapi import APIRouter

from app.core.exceptions import BadRequestException, NotFoundException
from app.core.logger import logger
from app.core.response import ResponseModel, success_response
from app.models.order import Order
from app.schemas.order import OrderStatus, PaymentInitRequest, PaymentInitResponse
from app.services.email import EmailService
from app.services.payment.registry import get_registry
from app.utils.redis_client import (
    ORDER_TIMEOUT,
    get_order_by_trc20_amount,
    get_pending_order,
    remove_pending_order,
)

router = APIRouter()


@router.post("/init", response_model=ResponseModel, summary="初始化支付")
async def init_payment(data: PaymentInitRequest):
    """
    初始化支付

    用户创建订单后，调用此接口获取支付信息（二维码、跳转链接等）
    """
    logger.info(f"初始化支付: order_no={data.order_no}")

    # 获取订单
    order = await Order.filter(order_no=data.order_no).first()
    if not order:
        raise NotFoundException(message="订单不存在")

    if order.status != OrderStatus.PENDING:
        raise BadRequestException(message="订单状态不正确，无法支付")

    # 检查是否已有待支付记录
    pending = await get_pending_order(data.order_no)
    if pending:
        # 计算剩余过期时间
        expires_at = pending.get("expires_at", 0)
        expires_in = max(0, int(expires_at - time.time()))

        if expires_in <= 0:
            # 清理过期的待支付记录
            await remove_pending_order(data.order_no)
            pending = None
        else:
            # 验证金额是否仍属于当前订单（防止金额被其他订单占用）
            payment_data = pending.get("payment_data", {})
            pending_amount = payment_data.get("amount")
            if pending_amount:
                current_owner = await get_order_by_trc20_amount(pending_amount)
                if current_owner and current_owner != data.order_no:
                    # 金额已被其他订单占用，清理当前待支付记录，重新创建
                    logger.warning(
                        f"支付金额冲突: order_no={data.order_no}, amount={pending_amount}, "
                        f"current_owner={current_owner}"
                    )
                    await remove_pending_order(data.order_no)
                    pending = None
                elif not current_owner:
                    # 金额映射已过期，清理并重新创建
                    logger.info(f"支付金额映射已过期，重新创建: order_no={data.order_no}")
                    await remove_pending_order(data.order_no)
                    pending = None

    # 返回已有的有效支付信息
    if pending:
        payment_data = pending.get("payment_data", {})
        expires_at = pending.get("expires_at", 0)
        expires_in = max(0, int(expires_at - time.time()))
        return success_response(
            data=PaymentInitResponse(
                payment_url=None,
                payment_data=payment_data,
                expires_in=expires_in,
            )
        )

    # 获取支付方式
    await order.fetch_related("payment_method")
    payment_method = order.payment_method
    if not payment_method:
        raise BadRequestException(message="订单未关联支付方式")

    # 获取支付提供者
    meta_data = payment_method.meta_data or {}
    provider_id = meta_data.get("provider_id")
    if not provider_id:
        raise BadRequestException(message="支付方式未配置提供者")

    registry = get_registry()
    provider = registry.get_active_provider(provider_id)
    if not provider:
        raise BadRequestException(message="支付服务暂不可用")

    # 创建支付
    result = await provider.create_payment(
        order_no=data.order_no,
        amount=str(order.total_price),
        currency=order.currency,
    )

    if not result.success:
        raise BadRequestException(message=result.error_message or "创建支付失败")

    logger.info(f"支付初始化成功: order_no={data.order_no}")

    # 异步发送待支付通知邮件（不阻塞响应）
    asyncio.create_task(
        EmailService.send_payment_pending_email(
            to_email=order.email,
            order_no=data.order_no,
            total_price=str(order.total_price),
            currency=order.currency,
            payment_data=result.payment_data,
        )
    )

    return success_response(
        data=PaymentInitResponse(
            payment_url=result.payment_url,
            payment_data=result.payment_data,
            expires_in=ORDER_TIMEOUT,
        )
    )


@router.get("/status/{order_no}", response_model=ResponseModel, summary="查询支付状态")
async def get_payment_status(order_no: str):
    """查询支付状态"""
    logger.info(f"查询支付状态: order_no={order_no}")

    order = await Order.filter(order_no=order_no).first()
    if not order:
        raise NotFoundException(message="订单不存在")

    # 检查待支付记录
    pending = await get_pending_order(order_no)

    status = "pending"
    if order.status == OrderStatus.PAID:
        status = "paid"
    elif order.status == OrderStatus.CANCELLED:
        status = "cancelled"
    elif order.status == OrderStatus.COMPLETED:
        status = "completed"
    elif not pending:
        status = "expired"

    return success_response(
        data={
            "order_no": order_no,
            "status": status,
            "order_status": order.status.value,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        }
    )


# ==================== 测试接口（仅用于开发测试，生产环境请删除） ====================
@router.post("/mock-pay/{order_no}", response_model=ResponseModel, summary="[测试] 模拟支付成功")
async def mock_payment(order_no: str):
    """
    模拟支付成功（仅用于测试）

    直接将订单状态改为已支付
    """
    from datetime import datetime

    from app.models.order import OrderLog
    from app.services.delivery import DeliveryService

    logger.warning(f"[MOCK] 模拟支付: order_no={order_no}")

    order = await Order.filter(order_no=order_no).first()
    if not order:
        raise NotFoundException(message="订单不存在")

    if order.status != OrderStatus.PENDING:
        raise BadRequestException(message="订单状态不正确")

    # 更新订单状态为已支付
    order.status = OrderStatus.PAID
    order.paid_at = datetime.now()
    order.payment_data = {"mock": True, "paid_at": datetime.now().isoformat()}
    await order.save()

    # 记录订单日志
    await OrderLog.create(
        order=order,
        action="payment",
        content="[MOCK] 模拟支付成功",
    )

    # 发送支付成功邮件（异步）
    asyncio.create_task(
        EmailService.send_payment_success_email(
            to_email=order.email,
            order_no=order_no,
            total_price=str(order.total_price),
            currency=order.currency,
        )
    )

    # 检查是否启用虚拟商品自动发货
    if await DeliveryService.get_auto_delivery_enabled():
        success, message, count = await DeliveryService.auto_deliver_virtual_items(order)
        if success and count > 0:
            logger.info(f"[MOCK] 虚拟商品自动发货成功: order_no={order_no}, count={count}")

    logger.warning(f"[MOCK] 支付模拟成功: order_no={order_no}")

    return success_response(message="模拟支付成功")
