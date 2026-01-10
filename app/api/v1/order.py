"""订单前台API"""

from decimal import Decimal

from fastapi import APIRouter

from app.core.exceptions import BadRequestException, NotFoundException
from app.core.logger import logger
from app.core.response import ResponseModel, success_response
from app.models.order import Order, OrderItem, OrderLog
from app.schemas.order import OrderStatus
from app.models.product import PaymentMethod, Product
from app.schemas.order import (
    OrderCreate,
    OrderDetailResponse,
    OrderItemResponse,
    OrderListResponse,
    OrderQueryByEmail,
)
from app.schemas.product import ProductType
from app.services.delivery import DeliveryService

router = APIRouter()


@router.post("", response_model=ResponseModel, summary="创建订单")
async def create_order(data: OrderCreate):
    logger.info(f"创建订单: email={data.email}, items={len(data.items)}")

    payment_method = await PaymentMethod.filter(id=data.payment_method_id, is_active=True).first()
    if not payment_method:
        logger.warning(f"支付方式不存在: id={data.payment_method_id}")
        raise BadRequestException(message="支付方式不存在或已禁用")

    total_price = Decimal("0")
    order_items_data = []

    for item in data.items:
        product = await Product.filter(id=item.product_id, is_active=True).first()
        if not product:
            logger.warning(f"商品不存在: id={item.product_id}")
            raise BadRequestException(message=f"商品ID {item.product_id} 不存在或已下架")

        # 虚拟商品检查InventoryItem库存，实体商品检查stock
        if product.product_type == ProductType.VIRTUAL:
            is_sufficient, available = await DeliveryService.check_virtual_stock(product.id, item.quantity)
            if not is_sufficient:
                logger.warning(f"虚拟商品库存不足: {product.name}, available={available}, need={item.quantity}")
                raise BadRequestException(message=f"商品 {product.name} 库存不足（可用: {available}）")
        else:
            if product.stock < item.quantity:
                logger.warning(f"实体商品库存不足: {product.name}, stock={product.stock}, need={item.quantity}")
                raise BadRequestException(message=f"商品 {product.name} 库存不足")

        await product.fetch_related("payment_methods")
        if payment_method not in product.payment_methods:
            logger.warning(f"商品不支持此支付方式: {product.name}")
            raise BadRequestException(message=f"商品 {product.name} 不支持此支付方式")

        subtotal = product.price * item.quantity
        total_price += subtotal
        order_items_data.append(
            {
                "product": product,
                "product_name": product.name,
                "product_type": product.product_type,
                "quantity": item.quantity,
                "price": product.price,
                "subtotal": subtotal,
            }
        )

    if payment_method.fee_type.value == "percentage":
        fee = total_price * payment_method.fee_value / 100
    else:
        fee = payment_method.fee_value
    total_price += fee

    order = await Order.create(
        email=data.email,
        currency=data.currency,
        total_price=total_price,
        payment_method=payment_method,
        shipping_name=data.shipping_name,
        shipping_phone=data.shipping_phone,
        shipping_address=data.shipping_address,
        remark=data.remark,
    )

    logger.info(f"订单创建成功: order_no={order.order_no}")

    for item_data in order_items_data:
        product = item_data.pop("product")
        await OrderItem.create(order=order, product=product, **item_data)
        product.stock -= item_data["quantity"]
        await product.save()

    await OrderLog.create(order=order, action="create", content="订单创建")
    await order.fetch_related("items")

    response_data = OrderDetailResponse(
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
    return success_response(data=response_data, message="订单创建成功")


@router.post("/query", response_model=ResponseModel, summary="通过邮箱查询订单")
async def query_orders(data: OrderQueryByEmail):
    logger.info(f"查询订单: email={data.email}, order_no={data.order_no}")
    query = Order.filter(email=data.email)
    if data.order_no:
        query = query.filter(order_no=data.order_no)

    orders = await query.order_by("-created_at").limit(50)
    result = [OrderListResponse.model_validate(order) for order in orders]
    logger.info(f"查询到 {len(result)} 个订单")
    return success_response(data=result)


@router.get("/{order_no}", response_model=ResponseModel, summary="获取订单详情")
async def get_order(order_no: str, email: str):
    logger.info(f"获取订单详情: order_no={order_no}, email={email}")
    order = await Order.filter(order_no=order_no, email=email).first()
    if not order:
        logger.warning(f"订单不存在: order_no={order_no}")
        raise NotFoundException(message="订单不存在")

    await order.fetch_related("items")

    items = []
    for item in order.items:
        item_dict = OrderItemResponse.model_validate(item).model_dump()
        if order.status != OrderStatus.COMPLETED:
            item_dict["delivery_content"] = None
        items.append(OrderItemResponse.model_validate(item_dict))

    response_data = OrderDetailResponse(
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
        items=items,
    )
    return success_response(data=response_data)
