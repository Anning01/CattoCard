"""TRC20 USDT 支付提供者"""

import asyncio
import time
from datetime import UTC
from decimal import ROUND_DOWN, Decimal
from typing import Any

import httpx

from app.core.logger import logger
from app.services.payment.base import PaymentProvider, PaymentResult
from app.services.payment.registry import register_provider
from app.utils.redis_client import (
    DistributedLock,
    add_pending_order,
    add_scan_log,
    add_trc20_pending_amount,
    get_order_by_trc20_amount,
    get_pending_order,
    is_tx_processed,
    mark_tx_processed,
    remove_pending_order,
    remove_trc20_pending_amount,
)


@register_provider
class TRC20Provider(PaymentProvider):
    """TRC20 USDT 支付提供者"""

    provider_id = "trc20_usdt"
    provider_name = "TRC20 USDT"

    # TronGrid API
    TRONGRID_API = "https://api.trongrid.io"
    # USDT TRC20 合约地址
    USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._scanner_task: asyncio.Task | None = None
        self._should_stop = False

        # 配置参数
        self.wallet_address = config.get("wallet_address", "")
        self.trongrid_api_key = config.get("trongrid_api_key", "")
        self.scan_interval = config.get("scan_interval", 30)  # 扫描间隔（秒）
        self.amount_precision = config.get("amount_precision", 4)  # 金额精度（小数位）

    def is_configured(self) -> bool:
        """检查是否已配置"""
        if not self.wallet_address:
            logger.warning("TRC20: 未配置钱包地址 (wallet_address)")
            return False
        return True

    async def start(self) -> None:
        """启动扫描任务"""
        logger.info(f"TRC20 支付提供者启动中... 钱包地址: {self.wallet_address}")
        self._should_stop = False
        self._scanner_task = asyncio.create_task(self._scanner_loop())
        logger.info("TRC20 区块链扫描任务已启动")

    async def stop(self) -> None:
        """停止扫描任务"""
        logger.info("TRC20 支付提供者停止中...")
        self._should_stop = True

        if self._scanner_task:
            self._scanner_task.cancel()
            try:
                await self._scanner_task
            except asyncio.CancelledError:
                pass
            self._scanner_task = None

        logger.info("TRC20 支付提供者已停止")

    async def create_payment(self, order_no: str, amount: str, currency: str) -> PaymentResult:
        """
        创建 TRC20 支付

        生成唯一金额（通过添加小额后缀）来识别订单
        """
        try:
            # 生成唯一金额
            unique_amount = await self._generate_unique_amount(amount, order_no)

            if not unique_amount:
                return PaymentResult(
                    success=False,
                    error_message="无法生成唯一支付金额，请稍后重试",
                )

            # 记录待支付订单
            payment_data = {
                "wallet_address": self.wallet_address,
                "amount": unique_amount,
                "original_amount": amount,
                "currency": "USDT",
                "network": "TRC20",
            }

            await add_pending_order(order_no, self.provider_id, payment_data)
            await add_trc20_pending_amount(unique_amount, order_no)

            logger.info(f"TRC20 支付创建成功: order_no={order_no}, amount={unique_amount}")

            return PaymentResult(
                success=True,
                payment_data={
                    "wallet_address": self.wallet_address,
                    "amount": unique_amount,
                    "original_amount": amount,
                    "network": "TRC20",
                    "currency": "USDT",
                    "qr_content": self.wallet_address,
                },
            )

        except Exception as e:
            logger.error(f"TRC20 创建支付失败: {e}")
            return PaymentResult(
                success=False,
                error_message=f"创建支付失败: {str(e)}",
            )

    async def _generate_unique_amount(self, base_amount: str, order_no: str) -> str | None:
        """
        生成唯一金额

        在原金额基础上添加小额后缀（如 10.00 -> 10.0001）
        确保金额唯一性以便识别订单
        """
        base = Decimal(base_amount)

        # 尝试不同的后缀
        limit = 10**self.amount_precision
        for i in range(1, limit):
            # 生成后缀 0.0001, 0.0002, ...
            suffix = Decimal(i) / Decimal(10**self.amount_precision)
            unique_amount = (base + suffix).quantize(
                Decimal(10) ** -self.amount_precision, rounding=ROUND_DOWN
            )
            amount_str = str(unique_amount)

            # 检查是否已被使用
            existing = await get_order_by_trc20_amount(amount_str)
            if not existing:
                return amount_str

        logger.error(f"无法为订单 {order_no} 生成唯一金额")
        return None

    async def verify_payment(self, order_no: str, payment_data: dict) -> bool:
        """验证支付是否完成"""
        pending = await get_pending_order(order_no)
        return pending is None  # 如果待支付记录已删除，说明支付已完成

    async def _scanner_loop(self) -> None:
        """扫描循环"""
        logger.info("TRC20 扫描循环开始")

        while not self._should_stop:
            try:
                # 尝试获取分布式锁
                lock = DistributedLock("trc20_scanner", ttl=self.scan_interval + 10)

                if await lock.acquire():
                    try:
                        await self._scan_transactions()
                    finally:
                        await lock.release()
                else:
                    logger.debug("TRC20 扫描锁被其他 worker 持有，跳过本次扫描")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"TRC20 扫描出错: {e}")
                await add_scan_log(
                    {
                        "time": time.time(),
                        "type": "error",
                        "message": str(e),
                    }
                )

            # 等待下一次扫描
            await asyncio.sleep(self.scan_interval)

        logger.info("TRC20 扫描循环结束")

    async def _scan_transactions(self) -> None:
        """扫描区块链交易"""
        scan_start = time.time()
        matched_count = 0

        try:
            # 获取最近的 TRC20 转账交易
            transactions = await self._fetch_trc20_transfers()
            scanned_count = len(transactions)

            for tx in transactions:
                tx_id = tx.get("transaction_id")
                if not tx_id:
                    continue

                # 检查是否已处理
                if await is_tx_processed(tx_id):
                    continue

                # 检查是否是转入交易
                to_address = tx.get("to")
                if to_address != self.wallet_address:
                    continue

                # 获取金额（USDT 有 6 位小数）
                value = tx.get("value", "0")
                amount = str(Decimal(value) / Decimal(10**6))

                # 查找匹配的订单
                order_no = await get_order_by_trc20_amount(amount)
                if order_no:
                    logger.info(
                        f"TRC20 匹配到订单: order_no={order_no}, amount={amount}, tx_id={tx_id}"
                    )
                    matched_count += 1

                    # 标记交易已处理
                    await mark_tx_processed(tx_id)

                    # 通知订单支付完成
                    await self._complete_payment(order_no, tx_id, amount)

            # 记录扫描日志
            await add_scan_log(
                {
                    "time": time.time(),
                    "type": "scan",
                    "duration": time.time() - scan_start,
                    "scanned": scanned_count,
                    "matched": matched_count,
                }
            )

        except Exception as e:
            logger.error(f"TRC20 扫描交易失败: {e}")
            await add_scan_log(
                {
                    "time": time.time(),
                    "type": "error",
                    "message": str(e),
                }
            )

    async def _fetch_trc20_transfers(self) -> list[dict]:
        """获取 TRC20 转账记录"""
        url = f"{self.TRONGRID_API}/v1/accounts/{self.wallet_address}/transactions/trc20"

        headers = {}
        if self.trongrid_api_key:
            headers["TRON-PRO-API-KEY"] = self.trongrid_api_key

        params = {
            "only_to": "true",
            "limit": 50,
            "contract_address": self.USDT_CONTRACT,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])

    async def _complete_payment(self, order_no: str, tx_id: str, amount: str) -> None:
        """完成支付处理"""
        from datetime import datetime

        from app.models.order import Order, OrderLog
        from app.schemas.order import OrderStatus
        from app.services.delivery import DeliveryService
        from app.services.email import EmailService

        try:
            # 获取待支付订单信息
            pending = await get_pending_order(order_no)
            if not pending:
                logger.warning(f"待支付订单不存在: {order_no}")
                return

            # 更新数据库订单状态
            order = await Order.filter(order_no=order_no).first()
            if not order:
                logger.error(f"订单不存在: {order_no}")
                return

            if order.status != OrderStatus.PENDING:
                logger.warning(f"订单状态不是待支付: {order_no}, status={order.status}")
                return

            # 更新订单
            order.status = OrderStatus.PAID
            order.paid_at = datetime.now(UTC)
            order.payment_data = {
                "provider": self.provider_id,
                "tx_id": tx_id,
                "amount": amount,
                "wallet_address": self.wallet_address,
            }
            await order.save()

            # 记录日志
            await OrderLog.create(
                order=order,
                action="payment",
                content=f"TRC20 支付成功，交易ID: {tx_id}，金额: {amount} USDT",
            )

            # 清理 Redis 数据
            await remove_pending_order(order_no)
            payment_data = pending.get("payment_data", {})
            if payment_data.get("amount"):
                await remove_trc20_pending_amount(payment_data["amount"])

            logger.info(f"订单支付完成: order_no={order_no}, tx_id={tx_id}")

            # 发送支付成功邮件
            await EmailService.send_payment_success_email(
                to_email=order.email,
                order_no=order_no,
                total_price=str(order.total_price),
                currency=order.currency,
            )

            # 检查是否启用虚拟商品自动发货
            if await DeliveryService.get_auto_delivery_enabled():
                success, message, count = await DeliveryService.auto_deliver_virtual_items(order)
                if success and count > 0:
                    logger.info(f"虚拟商品自动发货成功: order_no={order_no}, count={count}")
                elif not success:
                    logger.warning(f"虚拟商品自动发货失败: order_no={order_no}, message={message}")

            # 记录到扫描日志
            await add_scan_log(
                {
                    "time": time.time(),
                    "type": "payment_success",
                    "order_no": order_no,
                    "tx_id": tx_id,
                    "amount": amount,
                }
            )

        except Exception as e:
            logger.error(f"完成支付处理失败: order_no={order_no}, error={e}")
            await add_scan_log(
                {
                    "time": time.time(),
                    "type": "payment_error",
                    "order_no": order_no,
                    "tx_id": tx_id,
                    "error": str(e),
                }
            )


