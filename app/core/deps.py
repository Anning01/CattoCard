"""依赖注入"""

from fastapi import Depends, Header

from app.core.exceptions import UnauthorizedException
from app.core.logger import logger
from app.core.security import decode_access_token
from app.models.admin import Admin


async def get_current_admin(authorization: str = Header(..., description="Bearer Token")) -> Admin:
    """
    获取当前登录的管理员

    需要在请求头中携带: Authorization: Bearer <token>
    """
    if not authorization.startswith("Bearer "):
        logger.warning("认证失败: 无效的Authorization格式")
        raise UnauthorizedException(message="无效的认证格式，请使用 Bearer Token")

    token = authorization[7:]  # 去掉 "Bearer " 前缀
    payload = decode_access_token(token)

    if not payload:
        logger.warning("认证失败: Token无效或已过期")
        raise UnauthorizedException(message="Token无效或已过期")

    admin_id = payload.get("sub")
    if not admin_id:
        logger.warning("认证失败: Token中缺少用户信息")
        raise UnauthorizedException(message="无效的Token")

    admin = await Admin.filter(id=int(admin_id), is_active=True).first()
    if not admin:
        logger.warning(f"认证失败: 管理员不存在或已禁用, id={admin_id}")
        raise UnauthorizedException(message="用户不存在或已被禁用")

    return admin


async def get_current_superuser(admin: Admin = Depends(get_current_admin)) -> Admin:
    """获取当前超级管理员"""
    if not admin.is_superuser:
        logger.warning(f"权限不足: {admin.username} 不是超级管理员")
        raise UnauthorizedException(message="需要超级管理员权限")
    return admin
