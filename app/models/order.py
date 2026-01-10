"""订单相关模型"""

from __future__ import annotations

import time
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from tortoise import fields

from app.models.base import BaseModel
from app.schemas.order import OrderStatus
from app.schemas.product import ProductType

if TYPE_CHECKING:
    from app.models.product import PaymentMethod, Product


class Order(BaseModel):
    """订单"""

    order_no = fields.CharField(
        max_length=64, unique=True, description="订单号", default=""
    )
    status = fields.CharEnumField(
        OrderStatus, default=OrderStatus.PENDING, description="订单状态"
    )
    email = fields.CharField(max_length=255, description="下单邮箱")
    currency = fields.CharField(max_length=10, default="USD", description="结算币种")
    total_price = fields.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0"), description="订单总价"
    )

    # 支付信息
    payment_method: fields.ForeignKeyNullableRelation[PaymentMethod] = fields.ForeignKeyField(
        "models.PaymentMethod",
        related_name="orders",
        null=True,
        on_delete=fields.SET_NULL,
        description="支付方式",
    )
    paid_at = fields.DatetimeField(null=True, description="支付时间")
    payment_data = fields.JSONField(default=dict, description="支付回调数据")

    # 收货信息(实体商品)
    shipping_name = fields.CharField(max_length=100, null=True, description="收货人姓名")
    shipping_phone = fields.CharField(max_length=50, null=True, description="收货人电话")
    shipping_address = fields.TextField(null=True, description="收货地址")

    # 备注
    remark = fields.TextField(null=True, description="订单备注")

    # 反向关系
    items: fields.ReverseRelation[OrderItem]

    class Meta:
        table = "order"
        table_description = "订单表"
        ordering = ["-created_at"]

    @staticmethod
    def generate_order_no() -> str:
        """生成订单号"""
        timestamp = int(time.time() * 1000)
        unique_id = uuid.uuid4().hex[:8].upper()
        return f"CS{timestamp}{unique_id}"

    async def save(self, *args, **kwargs):
        if not self.order_no:
            self.order_no = self.generate_order_no()
        await super().save(*args, **kwargs)


class OrderItem(BaseModel):
    """订单商品项"""

    order: fields.ForeignKeyRelation[Order] = fields.ForeignKeyField(
        "models.Order",
        related_name="items",
        on_delete=fields.CASCADE,
        description="关联订单",
    )
    product: fields.ForeignKeyRelation[Product] = fields.ForeignKeyField(
        "models.Product",
        related_name="order_items",
        on_delete=fields.RESTRICT,
        description="关联商品",
    )
    product_name = fields.CharField(max_length=255, description="商品名称(快照)")
    product_type = fields.CharEnumField(
        ProductType, default=ProductType.VIRTUAL, description="商品类型(快照)"
    )
    quantity = fields.IntField(default=1, description="购买数量")
    price = fields.DecimalField(
        max_digits=10, decimal_places=2, description="商品单价(下单时价格)"
    )
    subtotal = fields.DecimalField(
        max_digits=10, decimal_places=2, description="小计金额"
    )

    # 虚拟商品发货内容
    delivery_content = fields.TextField(null=True, description="发货内容(卡密等)")
    delivered_at = fields.DatetimeField(null=True, description="发货时间")

    class Meta:
        table = "order_item"
        table_description = "订单商品项表"

    def calculate_subtotal(self):
        """计算小计金额"""
        self.subtotal = self.price * self.quantity


class OrderLog(BaseModel):
    """订单日志"""

    order: fields.ForeignKeyRelation[Order] = fields.ForeignKeyField(
        "models.Order",
        related_name="logs",
        on_delete=fields.CASCADE,
        description="关联订单",
    )
    action = fields.CharField(max_length=50, description="操作类型")
    content = fields.TextField(null=True, description="日志内容")
    operator = fields.CharField(max_length=100, null=True, description="操作人")

    class Meta:
        table = "order_log"
        table_description = "订单日志表"
        ordering = ["-created_at"]