# ==================== 测试工具 ====================


async def test_fetch_transactions(wallet_address: str, api_key: str = "") -> None:
    """测试获取钱包的 TRC20 USDT 转账记录"""
    # 主网 USDT 合约地址
    usdt_contract = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
    url = f"https://api.trongrid.io/v1/accounts/{wallet_address}/transactions/trc20"

    headers = {}
    if api_key:
        headers["TRON-PRO-API-KEY"] = api_key

    params = {
        "only_to": "true",
        "limit": 20,
        "contract_address": usdt_contract,
    }

    print(f"\n{'=' * 60}")
    print(f"钱包地址: {wallet_address}")
    print(f"API Key: {'已配置' if api_key else '未配置'}")
    print(f"USDT 合约: {usdt_contract}")
    print(f"{'=' * 60}\n")

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            transactions = data.get("data", [])
            print(f"获取到 {len(transactions)} 条交易记录\n")

            if not transactions:
                print("暂无转入交易")
                return

            for i, tx in enumerate(transactions, 1):
                tx_id = tx.get("transaction_id", "N/A")
                from_addr = tx.get("from", "N/A")
                to_addr = tx.get("to", "N/A")
                value = tx.get("value", "0")
                # USDT 有 6 位小数
                amount = Decimal(value) / Decimal(10**6)
                token_info = tx.get("token_info", {})
                symbol = token_info.get("symbol", "USDT")
                block_timestamp = tx.get("block_timestamp", 0)

                # 转换时间戳
                from datetime import datetime

                tx_time = datetime.fromtimestamp(block_timestamp / 1000).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                print(f"[{i}] 交易 ID: {tx_id[:20]}...")
                print(f"    时间: {tx_time}")
                print(f"    发送方: {from_addr}")
                print(f"    接收方: {to_addr}")
                print(f"    金额: {amount} {symbol}")
                print()

        except httpx.HTTPStatusError as e:
            print(f"HTTP 错误: {e.response.status_code}")
            print(f"响应内容: {e.response.text}")
        except Exception as e:
            print(f"请求失败: {e}")


if __name__ == "__main__":
    import sys

    print("\n" + "=" * 60)
    print("TRC20 USDT 支付测试工具")
    print("=" * 60)

    # 从命令行获取钱包地址
    if len(sys.argv) < 2:
        print("\n用法: python -m app.services.payment.providers.trc20 <钱包地址> [API_KEY]")
        print("\n示例:")
        print("  python -m app.services.payment.providers.trc20 TXxxxxx")
        print("  python -m app.services.payment.providers.trc20 TXxxxxx your-api-key")
        sys.exit(1)

    wallet = sys.argv[1]
    api_key = sys.argv[2] if len(sys.argv) > 2 else ""

    asyncio.run(test_fetch_transactions(wallet, api_key))
