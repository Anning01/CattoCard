"""商品相关模型"""

from decimal import Decimal

from tortoise import fields

from app.models.base import BaseModel
from app.schemas.product import FeeType, ProductType


class Category(BaseModel):
    """商品分类(最多2层)"""

    name = fields.CharField(max_length=100, description="分类名称")
    slug = fields.CharField(max_length=100, unique=True, description="分类别名")
    description = fields.CharField(max_length=500, null=True, description="分类描述")
    icon = fields.CharField(max_length=500, null=True, description="分类图标")
    parent: fields.ForeignKeyNullableRelation["Category"] = fields.ForeignKeyField(
        "models.Category",
        related_name="children",
        null=True,
        on_delete=fields.SET_NULL,
        description="父分类",
    )
    sort_order = fields.IntField(default=0, description="排序")
    is_active = fields.BooleanField(default=True, description="是否启用")

    # 反向关系
    children: fields.ReverseRelation["Category"]
    products: fields.ReverseRelation["Product"]

    class Meta:
        table = "category"
        table_description = "商品分类表"
        ordering = ["sort_order"]


class PaymentMethod(BaseModel):
    """支付方式"""

    name = fields.CharField(max_length=100, description="支付名称")
    icon = fields.CharField(max_length=500, null=True, description="支付图标")
    fee_type = fields.CharEnumField(FeeType, default=FeeType.PERCENTAGE, description="手续费类型")
    fee_value = fields.DecimalField(
        max_digits=10, decimal_places=4, default=Decimal("0"), description="手续费值"
    )
    description = fields.TextField(null=True, description="支付描述")
    meta_data = fields.JSONField(default=dict, description="支付元数据配置")
    sort_order = fields.IntField(default=0, description="排序")
    is_active = fields.BooleanField(default=True, description="是否启用")

    # 反向关系
    products: fields.ManyToManyRelation["Product"]

    class Meta:
        table = "payment_method"
        table_description = "支付方式表"
        ordering = ["sort_order"]


class Product(BaseModel):
    """商品"""

    name = fields.CharField(max_length=255, description="商品名称")
    slug = fields.CharField(max_length=255, unique=True, description="商品别名")
    product_type = fields.CharEnumField(
        ProductType, default=ProductType.VIRTUAL, description="商品类型"
    )
    price = fields.DecimalField(max_digits=10, decimal_places=2, description="商品价格")
    stock = fields.IntField(default=0, description="库存数量")

    # 外键关系
    category: fields.ForeignKeyNullableRelation["Category"] = fields.ForeignKeyField(
        "models.Category",
        related_name="products",
        null=True,
        on_delete=fields.SET_NULL,
        description="商品分类",
    )

    # 多对多关系
    payment_methods: fields.ManyToManyRelation["PaymentMethod"] = fields.ManyToManyField(
        "models.PaymentMethod",
        related_name="products",
        through="product_payment_method",
        description="支付方式",
    )

    # 状态
    is_active = fields.BooleanField(default=True, description="是否上架")
    sort_order = fields.IntField(default=0, description="排序")

    # 反向关系
    images: fields.ReverseRelation["ProductImage"]
    tags: fields.ReverseRelation["ProductTag"]
    intros: fields.ReverseRelation["ProductIntro"]
    inventory_items: fields.ReverseRelation["InventoryItem"]

    class Meta:
        table = "product"
        table_description = "商品表"
        ordering = ["sort_order", "-created_at"]


class ProductImage(BaseModel):
    """商品图片"""

    product: fields.ForeignKeyRelation["Product"] = fields.ForeignKeyField(
        "models.Product",
        related_name="images",
        on_delete=fields.CASCADE,
        description="关联商品",
    )
    image_url = fields.CharField(max_length=500, description="图片URL")
    sort_order = fields.IntField(default=0, description="排序")
    is_primary = fields.BooleanField(default=False, description="是否主图")

    class Meta:
        table = "product_image"
        table_description = "商品图片表"
        ordering = ["sort_order"]


class ProductTag(BaseModel):
    """商品标签"""

    product: fields.ForeignKeyRelation["Product"] = fields.ForeignKeyField(
        "models.Product",
        related_name="tags",
        on_delete=fields.CASCADE,
        description="关联商品",
    )
    key = fields.CharField(max_length=100, description="标签键")
    value = fields.CharField(max_length=255, description="标签值")

    class Meta:
        table = "product_tag"
        table_description = "商品标签表"


class ProductIntro(BaseModel):
    """商品介绍内容（一对多，支持多种类型的介绍）

    可用于：商品信息、商品优势、使用教程、售后说明等
    不同商品可以有不同的介绍类型，灵活配置
    """

    product: fields.ForeignKeyRelation["Product"] = fields.ForeignKeyField(
        "models.Product",
        related_name="intros",
        on_delete=fields.CASCADE,
        description="关联商品",
    )
    title = fields.CharField(
        max_length=100, description="介绍标题(如: 商品信息/商品优势/使用教程/售后说明)"
    )
    content = fields.TextField(description="介绍内容(富文本HTML)")
    icon = fields.CharField(max_length=255, null=True, description="图标(可选)")
    sort_order = fields.IntField(default=0, description="排序")
    is_active = fields.BooleanField(default=True, description="是否启用")

    class Meta:
        table = "product_intro"
        table_description = "商品介绍内容表"
        ordering = ["sort_order"]


class InventoryItem(BaseModel):
    """虚拟商品库存项(卡密等)"""

    product: fields.ForeignKeyRelation["Product"] = fields.ForeignKeyField(
        "models.Product",
        related_name="inventory_items",
        on_delete=fields.CASCADE,
        description="关联商品",
    )
    content = fields.TextField(description="库存内容(卡密等)")
    is_sold = fields.BooleanField(default=False, description="是否已售出")
    sold_at = fields.DatetimeField(null=True, description="售出时间")

    class Meta:
        table = "inventory_item"
        table_description = "虚拟商品库存项表"
