"""订单管理API"""

from fastapi import APIRouter, Query

from app.core.exceptions import BadRequestException, NotFoundException
from app.core.logger import logger
from app.core.response import PaginatedData, ResponseModel, success_response
from app.models.order import Order, OrderLog
from app.models.product import InventoryItem
from app.schemas.order import (
    OrderDetailResponse,
    OrderItemResponse,
    OrderListResponse,
    OrderLogResponse,
    OrderStatus,
    OrderUpdate,
)
from app.services.delivery import DeliveryService
from app.utils.common import paginate

router = APIRouter()


async def _get_order_detail(order_id: int) -> OrderDetailResponse:
    order = await Order.filter(id=order_id).first()
    if not order:
        raise NotFoundException(message="订单不存在")

    await order.fetch_related("items")

    return OrderDetailResponse(
        id=order.id,
        order_no=order.order_no,
        status=order.status,
        email=order.email,
        currency=order.currency,
        total_price=order.total_price,
        paid_at=order.paid_at,
        payment_method_id=order.payment_method_id,
        shipping_name=order.shipping_name,
        shipping_phone=order.shipping_phone,
        shipping_address=order.shipping_address,
        remark=order.remark,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=[OrderItemResponse.model_validate(item) for item in order.items],
    )


@router.get("", response_model=ResponseModel, summary="获取订单列表")
async def get_orders(
    status: OrderStatus | None = None,
    email: str | None = None,
    order_no: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    logger.info(f"获取订单列表(管理): status={status}, email={email}, order_no={order_no}")
    query = Order.all()

    if status:
        query = query.filter(status=status)
    if email:
        query = query.filter(email__icontains=email)
    if order_no:
        query = query.filter(order_no__icontains=order_no)

    query = query.order_by("-created_at")
    items, total, pages = await paginate(query, page, page_size)

    logger.info(f"获取到 {len(items)} 个订单, 共 {total} 条")
    data = PaginatedData(
        items=[OrderListResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )
    return success_response(data=data)


@router.get("/{order_id}", response_model=ResponseModel, summary="获取订单详情")
async def get_order(order_id: int):
    logger.info(f"获取订单详情(管理): id={order_id}")
    data = await _get_order_detail(order_id)
    return success_response(data=data)


@router.put("/{order_id}", response_model=ResponseModel, summary="更新订单")
async def update_order(order_id: int, data: OrderUpdate):
    logger.info(f"更新订单: id={order_id}")
    order = await Order.filter(id=order_id).first()
    if not order:
        raise NotFoundException(message="订单不存在")

    old_status = order.status
    update_data = data.model_dump(exclude_unset=True)

    await order.update_from_dict(update_data).save()

    if "status" in update_data and update_data["status"] != old_status:
        await OrderLog.create(
            order=order,
            action="status_change",
            content=f"订单状态从 {old_status.value} 变更为 {update_data['status'].value}",
            operator="admin",
        )
        logger.info(f"订单状态变更: {old_status.value} -> {update_data['status'].value}")

    response_data = await _get_order_detail(order_id)
    return success_response(data=response_data)


@router.post("/{order_id}/deliver", response_model=ResponseModel, summary="订单发货（虚拟商品自动发货）")
async def deliver_order(order_id: int, remark: str | None = None, item_ids: str | None = None):
    """
    虚拟商品订单发货：自动从库存中扣除卡密
    实体商品订单发货：只标记为已发货，不处理库存

    item_ids: 可选，逗号分隔的商品项ID列表，用于部分发货。不传则发全部未发货的商品项。
    """
    logger.info(f"订单发货: id={order_id}, item_ids={item_ids}")
    order = await Order.filter(id=order_id).first()
    if not order:
        raise NotFoundException(message="订单不存在")

    if order.status not in [OrderStatus.PAID, OrderStatus.PROCESSING]:
        raise BadRequestException(message="只有已支付或处理中的订单可以发货")

    # 解析要发货的商品项ID
    target_item_ids: set[int] | None = None
    if item_ids:
        target_item_ids = set(int(x.strip()) for x in item_ids.split(",") if x.strip())

    success, message, delivered_count = await DeliveryService.deliver_order(
        order=order,
        item_ids=target_item_ids,
        remark=remark,
        operator="admin",
    )

    if not success:
        raise BadRequestException(message=message)

    return success_response(message=message)


@router.post("/{order_id}/cancel", response_model=ResponseModel, summary="取消订单")
async def cancel_order(order_id: int):
    logger.info(f"取消订单: id={order_id}")
    order = await Order.filter(id=order_id).first()
    if not order:
        raise NotFoundException(message="订单不存在")

    # 只有待支付订单可以取消
    if order.status != OrderStatus.PENDING:
        raise BadRequestException(message="只有待支付的订单可以取消")

    await order.fetch_related("items")
    for item in order.items:
        await item.fetch_related("product")
        product = item.product
        product.stock += item.quantity
        await product.save()

    order.status = OrderStatus.CANCELLED
    await order.save()

    await OrderLog.create(
        order=order,
        action="cancel",
        content="订单已取消",
        operator="admin",
    )

    logger.info(f"订单取消成功: order_no={order.order_no}")
    return success_response(message="订单已取消")


@router.get("/{order_id}/logs", response_model=ResponseModel, summary="获取订单日志")
async def get_order_logs(order_id: int):
    logger.info(f"获取订单日志: order_id={order_id}")
    order = await Order.filter(id=order_id).first()
    if not order:
        raise NotFoundException(message="订单不存在")

    logs = await OrderLog.filter(order_id=order_id).order_by("-created_at")
    data = [OrderLogResponse.model_validate(log) for log in logs]
    logger.info(f"获取到 {len(data)} 条日志")
    return success_response(data=data)
