"""管理员模型"""

from tortoise import fields

from app.models.base import BaseModel


class Admin(BaseModel):
    """管理员"""

    username = fields.CharField(max_length=50, unique=True, description="用户名")
    password_hash = fields.CharField(max_length=255, description="密码哈希")
    nickname = fields.CharField(max_length=100, null=True, description="昵称")
    email = fields.CharField(max_length=255, null=True, description="邮箱")
    is_active = fields.BooleanField(default=True, description="是否启用")
    is_superuser = fields.BooleanField(default=False, description="是否超级管理员")
    last_login_at = fields.DatetimeField(null=True, description="最后登录时间")

    class Meta:
        table = "admin"
        table_description = "管理员表"

    def __str__(self):
        return self.username
