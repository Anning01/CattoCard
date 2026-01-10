"""统一响应格式"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    """
    统一响应模型

    成功响应 (code=200):
    {
        "code": 200,
        "message": "success",
        "data": {...}
    }

    失败响应 (code=4xx/5xx):
    {
        "code": 400,
        "message": "错误描述",
        "data": null
    }
    """

    code: int = 200
    message: str = "success"
    data: T | None = None


class PaginatedData(BaseModel, Generic[T]):
    """分页数据"""

    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


def success_response(
    data: Any = None,
    message: str = "success",
) -> ResponseModel:
    """
    创建成功响应

    Args:
        data: 响应数据
        message: 成功消息

    Returns:
        ResponseModel
    """
    return ResponseModel(code=200, message=message, data=data)


def error_response(
    code: int,
    message: str,
    data: Any = None,
) -> ResponseModel:
    """
    创建错误响应

    Args:
        code: 错误码 (4xx 客户端错误, 5xx 服务端错误)
        message: 错误消息
        data: 附加数据

    Returns:
        ResponseModel
    """
    return ResponseModel(code=code, message=message, data=data)
