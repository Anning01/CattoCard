"""订单相关Schema"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import EmailStr, Field

from app.schemas.common import BaseSchema, IDSchema, TimestampSchema
from app.schemas.product import ProductType


class OrderStatus(str, Enum):
    """
    订单状态

    - pending: 待支付（订单已创建，等待用户支付）
    - paid: 已支付（用户已完成支付，等待发货）
    - processing: 处理中（订单正在处理，如实体商品发货中）
    - completed: 已完成（订单已完成，虚拟商品已发货或实体商品已签收）
    - cancelled: 已取消（订单被取消，库存已恢复）
    - refunded: 已退款（订单已退款）
    """

    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


# ==================== 订单商品项 ====================
class OrderItemCreate(BaseSchema):
    """创建订单商品项"""

    product_id: int = Field(..., description="商品ID")
    quantity: int = Field(1, gt=0, description="购买数量")


class OrderItemResponse(IDSchema):
    """订单商品项响应"""

    product_id: int = Field(..., description="商品ID")
    product_name: str = Field(..., description="商品名称（下单时快照）")
    product_type: ProductType = Field(..., description="商品类型")
    quantity: int = Field(..., description="购买数量")
    price: Decimal = Field(..., description="商品单价（下单时价格）")
    subtotal: Decimal = Field(..., description="小计金额")
    delivery_content: str | None = Field(None, description="发货内容（卡密等，仅订单完成后可见）")
    delivered_at: datetime | None = Field(None, description="发货时间")


# ==================== 订单 ====================
class OrderCreate(BaseSchema):
    """创建订单"""

    email: EmailStr = Field(
        ..., description="下单邮箱（用于接收订单通知）", examples=["user@example.com"]
    )
    items: list[OrderItemCreate] = Field(..., min_length=1, description="订单商品列表")
    payment_method_id: int = Field(..., description="支付方式ID")
    currency: str = Field("USD", max_length=10, description="结算币种", examples=["USD", "CNY"])
    # 实体商品收货信息
    shipping_name: str | None = Field(None, max_length=100, description="收货人姓名")
    shipping_phone: str | None = Field(None, max_length=50, description="收货人电话")
    shipping_address: str | None = Field(None, description="收货地址")
    remark: str | None = Field(None, description="订单备注")


class OrderUpdate(BaseSchema):
    """更新订单（管理后台）"""

    status: OrderStatus | None = Field(None, description="订单状态")
    shipping_name: str | None = Field(None, description="收货人姓名")
    shipping_phone: str | None = Field(None, description="收货人电话")
    shipping_address: str | None = Field(None, description="收货地址")
    remark: str | None = Field(None, description="订单备注")


class OrderListResponse(IDSchema, TimestampSchema):
    """订单列表响应"""

    order_no: str = Field(..., description="订单号", examples=["CS1704067200000ABC123"])
    status: OrderStatus = Field(..., description="订单状态")
    email: str = Field(..., description="下单邮箱")
    currency: str = Field(..., description="结算币种")
    total_price: Decimal = Field(..., description="订单总价（含手续费）")
    paid_at: datetime | None = Field(None, description="支付时间")
    # 收货信息（实体商品）
    shipping_name: str | None = Field(None, description="收货人姓名")
    shipping_phone: str | None = Field(None, description="收货人电话")
    shipping_address: str | None = Field(None, description="收货地址")


class OrderDetailResponse(OrderListResponse):
    """订单详情响应"""

    payment_method_id: int | None = Field(None, description="支付方式ID")
    shipping_name: str | None = Field(None, description="收货人姓名")
    shipping_phone: str | None = Field(None, description="收货人电话")
    shipping_address: str | None = Field(None, description="收货地址")
    remark: str | None = Field(None, description="订单备注")
    items: list[OrderItemResponse] = Field(default_factory=list, description="订单商品列表")


class OrderQueryByEmail(BaseSchema):
    """通过邮箱查询订单"""

    email: EmailStr = Field(..., description="下单邮箱")
    order_no: str | None = Field(None, description="订单号（可选，用于精确查询）")


# ==================== 订单日志 ====================
class OrderLogResponse(IDSchema, TimestampSchema):
    """订单日志响应"""

    action: str = Field(
        ...,
        description="操作类型: create=创建, status_change=状态变更, deliver=发货, cancel=取消",
        examples=["create", "status_change", "deliver"],
    )
    content: str | None = Field(None, description="日志内容")
    operator: str | None = Field(None, description="操作人")


# ==================== 支付 ====================
class PaymentInitRequest(BaseSchema):
    """支付初始化请求"""

    order_no: str = Field(..., description="订单号")


class PaymentInitResponse(BaseSchema):
    """支付初始化响应"""

    payment_url: str | None = Field(None, description="支付跳转URL")
    payment_data: dict[str, Any] = Field(
        default_factory=dict, description="支付相关数据（如二维码内容等）"
    )
    expires_in: int = Field(900, description="支付过期时间（秒），默认15分钟")


class PaymentCallbackData(BaseSchema):
    """支付回调数据"""

    order_no: str = Field(..., description="订单号")
    status: str = Field(..., description="支付状态: success=成功, failed=失败")
    raw_data: dict[str, Any] = Field(default_factory=dict, description="原始回调数据")
