"""管理后台API路由"""

from fastapi import APIRouter, Depends

from app.api.admin import auth, order, payment, platform, product
from app.core.deps import get_current_admin

router = APIRouter(prefix="/admin", tags=["管理后台"])

# 认证路由 (不需要登录)
router.include_router(auth.router, prefix="/auth", tags=["管理-认证"])

# 需要登录的路由
router.include_router(
    platform.router,
    prefix="/platform",
    tags=["管理-平台配置"],
    dependencies=[Depends(get_current_admin)],
)
router.include_router(
    product.router,
    prefix="/products",
    tags=["管理-商品"],
    dependencies=[Depends(get_current_admin)],
)
router.include_router(
    order.router,
    prefix="/orders",
    tags=["管理-订单"],
    dependencies=[Depends(get_current_admin)],
)
router.include_router(
    payment.router,
    prefix="/payment",
    tags=["管理-支付"],
    dependencies=[Depends(get_current_admin)],
)
