"""商品相关Schema"""

from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import Field

from app.schemas.common import BaseSchema, IDSchema, TimestampSchema


class ProductType(str, Enum):
    """
    商品类型

    - virtual: 虚拟商品（如卡密、激活码、会员等）
    - physical: 实体商品（需要物流配送）
    """

    VIRTUAL = "virtual"
    PHYSICAL = "physical"


class FeeType(str, Enum):
    """
    手续费类型

    - percentage: 百分比（如 3.5 表示 3.5%）
    - fixed: 固定金额（如 1.00 表示固定收取 1.00）
    """

    PERCENTAGE = "percentage"
    FIXED = "fixed"


# ==================== 分类 ====================
class CategoryBase(BaseSchema):
    """分类基础"""

    name: str = Field(..., max_length=100, description="分类名称", examples=["SIM卡"])
    slug: str = Field(
        ...,
        max_length=100,
        description="分类别名，用于URL，唯一",
        examples=["sim-card"],
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    description: str | None = Field(None, max_length=500, description="分类描述", examples=["各类SIM卡"])
    icon: str | None = Field(
        None,
        max_length=500,
        description="分类图标URL",
        examples=["https://example.com/icon.png"],
    )
    parent_id: int | None = Field(None, description="父分类ID，为空表示顶级分类")
    sort_order: int = Field(0, ge=0, description="排序值，越小越靠前")
    is_active: bool = Field(True, description="是否启用", examples=[True])


class CategoryCreate(CategoryBase):
    """创建分类"""

    pass


class CategoryUpdate(BaseSchema):
    """更新分类"""

    name: str | None = Field(None, description="分类名称")
    slug: str | None = Field(None, description="分类别名")
    description: str | None = Field(None, description="分类描述")
    icon: str | None = Field(None, description="分类图标URL")
    parent_id: int | None = Field(None, description="父分类ID")
    sort_order: int | None = Field(None, description="排序值")
    is_active: bool | None = Field(None, description="是否启用")


class CategoryResponse(IDSchema, TimestampSchema):
    """分类响应"""

    name: str = Field(..., description="分类名称")
    slug: str = Field(..., description="分类别名")
    description: str | None = Field(None, description="分类描述")
    icon: str | None = Field(None, description="分类图标URL")
    parent_id: int | None = Field(None, description="父分类ID")
    sort_order: int = Field(..., description="排序值")
    is_active: bool = Field(..., description="是否启用")


class CategoryTreeResponse(CategoryResponse):
    """分类树响应（含子分类）"""

    children: list["CategoryTreeResponse"] = Field(default_factory=list, description="子分类列表")


# ==================== 支付方式 ====================
class PaymentMethodBase(BaseSchema):
    """支付方式基础"""

    name: str = Field(..., max_length=100, description="支付方式名称", examples=["TRC20", "支付宝"])
    icon: str | None = Field(
        None,
        max_length=500,
        description="支付方式图标URL",
        examples=["https://example.com/alipay.png"],
    )
    fee_type: FeeType = Field(
        FeeType.PERCENTAGE,
        description="手续费类型: percentage=百分比, fixed=固定金额",
    )
    fee_value: Decimal = Field(
        Decimal("0"),
        ge=0,
        description="手续费值（小于1为百分比，大于等于1为固定金额）",
        examples=["0.35", "1.00"],
    )
    description: str | None = Field(None, description="支付方式说明", examples=["支持花呗、信用卡支付"])
    meta_data: dict[str, Any] = Field(
        default_factory=dict,
        description="支付配置元数据（如API密钥、商户ID等）",
        examples=[{"app_id": "xxx", "private_key": "xxx"}],
    )
    sort_order: int = Field(0, ge=0, description="排序值，越小越靠前")
    is_active: bool = Field(True, description="是否启用")


class PaymentMethodCreate(PaymentMethodBase):
    """创建支付方式"""

    pass


class PaymentMethodUpdate(BaseSchema):
    """更新支付方式"""

    name: str | None = Field(None, description="支付方式名称")
    icon: str | None = Field(None, description="图标URL")
    fee_type: FeeType | None = Field(None, description="手续费类型")
    fee_value: Decimal | None = Field(None, description="手续费值")
    description: str | None = Field(None, description="说明")
    meta_data: dict[str, Any] | None = Field(None, description="配置元数据")
    sort_order: int | None = Field(None, description="排序值")
    is_active: bool | None = Field(None, description="是否启用")


class PaymentMethodResponse(IDSchema, TimestampSchema):
    """支付方式响应（前台，不含敏感配置）"""

    name: str = Field(..., description="支付方式名称")
    icon: str | None = Field(None, description="图标URL")
    fee_type: FeeType = Field(..., description="手续费类型")
    fee_value: Decimal = Field(..., description="手续费值")
    description: str | None = Field(None, description="说明")
    sort_order: int = Field(..., description="排序值")
    is_active: bool = Field(..., description="是否启用")


class PaymentMethodAdminResponse(PaymentMethodResponse):
    """支付方式管理响应（含完整配置）"""

    meta_data: dict[str, Any] = Field(..., description="配置元数据")


# ==================== 商品图片 ====================
class ProductImageBase(BaseSchema):
    """商品图片基础"""

    image_url: str = Field(
        ...,
        max_length=500,
        description="图片URL",
        examples=["https://example.com/product1.jpg"],
    )
    sort_order: int = Field(0, ge=0, description="排序值，越小越靠前")
    is_primary: bool = Field(False, description="是否为主图（列表展示图）")


class ProductImageCreate(ProductImageBase):
    """创建商品图片"""

    pass


class ProductImageResponse(ProductImageBase, IDSchema):
    """商品图片响应"""

    pass


# ==================== 商品标签 ====================
class ProductTagBase(BaseSchema):
    """商品标签基础"""

    key: str = Field(..., max_length=100, description="标签键", examples=["地区", "国家"])
    value: str = Field(..., max_length=255, description="标签值", examples=["亚洲", "中国"])


class ProductTagCreate(ProductTagBase):
    """创建商品标签"""

    pass


class ProductTagResponse(ProductTagBase, IDSchema):
    """商品标签响应"""

    pass


# ==================== 商品介绍 ====================
class ProductIntroBase(BaseSchema):
    """商品介绍基础"""

    title: str = Field(
        ...,
        max_length=100,
        description="介绍标题（如: 商品信息/商品优势/使用教程/售后说明/购买须知/常见问题）",
        examples=["商品信息", "商品优势", "使用教程", "售后说明", "购买须知", "常见问题"],
    )
    content: str = Field(
        ...,
        description="介绍内容，支持HTML富文本",
        examples=["<h3>产品特点</h3><ul><li>特点1</li><li>特点2</li></ul>"],
    )
    icon: str | None = Field(
        None,
        max_length=255,
        description="图标（可选，用于前端展示）",
        examples=["info-circle", "https://example.com/icon.png"],
    )
    sort_order: int = Field(0, ge=0, description="排序值，越小越靠前")
    is_active: bool = Field(True, description="是否启用")


class ProductIntroCreate(ProductIntroBase):
    """创建商品介绍"""

    pass


class ProductIntroUpdate(BaseSchema):
    """更新商品介绍"""

    title: str | None = Field(None, description="介绍标题")
    content: str | None = Field(None, description="介绍内容")
    icon: str | None = Field(None, description="图标")
    sort_order: int | None = Field(None, description="排序值")
    is_active: bool | None = Field(None, description="是否启用")


class ProductIntroResponse(ProductIntroBase, IDSchema, TimestampSchema):
    """商品介绍响应"""

    pass


# ==================== 商品 ====================
class ProductBase(BaseSchema):
    """商品基础"""

    name: str = Field(..., max_length=255, description="商品名称", examples=["澳门 | 电信 | 大湾区预付卡（蓝卡）"])
    slug: str = Field(
        ...,
        max_length=255,
        description="商品别名，用于URL，唯一",
        examples=["macau-telecom-dabian-prepaid-card-blue"],
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    product_type: ProductType = Field(
        ProductType.VIRTUAL,
        description="商品类型: virtual=虚拟商品, physical=实体商品",
    )
    price: Decimal = Field(..., gt=0, description="商品价格", examples=["49.99"])
    stock: int = Field(0, ge=0, description="库存数量")
    category_id: int | None = Field(None, description="所属分类ID")
    is_active: bool = Field(True, description="是否上架")
    sort_order: int = Field(0, ge=0, description="排序值，越小越靠前")


class ProductCreate(ProductBase):
    """创建商品"""

    payment_method_ids: list[int] = Field(
        default_factory=list,
        description="支持的支付方式ID列表",
        examples=[[1, 2, 3]],
    )
    images: list[ProductImageCreate] = Field(default_factory=list, description="商品图片列表")
    tags: list[ProductTagCreate] = Field(default_factory=list, description="商品标签列表")
    intros: list[ProductIntroCreate] = Field(default_factory=list, description="商品介绍列表")
    inventory_contents: list[str] | None = Field(
        None,
        description="虚拟商品卡密列表（仅虚拟商品需要）",
        examples=[["CODE-0001", "CODE-0002", "CODE-0003"]],
    )


class ProductUpdate(BaseSchema):
    """更新商品"""

    name: str | None = Field(None, description="商品名称")
    slug: str | None = Field(None, description="商品别名")
    product_type: ProductType | None = Field(None, description="商品类型")
    price: Decimal | None = Field(None, description="商品价格")
    stock: int | None = Field(None, description="库存数量")
    category_id: int | None = Field(None, description="分类ID")
    is_active: bool | None = Field(None, description="是否上架")
    sort_order: int | None = Field(None, description="排序值")
    payment_method_ids: list[int] | None = Field(None, description="支付方式ID列表")
    images: list[ProductImageCreate] | None = Field(None, description="商品图片列表")
    tags: list[ProductTagCreate] | None = Field(None, description="商品标签列表")
    intros: list[ProductIntroCreate] | None = Field(None, description="商品介绍列表")


class ProductListResponse(IDSchema, TimestampSchema):
    """商品列表响应"""

    name: str = Field(..., description="商品名称")
    slug: str = Field(..., description="商品别名")
    product_type: ProductType = Field(..., description="商品类型")
    price: Decimal = Field(..., description="商品价格")
    stock: int = Field(..., description="库存数量")
    is_active: bool = Field(..., description="是否上架")
    category: CategoryResponse | None = Field(None, description="所属分类")
    primary_image: str | None = Field(None, description="商品主图URL")
    tags: list[ProductTagResponse] = Field(default_factory=list, description="商品标签列表")


class ProductDetailResponse(ProductListResponse):
    """商品详情响应"""

    sort_order: int = Field(..., description="排序值")
    images: list[ProductImageResponse] = Field(default_factory=list, description="图片列表")
    tags: list[ProductTagResponse] = Field(default_factory=list, description="标签列表")
    intros: list[ProductIntroResponse] = Field(default_factory=list, description="商品介绍列表")
    payment_methods: list[PaymentMethodResponse] = Field(default_factory=list, description="支持的支付方式")


# ==================== 库存项 ====================
class InventoryItemBase(BaseSchema):
    """库存项基础"""

    content: str = Field(..., description="库存内容（如卡密、激活码等）", examples=["XXXX-XXXX-XXXX-XXXX"])


class InventoryItemCreate(InventoryItemBase):
    """创建库存项"""

    pass


class InventoryItemBatchCreate(BaseSchema):
    """批量创建库存项"""

    contents: list[str] = Field(
        ...,
        min_length=1,
        description="库存内容列表",
        examples=[["CODE-0001", "CODE-0002", "CODE-0003"]],
    )


class InventoryItemResponse(InventoryItemBase, IDSchema, TimestampSchema):
    """库存项响应"""

    is_sold: bool = Field(..., description="是否已售出")
