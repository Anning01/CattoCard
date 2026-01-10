"""认证API"""

from datetime import datetime

from fastapi import APIRouter, Depends

from app.config import get_settings
from app.core.deps import get_current_admin
from app.core.exceptions import BadRequestException, UnauthorizedException
from app.core.logger import logger
from app.core.response import ResponseModel, success_response
from app.core.security import create_access_token, hash_password, verify_password
from app.models.admin import Admin
from app.schemas.admin import (
    AdminChangePassword,
    AdminCreate,
    AdminLogin,
    AdminResponse,
    TokenResponse,
)

router = APIRouter()
settings = get_settings()


@router.post("/login", response_model=ResponseModel, summary="管理员登录")
async def login(data: AdminLogin):
    logger.info(f"管理员登录: username={data.username}")

    admin = await Admin.filter(username=data.username).first()
    if not admin:
        logger.warning(f"登录失败: 用户不存在, username={data.username}")
        raise UnauthorizedException(message="用户名或密码错误")

    if not admin.is_active:
        logger.warning(f"登录失败: 用户已禁用, username={data.username}")
        raise UnauthorizedException(message="账号已被禁用")

    if not verify_password(data.password, admin.password_hash):
        logger.warning(f"登录失败: 密码错误, username={data.username}")
        raise UnauthorizedException(message="用户名或密码错误")

    # 更新最后登录时间
    admin.last_login_at = datetime.now()
    await admin.save()

    # 生成Token
    access_token = create_access_token(data={"sub": str(admin.id)})
    expires_in = settings.jwt_expire_minutes * 60 * 24 * 7  # 7天

    logger.info(f"登录成功: username={data.username}")
    return success_response(
        data=TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
        ),
        message="登录成功",
    )


@router.get("/me", response_model=ResponseModel, summary="获取当前用户信息")
async def get_me(admin: Admin = Depends(get_current_admin)):
    logger.info(f"获取当前用户信息: username={admin.username}")
    return success_response(data=AdminResponse.model_validate(admin))


@router.put("/me/password", response_model=ResponseModel, summary="修改密码")
async def change_password(
    data: AdminChangePassword,
    admin: Admin = Depends(get_current_admin),
):
    logger.info(f"修改密码: username={admin.username}")

    if not verify_password(data.old_password, admin.password_hash):
        logger.warning(f"修改密码失败: 原密码错误, username={admin.username}")
        raise BadRequestException(message="原密码错误")

    admin.password_hash = hash_password(data.new_password)
    await admin.save()

    logger.info(f"密码修改成功: username={admin.username}")
    return success_response(message="密码修改成功")


@router.post("/init", response_model=ResponseModel, summary="初始化超级管理员")
async def init_admin(data: AdminCreate):
    """
    初始化超级管理员（仅当系统中没有管理员时可用）
    """
    logger.info("尝试初始化超级管理员")

    # 检查是否已有管理员
    admin_count = await Admin.all().count()
    if admin_count > 0:
        logger.warning("初始化失败: 系统中已存在管理员")
        raise BadRequestException(message="系统已初始化，无法重复创建")

    # 创建超级管理员
    admin = await Admin.create(
        username=data.username,
        password_hash=hash_password(data.password),
        nickname=data.nickname,
        email=data.email,
        is_superuser=True,
        is_active=True,
    )

    logger.info(f"超级管理员创建成功: username={admin.username}")
    return success_response(
        data=AdminResponse.model_validate(admin),
        message="超级管理员创建成功",
    )
