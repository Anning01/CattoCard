#!/bin/bash
set -e

echo "=========================================="
echo "CardStore 后端服务启动中..."
echo "=========================================="

# 等待数据库就绪
echo "等待数据库连接..."
sleep 3

# 检查数据库是否已初始化（通过检查表是否存在）
echo "检查数据库状态..."
DB_INITIALIZED=$(uv run python -c "
import asyncio
from tortoise import Tortoise
from app.config import TORTOISE_ORM

async def check():
    try:
        await Tortoise.init(config=TORTOISE_ORM)
        conn = Tortoise.get_connection('default')
        # 检查 admin 表是否存在
        result = await conn.execute_query(
            \"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'admin')\"
        )
        exists = result[1][0]['exists'] if result[1] else False
        await Tortoise.close_connections()
        print('yes' if exists else 'no')
    except Exception as e:
        print('no')

asyncio.run(check())
" 2>/dev/null || echo "no")

if [ "$DB_INITIALIZED" = "no" ]; then
    echo "数据库未初始化，正在初始化..."

    # 生成数据库 schema
    uv run python -c "
import asyncio
from tortoise import Tortoise
from app.config import TORTOISE_ORM

async def init():
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    await Tortoise.close_connections()
    print('数据库 schema 生成完成')

asyncio.run(init())
"

    # 初始化管理员
    echo "初始化管理员..."
    uv run python /app/scripts/init_admin.py

    echo "数据库初始化完成"
else
    echo "数据库已初始化，跳过"
fi

echo "启动应用服务..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
