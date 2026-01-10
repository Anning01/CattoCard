"""模型基类"""

from tortoise import fields
from tortoise.models import Model


class TimestampMixin:
    """时间戳混入类"""

    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")


class BaseModel(Model, TimestampMixin):
    """基础模型"""

    id = fields.IntField(pk=True, description="主键ID")

    class Meta:
        abstract = True
