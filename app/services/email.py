"""邮件服务"""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.models.platform import EmailConfig

logger = logging.getLogger(__name__)


class EmailService:
    """邮件发送服务"""

    @staticmethod
    async def get_config() -> EmailConfig | None:
        """获取邮件配置"""
        return await EmailConfig.filter(is_verified=True).first()

    @classmethod
    async def send_email(
        cls,
        to_email: str,
        subject: str,
        html_content: str,
    ) -> bool:
        """
        发送邮件

        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            html_content: HTML内容

        Returns:
            是否发送成功
        """
        config = await cls.get_config()
        if not config:
            logger.warning("邮件配置不存在或未启用")
            return False

        try:
            message = MIMEMultipart("alternative")
            message["From"] = f"{config.from_name} <{config.from_email}>"
            message["To"] = to_email
            message["Subject"] = subject

            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)

            await aiosmtplib.send(
                message,
                hostname=config.smtp_host,
                port=config.smtp_port,
                username=config.smtp_user,
                password=config.smtp_password,
                use_tls=config.use_tls,
            )

            logger.info(f"邮件发送成功: {to_email}")
            return True

        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False

    @classmethod
    async def send_payment_pending_email(
        cls,
        to_email: str,
        order_no: str,
        total_price: str,
        currency: str,
        payment_data: dict,
    ) -> bool:
        """发送待支付订单通知邮件（含支付信息）"""
        subject = f"订单待支付 - {order_no}"

        # 构建支付信息
        payment_info = ""
        if payment_data.get("wallet_address"):
            payment_info = f"""
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin: 0 0 15px 0; color: #333;">支付信息</h3>
                <p><strong>支付金额：</strong>{payment_data.get('amount', total_price)} {payment_data.get('currency', 'USDT')}</p>
                <p><strong>收款地址：</strong></p>
                <p style="background: #fff; padding: 10px; border-radius: 4px; word-break: break-all; font-family: monospace;">
                    {payment_data.get('wallet_address')}
                </p>
                <p><strong>网络：</strong>{payment_data.get('network', 'TRC20')}</p>
                <p style="color: #dc3545; font-size: 14px;">
                    ⚠️ 请务必转账精确金额 {payment_data.get('amount', total_price)} USDT，否则可能无法自动确认支付
                </p>
            </div>
            """

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #333;">订单待支付</h2>
            <p>您的订单已创建成功，请在15分钟内完成支付：</p>
            <div style="background: #f0f0f0; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p><strong>订单号：</strong>{order_no}</p>
                <p><strong>订单金额：</strong>{currency} {total_price}</p>
            </div>
            {payment_info}
            <p style="color: #666; font-size: 14px;">如有问题请联系客服。</p>
        </body>
        </html>
        """
        return await cls.send_email(to_email, subject, html_content)

    @classmethod
    async def send_payment_success_email(
        cls,
        to_email: str,
        order_no: str,
        total_price: str,
        currency: str,
    ) -> bool:
        """发送支付成功通知邮件"""
        subject = f"支付成功 - {order_no}"
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #28a745;">支付成功</h2>
            <p>您的订单已支付成功：</p>
            <div style="background: #d4edda; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p><strong>订单号：</strong>{order_no}</p>
                <p><strong>支付金额：</strong>{currency} {total_price}</p>
            </div>
            <p>我们将尽快为您处理订单，请耐心等待。</p>
            <p style="color: #666; font-size: 14px;">如有问题请联系客服。</p>
        </body>
        </html>
        """
        return await cls.send_email(to_email, subject, html_content)

    @classmethod
    async def send_delivery_notification(
        cls,
        to_email: str,
        order_no: str,
        delivery_content: str,
    ) -> bool:
        """发送发货通知邮件"""
        subject = f"订单已发货 - {order_no}"
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #17a2b8;">订单已发货</h2>
            <p>您的订单 <strong>{order_no}</strong> 已发货，商品内容如下：</p>
            <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <pre style="white-space: pre-wrap; word-break: break-all; font-family: monospace; margin: 0;">{delivery_content}</pre>
            </div>
            <p style="color: #dc3545; font-size: 14px;">⚠️ 请妥善保管以上信息，切勿泄露给他人。</p>
            <p style="color: #666; font-size: 14px;">如有问题请联系客服。</p>
        </body>
        </html>
        """
        return await cls.send_email(to_email, subject, html_content)
