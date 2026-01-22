"""异常处理器"""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppException
from app.core.logger import logger


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    应用异常处理器
    """
    logger.warning(
        f"AppException | {request.method} {request.url.path} | "
        f"code={exc.code} | message={exc.message}"
    )

    return JSONResponse(
        status_code=exc.code,
        content={
            "code": exc.code,
            "message": exc.message,
            "data": exc.data,
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    HTTP异常处理器
    """
    logger.warning(
        f"HTTPException | {request.method} {request.url.path} | "
        f"status={exc.status_code} | detail={exc.detail}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": str(exc.detail),
            "data": None,
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    请求验证异常处理器 (参数校验失败)
    """
    errors = exc.errors()
    error_messages = []

    for error in errors:
        loc = ".".join(str(x) for x in error["loc"] if x != "body")
        msg = error["msg"]
        error_messages.append(f"{loc}: {msg}")

    message = "; ".join(error_messages) if error_messages else "请求参数验证失败"

    logger.warning(f"ValidationError | {request.method} {request.url.path} | errors={errors}")

    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "message": message,
            "data": {"errors": errors},
        },
    )


async def pydantic_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """
    Pydantic验证异常处理器
    """
    errors = exc.errors()

    logger.warning(
        f"PydanticValidationError | {request.method} {request.url.path} | errors={errors}"
    )

    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "message": "数据验证失败",
            "data": {"errors": errors},
        },
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    全局异常处理器 (兜底)
    """
    logger.exception(
        f"UnhandledException | {request.method} {request.url.path} | "
        f"error={type(exc).__name__}: {exc}"
    )

    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "data": None,
        },
    )
