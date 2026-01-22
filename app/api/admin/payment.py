"""支付管理 API（后台）"""

from fastapi import APIRouter

from app.core.logger import logger
from app.core.response import ResponseModel, success_response
from app.services.payment.registry import get_registry
from app.utils.redis_client import (
    get_all_pending_orders,
    get_scan_logs,
    get_scan_logs_count,
)

router = APIRouter()


@router.get("/providers", response_model=ResponseModel, summary="获取支付提供者列表")
async def get_payment_providers():
    """获取所有已注册的支付提供者"""
    registry = get_registry()

    providers = []
    for provider_id in registry.get_all_provider_ids():
        provider_class = registry.get_provider_class(provider_id)
        active_provider = registry.get_active_provider(provider_id)

        providers.append(
            {
                "provider_id": provider_id,
                "name": provider_class.provider_name if provider_class else provider_id,
                "is_active": active_provider is not None,
                "is_started": active_provider.is_started if active_provider else False,
            }
        )

    return success_response(data=providers)


@router.get("/pending-orders", response_model=ResponseModel, summary="获取待支付订单列表")
async def get_pending_orders():
    """获取所有待支付订单（从 Redis）"""
    orders = await get_all_pending_orders()

    # 按创建时间倒序
    orders.sort(key=lambda x: x.get("created_at", 0), reverse=True)

    return success_response(data=orders)


@router.get("/scan-logs", response_model=ResponseModel, summary="获取扫描日志")
async def get_payment_scan_logs(limit: int = 50, offset: int = 0):
    """获取 TRC20 扫描日志"""
    logs = await get_scan_logs(limit=limit, offset=offset)
    total = await get_scan_logs_count()

    return success_response(
        data={
            "items": logs,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    )


@router.post("/reload", response_model=ResponseModel, summary="重新加载支付提供者")
async def reload_payment_providers():
    """重新加载支付提供者（配置变更后调用）"""
    logger.info("手动触发重新加载支付提供者")

    registry = get_registry()
    await registry.reload_providers()

    return success_response(message="支付提供者已重新加载")
