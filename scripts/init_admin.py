"""初始化管理员用户脚本"""

import asyncio
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, "/app")


async def init_admin():
    """初始化管理员用户"""
    from tortoise import Tortoise

    from app.config import TORTOISE_ORM
    from app.core.security import hash_password
    from app.models.admin import Admin

    # 从环境变量获取管理员信息
    username = os.getenv("INIT_ADMIN_USERNAME", "").strip()
    password = os.getenv("INIT_ADMIN_PASSWORD", "").strip()

    if not username or not password:
        print("未配置 INIT_ADMIN_USERNAME 或 INIT_ADMIN_PASSWORD，跳过管理员初始化")
        return

    try:
        await Tortoise.init(config=TORTOISE_ORM)

        # 检查是否已存在管理员
        existing = await Admin.filter(username=username).first()
        if existing:
            print(f"管理员 '{username}' 已存在，跳过创建")
            return

        # 检查是否有任何管理员
        admin_count = await Admin.all().count()
        if admin_count > 0:
            print(f"已存在 {admin_count} 个管理员，跳过初始化")
            return

        # 创建管理员
        await Admin.create(
            username=username,
            password_hash=hash_password(password),
            nickname="超级管理员",
            is_active=True,
            is_superuser=True,
        )
        print(f"管理员 '{username}' 创建成功")

    except Exception as e:
        print(f"初始化管理员失败: {e}")
        # 不抛出异常，允许应用继续启动
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(init_admin())
