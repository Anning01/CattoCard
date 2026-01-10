"""通用Schema"""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseSchema(BaseModel):
    """基础Schema"""

    model_config = ConfigDict(from_attributes=True)


class TimestampSchema(BaseSchema):
    """带时间戳的Schema"""

    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class IDSchema(BaseSchema):
    """带ID的Schema"""

    id: int = Field(..., description="主键ID")


class PaginationParams(BaseSchema):
    """分页参数"""

    page: int = Field(1, ge=1, description="页码，从1开始")
    page_size: int = Field(20, ge=1, le=100, description="每页数量，最大100")
