"""商品前台API"""

from fastapi import APIRouter, Query

from app.core.exceptions import NotFoundException
from app.core.logger import logger
from app.core.response import PaginatedData, ResponseModel, success_response
from app.models.product import Category, PaymentMethod, Product, ProductTag
from app.schemas.product import (
    CategoryResponse,
    CategoryTreeResponse,
    PaymentMethodResponse,
    ProductDetailResponse,
    ProductImageResponse,
    ProductIntroResponse,
    ProductListResponse,
    ProductTagResponse,
    ProductType,
)
from app.services.delivery import DeliveryService
from app.utils.common import paginate

router = APIRouter()


@router.get("/categories", response_model=ResponseModel, summary="获取分类树")
async def get_categories():
    logger.info("获取分类树")
    categories = await Category.filter(is_active=True, parent_id=None).order_by("sort_order")
    result = []
    for cat in categories:
        children = await Category.filter(is_active=True, parent_id=cat.id).order_by("sort_order")
        # 先构建子分类列表
        children_list = [
            CategoryTreeResponse(
                id=c.id,
                name=c.name,
                slug=c.slug,
                description=c.description,
                icon=c.icon,
                parent_id=getattr(c, "parent_id", None),
                sort_order=c.sort_order,
                is_active=c.is_active,
                created_at=c.created_at,
                updated_at=c.updated_at,
                children=[],
            )
            for c in children
        ]
        # 构建父分类
        cat_response = CategoryTreeResponse(
            id=cat.id,
            name=cat.name,
            slug=cat.slug,
            description=cat.description,
            icon=cat.icon,
            parent_id=getattr(cat, "parent_id", None),
            sort_order=cat.sort_order,
            is_active=cat.is_active,
            created_at=cat.created_at,
            updated_at=cat.updated_at,
            children=children_list,
        )
        result.append(cat_response)
    logger.info(f"获取到 {len(result)} 个顶级分类")
    return success_response(data=result)


@router.get("/categories/{slug}", response_model=ResponseModel, summary="获取分类详情")
async def get_category(slug: str):
    logger.info(f"获取分类详情: slug={slug}")
    category = await Category.filter(slug=slug, is_active=True).first()
    if not category:
        logger.warning(f"分类不存在: slug={slug}")
        raise NotFoundException(message="分类不存在")
    data = CategoryResponse.model_validate(category)
    return success_response(data=data)


