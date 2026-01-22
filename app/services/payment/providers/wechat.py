import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import asyncio
from forex_python.converter import CurrencyRates
from wechatpayv3 import WeChatPay, WeChatPayType

from app.core.logger import logger
from app.models.order import Order, OrderLog
from app.schemas.order import OrderStatus
from app.services.delivery import DeliveryService
from app.services.email import EmailService
from app.services.payment import PaymentProvider
from app.services.payment.base import PaymentResult
from app.services.payment.registry import register_provider
from app.utils.redis_client import add_pending_order, get_pending_order, remove_pending_order


def convert_to_cny(amount: str, from_currency: str) -> str:
    """
    将金额转换为人民币（CNY）

    Args:
        amount: 原始金额（字符串）
        from_currency: 原始货币代码，如 USD, EUR 等

    Returns:
        转换后的 CNY 金额（字符串）
    """
    if from_currency.upper() == "CNY":
        return amount

    try:
        c = CurrencyRates()
        # forex-python 返回的是 1 单位源货币等于多少 CNY
        rate = c.get_rate(from_currency.upper(), "CNY")
        cny_amount = Decimal(amount) * Decimal(str(rate))
        return f"{cny_amount:.2f}"
    except Exception as e:
        logger.warning(f"货币转换失败 ({from_currency} -> CNY): {e}")
        return amount


