"""发货服务"""

import asyncio
from datetime import datetime

from app.core.logger import logger
from app.models.order import Order, OrderItem, OrderLog
from app.models.platform import PlatformConfig
from app.models.product import InventoryItem
from app.schemas.order import OrderStatus
from app.schemas.product import ProductType
from app.services.email import EmailService


class DeliveryService:
    """发货服务"""

    @staticmethod
    async def get_auto_delivery_enabled() -> bool:
        """获取虚拟商品自动发货配置"""
        config = await PlatformConfig.filter(key="auto_delivery_virtual").first()
        if config:
            return config.value.lower() in ("true", "1", "yes", "on")
        return False

    @staticmethod
    async def deliver_order(
        order: Order,
        item_ids: set[int] | None = None,
        remark: str | None = None,
        operator: str = "system",
    ) -> tuple[bool, str, int]:
        """
        发货订单

        Args:
            order: 订单对象
            item_ids: 要发货的商品项ID列表，None表示发全部未发货的
            remark: 发货备注
            operator: 操作人

        Returns:
            (success, message, delivered_count)
        """
        await order.fetch_related("items")

        all_delivery_contents = []
        delivered_count = 0

        for item in order.items:
            # 如果指定了商品项ID，只发货指定的
            if item_ids and item.id not in item_ids:
                continue

            # 如果已发货，跳过
            if item.delivered_at:
                continue

            await item.fetch_related("product")
            product = item.product

            if product.product_type == ProductType.VIRTUAL:
                # 虚拟商品：从库存中获取卡密
                inventory_items = await InventoryItem.filter(
                    product_id=item.product_id,
                    is_sold=False,
                ).limit(item.quantity)

                if len(inventory_items) < item.quantity:
                    error_msg = f"商品 {item.product_name} 库存不足，需要 {item.quantity}，实际 {len(inventory_items)}"
                    logger.error(f"发货失败 - {error_msg}")
                    return False, error_msg, delivered_count

                delivery_contents = []
                for inv_item in inventory_items:
                    inv_item.is_sold = True
                    inv_item.sold_at = datetime.now()
                    await inv_item.save()
                    delivery_contents.append(inv_item.content)

                item.delivery_content = "\n".join(delivery_contents)
                item.delivered_at = datetime.now()
                await item.save()

                all_delivery_contents.append(f"【{item.product_name}】\n{item.delivery_content}")
                delivered_count += 1
            else:
                # 实体商品：标记已发货，delivery_content 为备注信息
                if remark:
                    item.delivery_content = remark
                item.delivered_at = datetime.now()
                await item.save()

                all_delivery_contents.append(f"【{item.product_name}】实体商品已发货")
                delivered_count += 1

        if delivered_count == 0:
            return False, "没有需要发货的商品项", 0

        # 检查是否全部发货完成
        all_delivered = all(item.delivered_at for item in order.items)
        if all_delivered:
            order.status = OrderStatus.COMPLETED
        else:
            order.status = OrderStatus.PROCESSING
        await order.save()

        # 记录日志
        status_text = "全部发货完成" if all_delivered else f"部分发货 ({delivered_count} 件)"
        log_content = status_text
        if remark:
            log_content += f"，备注: {remark}"
        await OrderLog.create(
            order=order,
            action="deliver",
            content=log_content,
            operator=operator,
        )

        # 异步发送发货通知邮件
        email_content = "\n\n".join(all_delivery_contents)
        if remark:
            email_content += f"\n\n商家备注: {remark}"

        asyncio.create_task(
            EmailService.send_delivery_notification(
                to_email=order.email,
                order_no=order.order_no,
                delivery_content=email_content,
            )
        )

        logger.info(f"订单发货成功: order_no={order.order_no}, delivered={delivered_count}, all_done={all_delivered}")
        return True, "发货成功", delivered_count

    @staticmethod
    async def auto_deliver_virtual_items(order: Order) -> tuple[bool, str, int]:
        """
        自动发货虚拟商品

        只发货虚拟商品，实体商品不处理

        Args:
            order: 订单对象

        Returns:
            (success, message, delivered_count)
        """
        await order.fetch_related("items")

        # 获取未发货的虚拟商品项ID
        virtual_item_ids = set()
        for item in order.items:
            if not item.delivered_at and item.product_type == ProductType.VIRTUAL:
                virtual_item_ids.add(item.id)

        if not virtual_item_ids:
            return True, "没有需要自动发货的虚拟商品", 0

        return await DeliveryService.deliver_order(
            order=order,
            item_ids=virtual_item_ids,
            remark=None,
            operator="auto",
        )

    @staticmethod
    async def check_virtual_stock(product_id: int, quantity: int) -> tuple[bool, int]:
        """
        检查虚拟商品库存（基于InventoryItem）

        Args:
            product_id: 商品ID
            quantity: 需要的数量

        Returns:
            (is_sufficient, available_count)
        """
        available = await InventoryItem.filter(
            product_id=product_id,
            is_sold=False,
        ).count()
        return available >= quantity, available

    @staticmethod
    async def get_virtual_stock_count(product_id: int) -> int:
        """获取虚拟商品可用库存数量"""
        return await InventoryItem.filter(
            product_id=product_id,
            is_sold=False,
        ).count()
