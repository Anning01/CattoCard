"""商品管理API"""

from fastapi import APIRouter, Query

from app.core.exceptions import BadRequestException, NotFoundException
from app.core.logger import logger
from app.core.response import PaginatedData, ResponseModel, success_response
from app.models.product import (
    Category,
    InventoryItem,
    PaymentMethod,
    Product,
    ProductImage,
    ProductIntro,
    ProductTag,
)
from app.schemas.product import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    InventoryItemBatchCreate,
    InventoryItemResponse,
    PaymentMethodAdminResponse,
    PaymentMethodCreate,
    PaymentMethodResponse,
    PaymentMethodUpdate,
    ProductCreate,
    ProductDetailResponse,
    ProductImageResponse,
    ProductIntroCreate,
    ProductIntroResponse,
    ProductIntroUpdate,
    ProductListResponse,
    ProductTagResponse,
    ProductUpdate,
)
from app.utils.common import paginate
from app.utils.cache import get_tag_suggestions, update_tag_suggestions
from app.services.delivery import DeliveryService

router = APIRouter()


# ==================== 标签建议 ====================
@router.get("/tags/suggestions", response_model=ResponseModel, summary="获取标签建议")
async def get_tag_suggestions_api():
    """获取常用标签建议（key -> [values]）"""
    logger.info("获取标签建议")
    data = await get_tag_suggestions()
    return success_response(data=data)


# ==================== 分类管理 ====================
@router.get("/categories", response_model=ResponseModel, summary="获取所有分类")
async def get_categories():
    logger.info("获取所有分类(管理)")
    categories = await Category.all().order_by("sort_order")
    data = [CategoryResponse.model_validate(c) for c in categories]
    return success_response(data=data)


@router.post("/categories", response_model=ResponseModel, summary="创建分类")
async def create_category(data: CategoryCreate):
    logger.info(f"创建分类: name={data.name}, slug={data.slug}")
    if await Category.filter(slug=data.slug).exists():
        raise BadRequestException(message="分类别名已存在")

    if data.parent_id:
        parent = await Category.filter(id=data.parent_id).first()
        if not parent:
            raise BadRequestException(message="父分类不存在")
        if parent.parent_id:
            raise BadRequestException(message="只支持两级分类")

    category = await Category.create(**data.model_dump())
    logger.info(f"分类创建成功: id={category.id}")
    return success_response(data=CategoryResponse.model_validate(category))


@router.put("/categories/{category_id}", response_model=ResponseModel, summary="更新分类")
async def update_category(category_id: int, data: CategoryUpdate):
    logger.info(f"更新分类: id={category_id}")
    category = await Category.filter(id=category_id).first()
    if not category:
        raise NotFoundException(message="分类不存在")

    update_data = data.model_dump(exclude_unset=True)

    if "slug" in update_data:
        exists = await Category.filter(slug=update_data["slug"]).exclude(id=category_id).exists()
        if exists:
            raise BadRequestException(message="分类别名已存在")

    if "parent_id" in update_data and update_data["parent_id"]:
        parent = await Category.filter(id=update_data["parent_id"]).first()
        if not parent:
            raise BadRequestException(message="父分类不存在")
        if parent.parent_id:
            raise BadRequestException(message="只支持两级分类")

    await category.update_from_dict(update_data).save()
    logger.info(f"分类更新成功: id={category_id}")
    return success_response(data=CategoryResponse.model_validate(category))


@router.delete("/categories/{category_id}", response_model=ResponseModel, summary="删除分类")
async def delete_category(category_id: int):
    logger.info(f"删除分类: id={category_id}")
    category = await Category.filter(id=category_id).first()
    if not category:
        raise NotFoundException(message="分类不存在")

    if await Category.filter(parent_id=category_id).exists():
        raise BadRequestException(message="请先删除子分类")

    if await Product.filter(category_id=category_id).exists():
        raise BadRequestException(message="分类下有商品，无法删除")

    await category.delete()
    logger.info(f"分类删除成功: id={category_id}")
    return success_response(message="删除成功")


# ==================== 支付方式管理 ====================
@router.get("/payment-methods", response_model=ResponseModel, summary="获取所有支付方式")
async def get_payment_methods():
    logger.info("获取所有支付方式(管理)")
    methods = await PaymentMethod.all().order_by("sort_order")
    data = [PaymentMethodAdminResponse.model_validate(m) for m in methods]
    return success_response(data=data)


@router.post("/payment-methods", response_model=ResponseModel, summary="创建支付方式")
async def create_payment_method(data: PaymentMethodCreate):
    logger.info(f"创建支付方式: name={data.name}")
    method = await PaymentMethod.create(**data.model_dump())
    logger.info(f"支付方式创建成功: id={method.id}")
    return success_response(data=PaymentMethodAdminResponse.model_validate(method))


