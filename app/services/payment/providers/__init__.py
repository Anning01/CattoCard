"""支付提供者模块"""

# 导入所有提供者以触发注册
from app.services.payment.providers.trc20 import TRC20Provider
from app.services.payment.providers.wechat import WechatProvider

__all__ = ["TRC20Provider", "WechatProvider"]
