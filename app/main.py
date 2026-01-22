"""FastAPI 应用入口"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from tortoise.contrib.fastapi import RegisterTortoise

from app.api.admin import router as admin_router
from app.api.common import router as common_router
from app.api.v1 import router as v1_router
from app.config import TORTOISE_ORM, get_settings
from app.core.exceptions import AppException
from app.core.handlers import (
    app_exception_handler,
    global_exception_handler,
    http_exception_handler,
    pydantic_exception_handler,
    validation_exception_handler,
)
from app.core.logger import logger, setup_logging

settings = get_settings()

# 初始化日志
setup_logging(
    level="DEBUG" if settings.debug else "INFO",
    log_file="logs/app.log" if not settings.debug else None,
)


async def startup_payment_system():
    """启动支付系统"""
    try:
        # 导入支付提供者以触发注册
        from app.services.payment import providers  # noqa: F401
        from app.services.payment.registry import get_registry
        from app.services.payment.timeout import get_timeout_task

        # 加载并启动支付提供者
        registry = get_registry()
        await registry.load_and_start_providers()

        # 启动订单超时检查任务
        timeout_task = get_timeout_task()
        await timeout_task.start()

        logger.info("支付系统启动完成")
    except Exception as e:
        logger.error(f"支付系统启动失败: {e}")


async def shutdown_payment_system():
    """关闭支付系统"""
    try:
        from app.services.payment.registry import get_registry
        from app.services.payment.timeout import get_timeout_task
        from app.utils.redis_client import close_redis

        # 停止订单超时检查任务
        timeout_task = get_timeout_task()
        await timeout_task.stop()

        # 停止所有支付提供者
        registry = get_registry()
        await registry.stop_all_providers()

        # 关闭 Redis 连接
        await close_redis()

        logger.info("支付系统已关闭")
    except Exception as e:
        logger.error(f"支付系统关闭失败: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info(f"启动应用: {settings.app_name} v{settings.app_version}")

    async with RegisterTortoise(
        app,
        config=TORTOISE_ORM,
        generate_schemas=False,
        add_exception_handlers=True,
    ):
        logger.info("数据库连接已建立")

        # 启动支付系统
        await startup_payment_system()

        yield

        # 关闭支付系统
        await shutdown_payment_system()

    logger.info("应用已关闭")


# API响应示例 (用于Swagger文档)
responses = {
    200: {
        "description": "成功响应",
        "content": {
            "application/json": {"example": {"code": 200, "message": "success", "data": {}}}
        },
    },
    400: {
        "description": "请求参数错误 (客户端错误)",
        "content": {
            "application/json": {"example": {"code": 400, "message": "请求参数错误", "data": None}}
        },
    },
    404: {
        "description": "资源不存在 (客户端错误)",
        "content": {
            "application/json": {"example": {"code": 404, "message": "资源不存在", "data": None}}
        },
    },
    422: {
        "description": "请求验证失败 (客户端错误)",
        "content": {
            "application/json": {
                "example": {
                    "code": 422,
                    "message": "字段验证失败",
                    "data": {"errors": []},
                }
            }
        },
    },
    500: {
        "description": "服务器内部错误 (服务端错误)",
        "content": {
            "application/json": {
                "example": {"code": 500, "message": "服务器内部错误", "data": None}
            }
        },
    },
}

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
## Card Store - 开源虚拟物品交易平台 API

### 响应格式

所有API返回统一格式:

```json
{
    "code": 200,
    "message": "success",
    "data": {...}
}
```

### 状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 (客户端问题) |
| 401 | 未授权 (客户端问题) |
| 403 | 禁止访问 (客户端问题) |
| 404 | 资源不存在 (客户端问题) |
| 422 | 请求验证失败 (客户端问题) |
| 500 | 服务器内部错误 (服务端问题) |

### 4xx vs 5xx

- **4xx**: 客户端错误，请检查请求参数、认证信息等
- **5xx**: 服务端错误，请联系管理员
    """,
    lifespan=lifespan,
    responses=responses,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# 注册异常处理器
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValidationError, pydantic_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
app.mount(
    settings.static_url_prefix,
    StaticFiles(directory=str(settings.upload_dir)),
    name="static",
)

# 注册路由
app.include_router(common_router, prefix="/api/common", tags=["通用接口"])
app.include_router(v1_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