@router.put("/payment-methods/{method_id}", response_model=ResponseModel, summary="更新支付方式")
async def update_payment_method(method_id: int, data: PaymentMethodUpdate):
    logger.info(f"更新支付方式: id={method_id}")
    method = await PaymentMethod.filter(id=method_id).first()
    if not method:
        raise NotFoundException(message="支付方式不存在")
    update_data = data.model_dump(exclude_unset=True)
    await method.update_from_dict(update_data).save()
    logger.info(f"支付方式更新成功: id={method_id}")
    return success_response(data=PaymentMethodAdminResponse.model_validate(method))


@router.delete("/payment-methods/{method_id}", response_model=ResponseModel, summary="删除支付方式")
async def delete_payment_method(method_id: int):
    logger.info(f"删除支付方式: id={method_id}")
    deleted = await PaymentMethod.filter(id=method_id).delete()
    if not deleted:
        raise NotFoundException(message="支付方式不存在")
    logger.info(f"支付方式删除成功: id={method_id}")
    return success_response(message="删除成功")


@router.get("/payment-methods/trc20/scan-logs", response_model=ResponseModel, summary="获取TRC20扫描日志")
async def get_trc20_scan_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """获取 TRC20 支付扫描日志"""
    from app.utils.redis_client import get_scan_logs, get_scan_logs_count
    
    logger.info(f"获取TRC20扫描日志: limit={limit}, offset={offset}")
    logs = await get_scan_logs(limit=limit, offset=offset)
    total = await get_scan_logs_count()
    
    return success_response(data={
        "logs": logs,
        "total": total,
        "limit": limit,
        "offset": offset,
    })


# ==================== 商品管理 ====================
async def _get_product_detail(product_id: int) -> ProductDetailResponse:
    product = await Product.filter(id=product_id).first()
    if not product:
        raise NotFoundException(message="商品不存在")

    await product.fetch_related("category", "images", "tags", "intros", "payment_methods")

    return ProductDetailResponse(
        id=product.id,
        name=product.name,
        slug=product.slug,
        product_type=product.product_type,
        price=product.price,
        stock=product.stock,
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
        intros=[ProductIntroResponse.model_validate(intro) for intro in product.intros],
        payment_methods=[PaymentMethodResponse.model_validate(pm) for pm in product.payment_methods],
    )