@router.get("", response_model=ResponseModel, summary="获取商品列表")
async def get_products(
    category_slug: str | None = Query(None, description="分类别名"),
    search: str | None = Query(None, description="搜索关键词"),
    tags: str | None = Query(
        None,
        description="标签筛选，格式: key:value，多个用逗号分隔（AND关系）。例: platform:PC端,region:国服",
        examples=["platform:PC端", "platform:PC端,region:国服"],
    ),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """
    获取商品列表，支持分类、搜索、多标签组合筛选

    标签筛选说明：
    - 格式: `key:value`，多个标签用逗号分隔
    - 多个标签为 AND 关系（同时满足）
    - 示例: `?tags=platform:PC端,region:国服` 表示筛选平台为PC端且区服为国服的商品
    """
    logger.info(
        f"获取商品列表: category={category_slug}, search={search}, tags={tags}, page={page}"
    )
    query = Product.filter(is_active=True)

    if category_slug:
        category = await Category.filter(slug=category_slug).first()
        if category:
            child_ids = await Category.filter(parent_id=category.id).values_list("id", flat=True)
            category_ids = [category.id] + list(child_ids)
            query = query.filter(category_id__in=category_ids)

    if search:
        query = query.filter(name__icontains=search)

    # 多标签筛选（AND逻辑）
    if tags:
        tag_filters = []
        for tag_str in tags.split(","):
            tag_str = tag_str.strip()
            if ":" in tag_str:
                key, value = tag_str.split(":", 1)
                tag_filters.append((key.strip(), value.strip()))

        if tag_filters:
            # 找到同时包含所有指定标签的商品
            # 对每个标签条件，找出满足的商品ID，然后取交集
            product_ids_sets = []
            for key, value in tag_filters:
                ids = await ProductTag.filter(key=key, value=value).values_list(
                    "product_id", flat=True
                )
                product_ids_sets.append(set(ids))

            if product_ids_sets:
                # 取所有集合的交集
                matched_ids = product_ids_sets[0]
                for ids_set in product_ids_sets[1:]:
                    matched_ids = matched_ids & ids_set

                if matched_ids:
                    query = query.filter(id__in=list(matched_ids))
                else:
                    # 没有交集，返回空结果
                    return success_response(
                        data=PaginatedData(
                            items=[],
                            total=0,
                            page=page,
                            page_size=page_size,
                            pages=0,
                        )
                    )

    query = query.order_by("sort_order", "-created_at")
    items, total, pages = await paginate(query, page, page_size)

    result = []
    for item in items:
        await item.fetch_related("category", "images", "tags")
        item_dict = ProductListResponse.model_validate(item).model_dump()
        primary_image = next((img for img in item.images if img.is_primary), None)
        if not primary_image and item.images:
            primary_image = item.images[0]
        item_dict["primary_image"] = primary_image.image_url if primary_image else None
        # 列表中也返回标签
        item_dict["tags"] = [ProductTagResponse.model_validate(tag) for tag in item.tags]
        # 虚拟商品使用 InventoryItem 计算库存
        if item.product_type == ProductType.VIRTUAL:
            item_dict["stock"] = await DeliveryService.get_virtual_stock_count(item.id)
        result.append(item_dict)

    logger.info(f"获取到 {len(result)} 个商品, 共 {total} 条")
    data = PaginatedData(
        items=result,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )
    return success_response(data=data)


@router.get("/tags", response_model=ResponseModel, summary="获取所有标签")
async def get_tags():
    """获取所有商品标签，按key分组返回所有可选值"""
    logger.info("获取所有标签")
    # 只获取上架商品的标签
    tags = await ProductTag.filter(product__is_active=True).all()

    # 按key分组，去重value
    tag_map: dict[str, set[str]] = {}
    for tag in tags:
        if tag.key not in tag_map:
            tag_map[tag.key] = set()
        tag_map[tag.key].add(tag.value)

    # 转换为列表格式
    data = [{"key": k, "values": sorted(list(v))} for k, v in sorted(tag_map.items())]
    logger.info(f"获取到 {len(data)} 种标签")
    return success_response(data=data)


@router.get("/payment-methods", response_model=ResponseModel, summary="获取支付方式列表")
async def get_payment_methods():
    logger.info("获取支付方式列表")
    methods = await PaymentMethod.filter(is_active=True).order_by("sort_order")
    data = [PaymentMethodResponse.model_validate(m) for m in methods]
    logger.info(f"获取到 {len(data)} 个支付方式")
    return success_response(data=data)


@router.get("/{slug}", response_model=ResponseModel, summary="获取商品详情")
async def get_product(slug: str):
    logger.info(f"获取商品详情: slug={slug}")
    product = await Product.filter(slug=slug, is_active=True).first()
    if not product:
        logger.warning(f"商品不存在: slug={slug}")
        raise NotFoundException(message="商品不存在")

    await product.fetch_related("category", "images", "tags", "intros", "payment_methods")

    # 只获取启用的介绍内容
    active_intros = [intro for intro in product.intros if intro.is_active]
    active_intros.sort(key=lambda x: x.sort_order)

    # 虚拟商品使用 InventoryItem 计算库存
    stock = product.stock
    if product.product_type == ProductType.VIRTUAL:
        stock = await DeliveryService.get_virtual_stock_count(product.id)

    data = ProductDetailResponse(
        id=product.id,
        name=product.name,
        slug=product.slug,
        product_type=product.product_type,
        price=product.price,
        stock=stock,
        is_active=product.is_active,
        sort_order=product.sort_order,
        created_at=product.created_at,
        updated_at=product.updated_at,
        category=CategoryResponse.model_validate(product.category) if product.category else None,
        primary_image=next(
            (img.image_url for img in product.images if img.is_primary),
            product.images[0].image_url if product.images else None,
        ),
        images=[ProductImageResponse.model_validate(img) for img in product.images],
        tags=[ProductTagResponse.model_validate(tag) for tag in product.tags],
        intros=[ProductIntroResponse.model_validate(intro) for intro in active_intros],
        payment_methods=[
            PaymentMethodResponse.model_validate(pm)
            for pm in product.payment_methods
            if pm.is_active
        ],
    )
    return success_response(data=data)
