"""数据库模型"""

from app.models.admin import Admin
from app.models.base import BaseModel, TimestampMixin
from app.models.order import Order, OrderItem, OrderLog
from app.models.platform import (
    Announcement,
    Banner,
    EmailConfig,
    FooterLink,
    PlatformConfig,
)
from app.models.product import (
    Category,
    InventoryItem,
    PaymentMethod,
    Product,
    ProductImage,
    ProductTag,
)

# 枚举从schemas导入
from app.schemas.order import OrderStatus
from app.schemas.platform import FooterLinkType
from app.schemas.product import FeeType, ProductType

__all__ = [
    # Base
    "BaseModel",
    "TimestampMixin",
    # Admin
    "Admin",
    # Platform
    "PlatformConfig",
    "EmailConfig",
    "Announcement",
    "Banner",
    "FooterLink",
    "FooterLinkType",
    # Product
    "Category",
    "PaymentMethod",
    "Product",
    "ProductImage",
    "ProductTag",
    "InventoryItem",
    "ProductType",
    "FeeType",
    # Order
    "Order",
    "OrderItem",
    "OrderLog",
    "OrderStatus",
]