@router.get("", response_model=ResponseModel, summary="获取商品列表")
async def get_products(
    category_id: int | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    logger.info(f"获取商品列表(管理): category_id={category_id}, is_active={is_active}")
    query = Product.all()

    if category_id:
        query = query.filter(category_id=category_id)
    if is_active is not None:
        query = query.filter(is_active=is_active)
    if search:
        query = query.filter(name__icontains=search)

    query = query.order_by("sort_order", "-created_at")
    items, total, pages = await paginate(query, page, page_size)

    result = []
    for item in items:
        await item.fetch_related("category", "images", "tags")
        primary_image = next((img for img in item.images if img.is_primary), None)
        if not primary_image and item.images:
            primary_image = item.images[0]

        item_dict = ProductListResponse(
            id=item.id,
            name=item.name,
            slug=item.slug,
            product_type=item.product_type,
            price=item.price,
            stock=item.stock,
            is_active=item.is_active,
            created_at=item.created_at,
            updated_at=item.updated_at,
            category=CategoryResponse.model_validate(item.category) if item.category else None,
            primary_image=primary_image.image_url if primary_image else None,
            tags=[ProductTagResponse.model_validate(tag) for tag in item.tags],
        ).model_dump()
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


@router.get("/{product_id}", response_model=ResponseModel, summary="获取商品详情")
async def get_product(product_id: int):
    logger.info(f"获取商品详情(管理): id={product_id}")
    data = await _get_product_detail(product_id)
    return success_response(data=data)


@router.post("", response_model=ResponseModel, summary="创建商品")
async def create_product(data: ProductCreate):
    logger.info(f"创建商品: name={data.name}, slug={data.slug}")
    if await Product.filter(slug=data.slug).exists():
        raise BadRequestException(message="商品别名已存在")

    if data.category_id:
        if not await Category.filter(id=data.category_id).exists():
            raise BadRequestException(message="分类不存在")

    payment_methods = []
    for pm_id in data.payment_method_ids:
        pm = await PaymentMethod.filter(id=pm_id).first()
        if not pm:
            raise BadRequestException(message=f"支付方式ID {pm_id} 不存在")
        payment_methods.append(pm)

    product_data = data.model_dump(exclude={"payment_method_ids", "images", "tags", "intros", "inventory_contents"})
    product = await Product.create(**product_data)

    await product.payment_methods.add(*payment_methods)

    for img_data in data.images:
        await ProductImage.create(product=product, **img_data.model_dump())

    for tag_data in data.tags:
        await ProductTag.create(product=product, **tag_data.model_dump())

    # 更新标签建议缓存
    if data.tags:
        await update_tag_suggestions([t.model_dump() for t in data.tags])

    for intro_data in data.intros:
        await ProductIntro.create(product=product, **intro_data.model_dump())

    # 创建虚拟商品卡密
    if data.product_type == "virtual" and data.inventory_contents:
        for content in data.inventory_contents:
            await InventoryItem.create(product=product, content=content)
        # 更新库存数量
        product.stock = len(data.inventory_contents)
        await product.save()
        logger.info(f"已添加 {len(data.inventory_contents)} 条卡密")

    logger.info(f"商品创建成功: id={product.id}")
    response_data = await _get_product_detail(product.id)
    return success_response(data=response_data)


@router.put("/{product_id}", response_model=ResponseModel, summary="更新商品")
async def update_product(product_id: int, data: ProductUpdate):
    logger.info(f"更新商品: id={product_id}")
    product = await Product.filter(id=product_id).first()
    if not product:
        raise NotFoundException(message="商品不存在")

    update_data = data.model_dump(exclude_unset=True, exclude={"payment_method_ids", "images", "tags", "intros"})

    if "slug" in update_data:
        exists = await Product.filter(slug=update_data["slug"]).exclude(id=product_id).exists()
        if exists:
            raise BadRequestException(message="商品别名已存在")

    if "category_id" in update_data and update_data["category_id"]:
        if not await Category.filter(id=update_data["category_id"]).exists():
            raise BadRequestException(message="分类不存在")

    await product.update_from_dict(update_data).save()

    # 更新支付方式
    if data.payment_method_ids is not None:
        await product.payment_methods.clear()
        payment_methods = []
        for pm_id in data.payment_method_ids:
            pm = await PaymentMethod.filter(id=pm_id).first()
            if pm:
                payment_methods.append(pm)
        await product.payment_methods.add(*payment_methods)

    # 更新商品图片
    if data.images is not None:
        await ProductImage.filter(product_id=product_id).delete()
        for img_data in data.images:
            await ProductImage.create(product=product, **img_data.model_dump())

    # 更新商品标签
    if data.tags is not None:
        await ProductTag.filter(product_id=product_id).delete()
        for tag_data in data.tags:
            await ProductTag.create(product=product, **tag_data.model_dump())
        # 更新标签建议缓存
        if data.tags:
            await update_tag_suggestions([t.model_dump() for t in data.tags])

    # 更新商品介绍
    if data.intros is not None:
        await ProductIntro.filter(product_id=product_id).delete()
        for intro_data in data.intros:
            await ProductIntro.create(product=product, **intro_data.model_dump())

    logger.info(f"商品更新成功: id={product_id}")
    response_data = await _get_product_detail(product_id)
    return success_response(data=response_data)


@router.delete("/{product_id}", response_model=ResponseModel, summary="删除商品")
async def delete_product(product_id: int):
    logger.info(f"删除商品: id={product_id}")
    product = await Product.filter(id=product_id).first()
    if not product:
        raise NotFoundException(message="商品不存在")
    await product.delete()
    logger.info(f"商品删除成功: id={product_id}")
    return success_response(message="删除成功")


# ==================== 库存管理(虚拟商品) ====================
@router.get("/{product_id}/inventory/stats", response_model=ResponseModel, summary="获取虚拟商品库存统计")
async def get_inventory_stats(product_id: int):
    """获取虚拟商品的库存统计（可用数量、已售数量）"""
    logger.info(f"获取库存统计: product_id={product_id}")
    product = await Product.filter(id=product_id).first()
    if not product:
        raise NotFoundException(message="商品不存在")

    available = await DeliveryService.get_virtual_stock_count(product_id)
    sold = await InventoryItem.filter(product_id=product_id, is_sold=True).count()
    total = available + sold

    return success_response(data={
        "available": available,
        "sold": sold,
        "total": total,
    })


@router.get("/{product_id}/inventory", response_model=ResponseModel, summary="获取商品库存")
async def get_inventory(
    product_id: int,
    is_sold: bool | None = None,
):
    logger.info(f"获取商品库存: product_id={product_id}, is_sold={is_sold}")
    product = await Product.filter(id=product_id).first()
    if not product:
        raise NotFoundException(message="商品不存在")

    query = InventoryItem.filter(product_id=product_id)
    if is_sold is not None:
        query = query.filter(is_sold=is_sold)

    items = await query.order_by("-created_at")
    data = [InventoryItemResponse.model_validate(item) for item in items]
    logger.info(f"获取到 {len(data)} 条库存")
    return success_response(data=data)


@router.post("/{product_id}/inventory", response_model=ResponseModel, summary="批量添加库存")
async def add_inventory(product_id: int, data: InventoryItemBatchCreate):
    logger.info(f"批量添加库存: product_id={product_id}, count={len(data.contents)}")
    product = await Product.filter(id=product_id).first()
    if not product:
        raise NotFoundException(message="商品不存在")

    for content in data.contents:
        await InventoryItem.create(product=product, content=content)

    unsold_count = await InventoryItem.filter(product_id=product_id, is_sold=False).count()
    product.stock = unsold_count
    await product.save()

    logger.info(f"成功添加 {len(data.contents)} 条库存, 当前库存: {unsold_count}")
    return success_response(message=f"成功添加 {len(data.contents)} 条库存")


@router.delete("/{product_id}/inventory/{item_id}", response_model=ResponseModel, summary="删除库存项")
async def delete_inventory(product_id: int, item_id: int):
    logger.info(f"删除库存项: product_id={product_id}, item_id={item_id}")
    item = await InventoryItem.filter(id=item_id, product_id=product_id).first()
    if not item:
        raise NotFoundException(message="库存项不存在")
    if item.is_sold:
        raise BadRequestException(message="已售出的库存项无法删除")

    await item.delete()

    unsold_count = await InventoryItem.filter(product_id=product_id, is_sold=False).count()
    product = await Product.filter(id=product_id).first()
    if product:
        product.stock = unsold_count
        await product.save()

    logger.info(f"库存项删除成功: id={item_id}")
    return success_response(message="删除成功")


# ==================== 商品介绍管理 ====================
@router.get("/{product_id}/intros", response_model=ResponseModel, summary="获取商品介绍列表")
async def get_product_intros(product_id: int):
    """获取指定商品的所有介绍内容"""
    logger.info(f"获取商品介绍: product_id={product_id}")
    product = await Product.filter(id=product_id).first()
    if not product:
        raise NotFoundException(message="商品不存在")

    intros = await ProductIntro.filter(product_id=product_id).order_by("sort_order")
    data = [ProductIntroResponse.model_validate(intro) for intro in intros]
    logger.info(f"获取到 {len(data)} 条商品介绍")
    return success_response(data=data)


@router.post("/{product_id}/intros", response_model=ResponseModel, summary="添加商品介绍")
async def create_product_intro(product_id: int, data: ProductIntroCreate):
    """为商品添加新的介绍内容（如：商品信息、商品优势、使用教程、售后说明等）"""
    logger.info(f"添加商品介绍: product_id={product_id}, title={data.title}")
    product = await Product.filter(id=product_id).first()
    if not product:
        raise NotFoundException(message="商品不存在")

    intro = await ProductIntro.create(product=product, **data.model_dump())
    logger.info(f"商品介绍添加成功: id={intro.id}")
    return success_response(data=ProductIntroResponse.model_validate(intro))


@router.put("/{product_id}/intros/{intro_id}", response_model=ResponseModel, summary="更新商品介绍")
async def update_product_intro(product_id: int, intro_id: int, data: ProductIntroUpdate):
    """更新商品介绍内容"""
    logger.info(f"更新商品介绍: product_id={product_id}, intro_id={intro_id}")
    intro = await ProductIntro.filter(id=intro_id, product_id=product_id).first()
    if not intro:
        raise NotFoundException(message="商品介绍不存在")

    update_data = data.model_dump(exclude_unset=True)
    await intro.update_from_dict(update_data).save()
    logger.info(f"商品介绍更新成功: id={intro_id}")
    return success_response(data=ProductIntroResponse.model_validate(intro))


@router.delete("/{product_id}/intros/{intro_id}", response_model=ResponseModel, summary="删除商品介绍")
async def delete_product_intro(product_id: int, intro_id: int):
    """删除商品介绍"""
    logger.info(f"删除商品介绍: product_id={product_id}, intro_id={intro_id}")
    intro = await ProductIntro.filter(id=intro_id, product_id=product_id).first()
    if not intro:
        raise NotFoundException(message="商品介绍不存在")

    await intro.delete()
    logger.info(f"商品介绍删除成功: id={intro_id}")
    return success_response(message="删除成功")
