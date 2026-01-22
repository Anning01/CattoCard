"""订单超时处理任务"""

import asyncio

from app.core.logger import logger
from app.models.order import Order, OrderLog
from app.models.product import Product
from app.schemas.order import OrderStatus
from app.utils.redis_client import (
    DistributedLock,
    get_expired_orders,
    remove_pending_order,
    remove_trc20_pending_amount,
)

# 超时检查间隔（秒）
CHECK_INTERVAL = 60


class OrderTimeoutTask:
    """订单超时处理任务"""

    def __init__(self):
        self._task: asyncio.Task | None = None
        self._should_stop = False

    async def start(self) -> None:
        """启动超时检查任务"""
        logger.info("订单超时检查任务启动中...")
        self._should_stop = False
        self._task = asyncio.create_task(self._check_loop())
        logger.info("订单超时检查任务已启动")

    async def stop(self) -> None:
        """停止超时检查任务"""
        logger.info("订单超时检查任务停止中...")
        self._should_stop = True

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info("订单超时检查任务已停止")

    async def _check_loop(self) -> None:
        """检查循环"""
        logger.info("订单超时检查循环开始")

        while not self._should_stop:
            try:
                # 尝试获取分布式锁
                lock = DistributedLock("order_timeout_checker", ttl=CHECK_INTERVAL + 10)

                if await lock.acquire():
                    try:
                        await self._check_expired_orders()
                    finally:
                        await lock.release()
                else:
                    logger.debug("订单超时检查锁被其他 worker 持有，跳过本次检查")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"订单超时检查出错: {e}")

            await asyncio.sleep(CHECK_INTERVAL)

        logger.info("订单超时检查循环结束")

    async def _check_expired_orders(self) -> None:
        """检查并处理过期订单"""
        expired_orders = await get_expired_orders()

        if not expired_orders:
            return

        logger.info(f"发现 {len(expired_orders)} 个过期订单")

        for order_data in expired_orders:
            order_no = order_data.get("order_no")
            if not order_no:
                continue

            try:
                await self._cancel_order(order_no, order_data)
            except Exception as e:
                logger.error(f"取消超时订单失败: order_no={order_no}, error={e}")

    async def _cancel_order(self, order_no: str, pending_data: dict) -> None:
        """取消超时订单并释放库存"""
        order = await Order.filter(order_no=order_no).first()
        if not order:
            # 订单不存在，清理 Redis 数据
            await self._cleanup_pending_data(order_no, pending_data)
            return

        # 只处理待支付状态的订单
        if order.status != OrderStatus.PENDING:
            await self._cleanup_pending_data(order_no, pending_data)
            return

        logger.info(f"取消超时订单: order_no={order_no}")

        # 释放库存
        await order.fetch_related("items")
        for item in order.items:
            product = await Product.filter(id=item.product_id).first()
            if product:
                product.stock += item.quantity
                await product.save()
                logger.info(f"释放库存: product_id={product.id}, quantity={item.quantity}")

        # 更新订单状态
        order.status = OrderStatus.CANCELLED
        await order.save()

        # 记录日志
        await OrderLog.create(
            order=order,
            action="timeout_cancel",
            content="订单超时未支付，自动取消并释放库存",
        )

        # 清理 Redis 数据
        await self._cleanup_pending_data(order_no, pending_data)

        logger.info(f"超时订单已取消: order_no={order_no}")

    async def _cleanup_pending_data(self, order_no: str, pending_data: dict) -> None:
        """清理待支付订单的 Redis 数据"""
        await remove_pending_order(order_no)

        # 如果是 TRC20 支付，清理金额映射
        payment_data = pending_data.get("payment_data", {})
        if payment_data.get("amount"):
            await remove_trc20_pending_amount(payment_data["amount"])


# 全局实例
_timeout_task: OrderTimeoutTask | None = None


def get_timeout_task() -> OrderTimeoutTask:
    """获取全局超时任务实例"""
    global _timeout_task
    if _timeout_task is None:
        _timeout_task = OrderTimeoutTask()
    return _timeout_task
