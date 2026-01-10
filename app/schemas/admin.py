"""管理员相关Schema"""

from datetime import datetime

from pydantic import EmailStr, Field

from app.schemas.common import BaseSchema, IDSchema, TimestampSchema


class AdminLogin(BaseSchema):
    """管理员登录"""

    username: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="用户名",
        examples=["admin"],
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="密码",
        examples=["123456"],
    )


class AdminCreate(BaseSchema):
    """创建管理员"""

    username: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="用户名，唯一",
        examples=["admin"],
        pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$",
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="密码，至少6位",
        examples=["123456"],
    )
    nickname: str | None = Field(
        None,
        max_length=100,
        description="昵称",
        examples=["管理员"],
    )
    email: EmailStr | None = Field(
        None,
        description="邮箱",
        examples=["admin@example.com"],
    )
    is_superuser: bool = Field(False, description="是否超级管理员")


class AdminUpdate(BaseSchema):
    """更新管理员"""

    nickname: str | None = Field(None, description="昵称")
    email: EmailStr | None = Field(None, description="邮箱")
    is_active: bool | None = Field(None, description="是否启用")
    is_superuser: bool | None = Field(None, description="是否超级管理员")


class AdminChangePassword(BaseSchema):
    """修改密码"""

    old_password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="原密码",
    )
    new_password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="新密码，至少6位",
    )


class AdminResetPassword(BaseSchema):
    """重置密码（超级管理员操作）"""

    new_password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="新密码，至少6位",
    )


class AdminResponse(IDSchema, TimestampSchema):
    """管理员响应"""

    username: str = Field(..., description="用户名")
    nickname: str | None = Field(None, description="昵称")
    email: str | None = Field(None, description="邮箱")
    is_active: bool = Field(..., description="是否启用")
    is_superuser: bool = Field(..., description="是否超级管理员")
    last_login_at: datetime | None = Field(None, description="最后登录时间")


class TokenResponse(BaseSchema):
    """Token响应"""

    access_token: str = Field(..., description="JWT访问令牌")
    token_type: str = Field("bearer", description="令牌类型，固定为 bearer")
    expires_in: int = Field(..., description="过期时间（秒）", examples=[86400])
