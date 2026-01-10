"""自定义异常"""

from typing import Any


class AppException(Exception):
    """
    应用基础异常

    4xx: 客户端错误 (请求参数错误、资源不存在等)
    5xx: 服务端错误 (内部错误、数据库错误等)
    """

    def __init__(
        self,
        code: int = 500,
        message: str = "服务器内部错误",
        data: Any = None,
    ):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


class BadRequestException(AppException):
    """400 请求参数错误"""

    def __init__(self, message: str = "请求参数错误", data: Any = None):
        super().__init__(code=400, message=message, data=data)


class UnauthorizedException(AppException):
    """401 未授权"""

    def __init__(self, message: str = "未授权，请先登录", data: Any = None):
        super().__init__(code=401, message=message, data=data)


class ForbiddenException(AppException):
    """403 禁止访问"""

    def __init__(self, message: str = "禁止访问", data: Any = None):
        super().__init__(code=403, message=message, data=data)


class NotFoundException(AppException):
    """404 资源不存在"""

    def __init__(self, message: str = "资源不存在", data: Any = None):
        super().__init__(code=404, message=message, data=data)


class ConflictException(AppException):
    """409 资源冲突"""

    def __init__(self, message: str = "资源冲突", data: Any = None):
        super().__init__(code=409, message=message, data=data)


class InternalServerException(AppException):
    """500 服务器内部错误"""

    def __init__(self, message: str = "服务器内部错误", data: Any = None):
        super().__init__(code=500, message=message, data=data)
