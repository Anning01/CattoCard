"""V1 API路由"""

from fastapi import APIRouter

from app.api.v1 import order, payment, platform, product

router = APIRouter(prefix="/v1")

router.include_router(platform.router, prefix="/platform", tags=["平台配置"])
router.include_router(product.router, prefix="/products", tags=["商品"])
router.include_router(order.router, prefix="/orders", tags=["订单"])
router.include_router(payment.router, prefix="/payment", tags=["支付"])
