"""支付提供者注册表 - 插件管理"""

from app.core.logger import logger
from app.models.product import PaymentMethod
from app.services.payment.base import PaymentProvider

# 全局注册表实例
_registry: "PaymentRegistry | None" = None


class PaymentRegistry:
    """支付提供者注册表"""

    def __init__(self):
        # 提供者类注册 {provider_id: ProviderClass}
        self._provider_classes: dict[str, type[PaymentProvider]] = {}
        # 已启动的提供者实例 {provider_id: instance}
        self._active_providers: dict[str, PaymentProvider] = {}

    def register(self, provider_class: type[PaymentProvider]) -> type[PaymentProvider]:
        """
        注册支付提供者类

        可作为装饰器使用:
            @registry.register
            class TRC20Provider(PaymentProvider):
                ...
        """
        provider_id = provider_class.provider_id
        if not provider_id:
            raise ValueError(f"PaymentProvider {provider_class.__name__} 必须定义 provider_id")

        self._provider_classes[provider_id] = provider_class
        logger.info(f"支付提供者已注册: {provider_id} ({provider_class.provider_name})")
        return provider_class

    def get_provider_class(self, provider_id: str) -> type[PaymentProvider] | None:
        """获取提供者类"""
        return self._provider_classes.get(provider_id)

    def get_active_provider(self, provider_id: str) -> PaymentProvider | None:
        """获取已激活的提供者实例"""
        return self._active_providers.get(provider_id)

    def get_all_provider_ids(self) -> list[str]:
        """获取所有已注册的提供者ID"""
        return list(self._provider_classes.keys())

    def get_all_active_providers(self) -> list[PaymentProvider]:
        """获取所有已激活的提供者实例"""
        return list(self._active_providers.values())

    async def load_and_start_providers(self) -> None:
        """
        根据数据库配置加载并启动支付提供者

        只启动已配置且启用的支付方式对应的提供者
        """
        logger.info("开始加载支付提供者...")

        # 获取所有启用的支付方式
        payment_methods = await PaymentMethod.filter(is_active=True).all()
        logger.info(f"找到 {len(payment_methods)} 个启用的支付方式")

        for method in payment_methods:
            meta_data = method.meta_data or {}
            provider_id = meta_data.get("provider_id")

            if not provider_id:
                logger.debug(f"支付方式 {method.name} 未配置 provider_id，跳过")
                continue

            provider_class = self._provider_classes.get(provider_id)
            if not provider_class:
                logger.warning(f"未找到支付提供者: {provider_id}")
                continue

            # 如果已经启动，跳过
            if provider_id in self._active_providers:
                logger.debug(f"支付提供者 {provider_id} 已启动，跳过")
                continue

            try:
                # 创建实例
                provider = provider_class(meta_data)

                # 检查配置
                if not provider.is_configured():
                    logger.warning(f"支付提供者 {provider_id} 配置不完整，跳过")
                    continue

                # 启动
                await provider.start()
                provider._is_started = True
                self._active_providers[provider_id] = provider
                logger.info(f"支付提供者已启动: {provider_id}")

            except Exception as e:
                logger.error(f"启动支付提供者 {provider_id} 失败: {e}")

        logger.info(f"支付提供者加载完成，共启动 {len(self._active_providers)} 个")

    async def stop_all_providers(self) -> None:
        """停止所有已启动的支付提供者"""
        logger.info("开始停止所有支付提供者...")

        for provider_id, provider in list(self._active_providers.items()):
            try:
                await provider.stop()
                provider._is_started = False
                logger.info(f"支付提供者已停止: {provider_id}")
            except Exception as e:
                logger.error(f"停止支付提供者 {provider_id} 失败: {e}")

        self._active_providers.clear()
        logger.info("所有支付提供者已停止")

    async def reload_providers(self) -> None:
        """重新加载支付提供者（配置变更后调用）"""
        await self.stop_all_providers()
        await self.load_and_start_providers()


def get_registry() -> PaymentRegistry:
    """获取全局注册表实例"""
    global _registry
    if _registry is None:
        _registry = PaymentRegistry()
    return _registry


def register_provider(provider_class: type[PaymentProvider]) -> type[PaymentProvider]:
    """注册支付提供者的便捷装饰器"""
    return get_registry().register(provider_class)
