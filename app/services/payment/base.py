"""支付服务基类"""

from abc import ABC, abstractmethod
from typing import Any


class PaymentResult:
    """支付结果"""

    def __init__(
        self,
        success: bool,
        payment_url: str | None = None,
        payment_data: dict | None = None,
        error_message: str | None = None,
    ):
        self.success = success
        self.payment_url = payment_url
        self.payment_data = payment_data or {}
        self.error_message = error_message


class PaymentProvider(ABC):
    """支付提供者基类 - 插件架构"""

    # 提供者标识符，子类必须覆盖
    provider_id: str = ""
    # 提供者名称
    provider_name: str = ""

    def __init__(self, config: dict[str, Any]):
        """
        初始化支付提供者

        Args:
            config: 支付方式的 meta_data 配置
        """
        self.config = config
        self._is_started = False

    @abstractmethod
    async def start(self) -> None:
        """
        启动支付提供者

        在这里初始化后台任务、连接等资源。
        只有配置了此支付方式时才会被调用。
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """
        停止支付提供者

        在这里清理后台任务、关闭连接等。
        """
        pass

    @abstractmethod
    async def create_payment(self, order_no: str, amount: str, currency: str) -> PaymentResult:
        """
        创建支付

        Args:
            order_no: 订单号
            amount: 支付金额
            currency: 货币类型

        Returns:
            PaymentResult: 支付创建结果
        """
        pass

    @abstractmethod
    async def verify_payment(self, order_no: str, payment_data: dict) -> bool:
        """
        验证支付是否完成

        Args:
            order_no: 订单号
            payment_data: 支付相关数据

        Returns:
            bool: 支付是否已完成
        """
        pass

    async def handle_callback(self, data: dict) -> dict:
        """
        处理支付回调

        Args:
            data: 回调数据

        Returns:
            dict: 处理结果
        """
        return {"success": False, "message": "此支付方式不支持回调"}

    def is_configured(self) -> bool:
        """
        检查是否已正确配置

        子类可以覆盖此方法来定义自己的配置验证逻辑
        """
        return True

    @property
    def is_started(self) -> bool:
        """是否已启动"""
        return self._is_started
