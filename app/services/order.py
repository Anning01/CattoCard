"""订单服务"""

from app.core.logger import logger
from app.models.order import Order, OrderLog, OrderStatus
from app.models.product import Product
from app.utils.redis_client import (
    get_pending_order,
    remove_pending_order,
    remove_trc20_pending_amount,
)


class OrderService:
    """订单服务"""

    @staticmethod
    async def cancel_order(
        order: Order,
        operator: str = "system",
        reason: str | None = None,
    ) -> bool:
        """取消订单"""
        # 验证订单状态
        if order.status != OrderStatus.PENDING:
            logger.warning(
                f"订单状态不正确，无法取消: order_no={order.order_no}, status={order.status}"
            )
            return False

        logger.info(f"取消订单: order_no={order.order_no}, operator={operator}")

        # 获取待支付数据用于后续清理
        pending_data = await get_pending_order(order.order_no)

        # 释放库存
        await order.fetch_related("items")
        for item in order.items:
            product = await Product.filter(id=item.product_id).first()
            if product:
                # 无论是实体还是虚拟商品，取消订单都需要恢复库存
                # 注意：虚拟商品下单时是扣减了InventoryItem还是Product.stock需要确认
                # 根据 app/api/v1/order.py 逻辑：
                # 虚拟商品检查 DeliveryService.check_virtual_stock (不扣减Product.stock?)
                # 实体商品扣减 Product.stock
                # 但 line 103: product.stock -= item_data["quantity"] 对所有商品都执行了扣减
                # 所以这里统一恢复 Product.stock 是正确的

                product.stock += item.quantity
                await product.save()
                logger.info(f"释放库存: product_id={product.id}, quantity={item.quantity}")

        # 更新订单状态
        order.status = OrderStatus.CANCELLED
        await order.save()

        # 记录日志
        log_content = f"订单已取消，操作人：{operator}"
        if reason:
            log_content += f"，原因：{reason}"

        await OrderLog.create(
            order=order,
            action="cancel",
            content=log_content,
            operator=operator,
        )

        # 清理 Redis 数据
        await remove_pending_order(order.order_no)

        # 如果是 TRC20 支付，清理金额映射
        if pending_data:
            payment_data = pending_data.get("payment_data", {})
            if payment_data.get("amount"):
                await remove_trc20_pending_amount(payment_data["amount"])
                logger.info(f"清理 TRC20 待支付金额: amount={payment_data['amount']}")

        logger.info(f"订单取消成功: order_no={order.order_no}")
        return True
