"""工具函数"""

from typing import TypeVar

from tortoise.models import Model
from tortoise.queryset import QuerySet

T = TypeVar("T", bound=Model)


async def paginate(
    queryset: QuerySet[T],
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[T], int, int]:
    """
    分页查询

    Args:
        queryset: 查询集
        page: 页码
        page_size: 每页数量

    Returns:
        (items, total, pages)
    """
    total = await queryset.count()
    pages = (total + page_size - 1) // page_size
    offset = (page - 1) * page_size
    items = await queryset.offset(offset).limit(page_size)
    return items, total, pages