def load_weird_shaped_key(weird_key_str: str) -> str:
    """
    能够处理：倒三角形、带空格、带换行、缺头尾的任何私钥字符串
    """
    # 1. 【核心步骤】清洗所有空白字符
    # split() 不带参数时，会自动去除所有换行符(\n)、空格( )、制表符(\t)
    # 然后用 join 将它们连成一整行纯净的 Base64 字符串
    clean_key = "".join(weird_key_str.split())

    # 2. 如果字符串里包含了头尾标识，先去掉（防止重复添加）
    clean_key = clean_key.replace("-----BEGINPRIVATEKEY-----", "").replace(
        "-----ENDPRIVATEKEY-----", ""
    )

    # 3. 【重组】按标准 PEM 格式组装（每64字符换行，但这步其实可选，关键是头尾要独占一行）
    # 为了模拟 open() 读取的效果，我们还是做一个切分
    chunk_size = 64
    content_lines = [clean_key[i : i + chunk_size] for i in range(0, len(clean_key), chunk_size)]

    # 4. 拼接最终结果
    final_pem = (
        "-----BEGIN PRIVATE KEY-----\n" + "\n".join(content_lines) + "\n-----END PRIVATE KEY-----"
    )

    return final_pem


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
                private_key=load_weird_shaped_key(self.apiclient_key),
                cert_serial_no=self.cert_serial_no,
                apiv3_key=self.apiv3_key,
                appid=self.appid,
                notify_url=self.notify_url,
                cert_dir=None,
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
            # 2. 转换为人民币（微信只支持 CNY）
            amount_cny = convert_to_cny(amount, currency)

            # 3. 转换金额为分（微信支付单位）
            amount_fen = int(float(amount_cny) * 100)

            # 4. 调用 SDK
            code, message = self.wechatpay_client.pay(
                description=f"订单-{order_no}",
                out_trade_no=order_no,
                amount={"total": amount_fen},
                pay_type=WeChatPayType.NATIVE,  # 使用 Native 扫码
            )

            if code == 200:
                # 解析 message 中的 code_url (针对 Native 支付)
                pay_data = json.loads(message)

                payment_data = {
                    "order_no": order_no,
                    "amount": amount_cny,
                    "original_amount": amount,
                    "currency": "CNY",
                    "network": "微信支付",
                    **pay_data,
                }

                # 记录待支付订单
                await add_pending_order(order_no, self.provider_id, payment_data)

                return PaymentResult(
                    success=True, payment_url=pay_data.get("code_url"), payment_data=pay_data
                )
            else:
                return PaymentResult(success=False, error_message=f"微信下单失败: {message}")

        except Exception as e:
            logger.exception("创建微信支付异常")
            return PaymentResult(success=False, error_message=str(e))

    async def verify_payment(self, order_no: str, payment_data: dict) -> bool:
        """
        主动查询微信支付订单状态，如果支付成功则触发完成流程
        :param order_no: 商户订单号 (out_trade_no)
        :param payment_data: 可选参数
        :return: True (支付成功) / False (未支付或失败)
        """
        # 1. 检查客户端是否初始化
        if not self._is_started or self.wechatpay_client is None:
            logger.error("微信支付服务未启动，无法查询")
            return False

        try:
            # 2. 定义同步查询函数 (wechatpayv3 是同步库)
            def _sync_query():
                return self.wechatpay_client.query(out_trade_no=order_no)

            # 3. 在线程池中执行同步代码，避免阻塞 Asyncio 事件循环
            loop = asyncio.get_running_loop()
            code, message = await loop.run_in_executor(None, _sync_query)

            # 4. 处理返回结果
            if code == 200:
                result = json.loads(message)
                trade_state = result.get("trade_state")

                if trade_state == "SUCCESS":
                    logger.info(f"订单 {order_no} 查询结果: 支付成功，触发完成流程")
                    # 调用统一的完成流程
                    callback_result = await self.handle_callback({
                        "source": "query",  # 标记来源是主动查询
                        "query_result": result,
                    })
                    return callback_result.get("success", False)
                else:
                    logger.info(f"订单 {order_no} 状态: {trade_state}")
                    return False
            else:
                logger.error(f"查询微信订单失败: {code} - {message}")
                return False

        except Exception as e:
            logger.exception(f"验证支付异常: {str(e)}")
            return False

    async def _process_payment_success(self, order_no: str, transaction_id: str, result: dict) -> dict:
        """
        处理支付成功的统一逻辑（回调和主动查询共用）

        Args:
            order_no: 订单号
            transaction_id: 微信交易号
            result: 微信返回的完整数据

        Returns:
            dict: 处理结果
        """
        # 1. 查询待支付订单
        pending = await get_pending_order(order_no)
        if not pending:
            logger.warning(f"待支付订单不存在: {order_no}")
            return {"success": False, "message": "待支付订单不存在", "order_no": order_no}

        # 2. 检查数据库订单状态
        order = await Order.filter(order_no=order_no).first()
        if not order:
            logger.error(f"订单不存在: {order_no}")
            return {"success": False, "message": "订单不存在", "order_no": order_no}

        if order.status != OrderStatus.PENDING:
            logger.warning(f"订单状态不是待支付: {order_no}, status={order.status}")
            return {"success": True, "message": "订单已处理", "order_no": order_no}

        # 3. 更新订单状态为已支付
        order.status = OrderStatus.PAID
        order.paid_at = datetime.now(UTC)
        order.payment_data = {
            "provider": self.provider_id,
            "transaction_id": transaction_id,
            **result,
        }
        await order.save()

        # 4. 记录支付日志
        amount_info = result.get("amount", {})
        amount_total = amount_info.get("total", 0)
        await OrderLog.create(
            order=order,
            action="payment",
            content=f"微信支付成功，交易ID: {transaction_id}，金额: {amount_total} 分",
        )

        # 5. 清理 Redis 数据
        await remove_pending_order(order_no)

        logger.info(f"订单支付完成: order_no={order_no}, transaction_id={transaction_id}")

        # 6. 发送支付成功邮件
        await EmailService.send_payment_success_email(
            to_email=order.email,
            order_no=order_no,
            total_price=str(order.total_price),
            currency=order.currency,
        )

        # 7. 检查是否启用虚拟商品自动发货
        if await DeliveryService.get_auto_delivery_enabled():
            success, message, count = await DeliveryService.auto_deliver_virtual_items(order)
            if success and count > 0:
                logger.info(f"虚拟商品自动发货成功: order_no={order_no}, count={count}")
            elif not success:
                logger.warning(f"虚拟商品自动发货失败: order_no={order_no}, message={message}")

        return {
            "success": True,
            "message": "支付成功",
            "order_no": order_no,
            "transaction_id": transaction_id,
        }

    async def handle_callback(self, data: dict) -> dict:
        """
        处理微信支付回调（兼容回调和主动查询）

        Args:
            data:
                - 回调模式: 包含 headers 和 body
                - 查询模式: 包含 source="query" 和 query_result

        Returns:
            dict: 包含 success, message, order_no 等信息
        """
        # 判断来源：主动查询 or 回调
        source = data.get("source", "callback")

        if source == "query":
            # === 主动查询模式 ===
            result = data.get("query_result", {})
            order_no = result.get("out_trade_no")
            trade_state = result.get("trade_state")
            transaction_id = result.get("transaction_id")

            if not order_no:
                return {"success": False, "message": "缺少订单号"}

            if trade_state != "SUCCESS":
                return {"success": False, "message": f"订单状态: {trade_state}", "order_no": order_no}

            logger.info(f"微信支付主动查询 - 订单号: {order_no}, 状态: {trade_state}")
            return await self._process_payment_success(order_no, transaction_id, result)

        else:
            # === 回调模式 ===
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

            # 5. 调用统一处理逻辑
            return await self._process_payment_success(order_no, transaction_id, result)

