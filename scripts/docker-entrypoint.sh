#!/bin/bash
set -e

echo "=========================================="
echo "CardStore 后端服务启动中..."
echo "=========================================="

# 显示自动生成的管理员密码（如果存在）
if [ -f .env ]; then
    ADMIN_PASSWORD=$(grep "^INIT_ADMIN_PASSWORD=" .env | cut -d'=' -f2)
    if [ "$ADMIN_PASSWORD" != "your-admin-password" ]; then
        echo "=========================================="
        echo "⚠️  自动生成的管理员密码："
        echo "   用户名: admin"
        echo "   密码: $ADMIN_PASSWORD"
        echo "   请登录后立即修改密码！"
        echo "=========================================="
    fi
fi

# 1. 等待数据库连接
sleep 3

echo "=========================================="
echo "执行自动化数据库同步 (No-Migration-Folder Mode)"
echo "=========================================="

# 2. 检查并初始化 Aerich 配置 (如果不存在)
if [ ! -f "pyproject.toml" ]; then
    echo "错误: 找不到 pyproject.toml"
    exit 1
fi

# 核心步骤：不管有没有 migrations 文件夹，我们都尝试确保它存在并包含最新逻辑
if [ ! -d "migrations/models" ]; then
    echo "首次部署：初始化 Aerich 并创建基础 Schema..."
    uv run aerich init -t app.config.TORTOISE_ORM
    # init-db 会直接根据当前的 models 生成表，并建立初始版本记录
    uv run aerich init-db
else
    echo "检测到变更：正在线上生成临时迁移脚本并同步..."
    # 这一步相当于 Django 的 makemigrations
    # 因为你没传文件夹，所以我们要现场根据代码 Model 生成差异文件
    uv run aerich migrate --name "auto_migration_$(date +%Y%m%d%H%M%S)"

    # 这一步相当于 Django 的 migrate
    # 执行刚才现场生成的差异文件
    uv run aerich upgrade
fi

# 3. 初始化管理员 (原逻辑)
uv run python /app/scripts/init_admin.py

echo "启动服务..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
