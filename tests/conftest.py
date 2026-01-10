"""测试配置"""

import pytest
from httpx import ASGITransport, AsyncClient
from tortoise import Tortoise

from app.main import app


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="function")
async def client():
    """测试客户端"""
    # 初始化测试数据库
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={
            "models": [
                "app.models.platform",
                "app.models.product",
                "app.models.order",
            ]
        },
    )
    await Tortoise.generate_schemas()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    await Tortoise.close_connections()
