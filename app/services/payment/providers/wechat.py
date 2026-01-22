import json
from datetime import datetime, timezone
from typing import Any
from app.services.payment import PaymentProvider
from app.services.payment.base import PaymentResult
from app.services.payment.registry import register_provider
from app.core.logger import logger

from app.models.order import Order, OrderLog
from app.schemas.order import OrderStatus
from app.services.delivery import DeliveryService
from app.services.email import EmailService

from wechatpayv3 import WeChatPay
from wechatpayv3 import WeChatPayType

from app.utils.redis_client import get_pending_order, remove_pending_order


@register_provider
class WechatProvider(PaymentProvider):
    """微信支付提供者"""
    provider_id = "wechat"
    provider_name = "微信支付"


    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._should_stop = False
        self.wechatpay_client = None  # 初始化为 None

        # 配置参数
        self.mchid = config.get("mchid", "")  # 微信支付商户号
        self.apiclient_key = config.get("apiclient_key", "")  # 商户证书私钥
        self.cert_serial_no = config.get("cert_serial_no", "")  # 商户证书序列号
        self.apiv3_key = config.get("apiv3_key", "")  # APIv3密钥
        self.appid = config.get("appid", "")  # APPID
        self.notify_url = config.get("notify_url", "")  # 回调地址
        self.pay_mode = config.get("pay_mode", False)  # 支付模式
        self.request_timeout = config.get("timeout", 10)  # 请求超时时间
        self.response_timeout = config.get("response_timeout", 30)  # 响应超时时间
        self.amount_precision = config.get("amount_precision", 4)  # 金额精度（小数位）

    def is_configured(self) -> bool:
        """检查是否已配置"""
        if not self.mchid:
            logger.warning("微信支付: 未配置商户号 (mchid)")
            return False
        if not self.apiclient_key:
            logger.warning("微信支付: 未配置商户证书私钥 (apiclient_key)")
            return False
        if not self.cert_serial_no:
            logger.warning("微信支付: 未配置商户证书序列号 (cert_serial_no)")
            return False
        if not self.apiv3_key:
            logger.warning("微信支付: 未配置APIv3密钥 (apiv3_key)")
            return False
        if not self.appid:
            logger.warning("微信支付: 未配置APPID (appid)")
            return False
        if not self.notify_url:
            logger.warning("微信支付: 未配置回调地址 (notify_url)")
            return False
        return True

    async def start(self) -> None:
        """
        在 start 中实例化 SDK
        """
        logger.info(f"微信支付提供者启动中... APPID: {self.appid}")

        if not self.is_configured():
            logger.error("微信支付配置不完整，无法启动")
            return

        try:
            # --- 实例化逻辑放在这里 ---
            self.wechatpay_client = WeChatPay(
                wechatpay_type=WeChatPayType.NATIVE,  # 或 JSAPI，根据需求动态传参
                mchid=self.mchid,
                private_key=self.apiclient_key,
                cert_serial_no=self.cert_serial_no,
                apiv3_key=self.apiv3_key,
                appid=self.appid,
                notify_url=self.notify_url,
                cert_dir=None,
                logger=logger  # 如果 SDK 支持传入 logger
            )

            self._is_started = True
            logger.info("微信支付 SDK 初始化成功")

        except Exception as e:
            logger.exception(f"微信支付启动失败: {str(e)}")
            self._is_started = False

    async def stop(self) -> None:
        logger.info("微信支付提供者停止中...")
        self.wechatpay_client = None  # 清理对象
        self._is_started = False

    async def create_payment(self, order_no: str, amount: str, currency: str) -> PaymentResult:
        # 1. 检查是否已启动
        if not self._is_started or self.wechatpay_client is None:
            return PaymentResult(success=False, error_message="微信支付服务未启动")

        try:
            # 2. 转换金额 (假设 amount 是字符串类型的元，微信通常需要分)
            amount_fen = int(float(amount) * 100)

            # 3. 调用 SDK (注意：如果 wechatpayv3 是同步库，建议在 async 环境中放入线程池执行，防止阻塞)
            # 这里假设直接调用
            code, message = self.wechatpay_client.pay(
                description=f"订单-{order_no}",
                out_trade_no=order_no,
                amount={"total": amount_fen, "currency": currency},
                pay_type=WeChatPayType.NATIVE  # 示例使用 Native 扫码
            )

            if code == 200:
                # 解析 message 中的 code_url (针对 Native 支付)
                pay_data = json.loads(message)
                return PaymentResult(
                    success=True,
                    payment_url=pay_data.get('code_url'),
                    payment_data=pay_data
                )
            else:
                return PaymentResult(success=False, error_message=f"微信下单失败: {message}")

        except Exception as e:
            logger.exception("创建微信支付异常")
            return PaymentResult(success=False, error_message=str(e))

    async def verify_payment(self, order_no: str, payment_data: dict) -> bool:
        pending = await get_pending_order(order_no)
        return pending is None  # 如果待支付记录已删除，说明支付已完成


    async def handle_callback(self, data: dict) -> dict:
        """
        处理微信支付回调

        Args:
            data: 包含 headers 和 body 的回调数据

        Returns:
            dict: 包含 success, message, order_no 等信息
        """

        headers = data.get("headers", {})
        body_str = data.get("body", "")

        # 1. 检查客户端是否初始化
        if not self.wechatpay_client:
            logger.error("微信支付回调失败: 微信支付客户端未初始化")
            return {"success": False, "message": "支付服务未初始化"}

        # 2. 验证签名并解密回调数据
        try:
            result = self.wechatpay_client.callback(headers, body_str)
        except Exception as e:
            logger.error(f"微信支付回调验证失败: {e}")
            return {"success": False, "message": "签名验证失败"}

        if not result:
            logger.error("微信支付回调失败: 签名验证失败或解密失败")
            return {"success": False, "message": "签名验证失败"}

        logger.info(f"微信支付回调解密成功: {result}")

        # 3. 提取订单信息
        order_no = result.get("out_trade_no")
        trade_state = result.get("trade_state")
        transaction_id = result.get("transaction_id")

        if not order_no:
            logger.error("微信支付回调失败: 缺少订单号")
            return {"success": False, "message": "缺少订单号"}

        logger.info(
            f"微信支付回调 - 订单号: {order_no}, "
            f"交易状态: {trade_state}, "
            f"微信订单号: {transaction_id}"
        )

        # 4. 只处理支付成功的回调
        if trade_state != "SUCCESS":
            logger.warning(f"微信支付回调 - 订单 {order_no} 状态非成功: {trade_state}")
            return {"success": True, "message": "状态非成功，已忽略", "order_no": order_no}

        # 5. 查询待支付订单
        pending = await get_pending_order(order_no)
        if not pending:
            logger.warning(f"待支付订单不存在: {order_no}")
            return {"success": False, "message": "待支付订单不存在", "order_no": order_no}

        # 6. 检查数据库订单状态
        order = await Order.filter(order_no=order_no).first()
        if not order:
            logger.error(f"订单不存在: {order_no}")
            return {"success": False, "message": "订单不存在", "order_no": order_no}

        if order.status != OrderStatus.PENDING:
            logger.warning(f"订单状态不是待支付: {order_no}, status={order.status}")
            return {"success": True, "message": "订单已处理", "order_no": order_no}

        # 7. 更新订单状态为已支付
        order.status = OrderStatus.PAID
        order.paid_at = datetime.now(timezone.utc)
        order.payment_data = {
            "provider": self.provider_id,
            "transaction_id": transaction_id,
            **result
        }
        await order.save()

        # 8. 记录支付日志
        amount_info = result.get("amount", {})
        amount_total = amount_info.get("total", 0)
        await OrderLog.create(
            order=order,
            action="payment",
            content=f"微信支付成功，交易ID: {transaction_id}，金额: {amount_total} 分",
        )

        # 9. 清理 Redis 数据
        await remove_pending_order(order_no)

        logger.info(f"订单支付完成: order_no={order_no}, transaction_id={transaction_id}")

        # 10. 发送支付成功邮件
        await EmailService.send_payment_success_email(
            to_email=order.email,
            order_no=order_no,
            total_price=str(order.total_price),
            currency=order.currency,
        )

        # 11. 检查是否启用虚拟商品自动发货
        if await DeliveryService.get_auto_delivery_enabled():
            success, message, count = await DeliveryService.auto_deliver_virtual_items(order)
            if success and count > 0:
                logger.info(f"虚拟商品自动发货成功: order_no={order_no}, count={count}")
            elif not success:
                logger.warning(f"虚拟商品自动发货失败: order_no={order_no}, message={message}")

        logger.info(f"微信支付回调处理完成: {order_no}")

        return {
            "success": True,
            "message": "支付成功",
            "order_no": order_no,
            "transaction_id": transaction_id
        }


