"""平台配置相关Schema"""

from datetime import datetime
from enum import Enum

from pydantic import Field

from app.schemas.common import BaseSchema, IDSchema, TimestampSchema


class FooterLinkType(str, Enum):
    """
    底部链接类型

    - agreement: 协议链接（如用户协议、隐私政策等）
    - friend_link: 友情链接
    """

    AGREEMENT = "agreement"
    FRIEND_LINK = "friend_link"


# ==================== 平台配置 ====================
class PlatformConfigBase(BaseSchema):
    """平台配置基础"""

    key: str = Field(..., max_length=100, description="配置键，唯一标识", examples=["site_name"])
    value: str = Field(..., description="配置值", examples=["Card Store"])
    description: str | None = Field(None, description="配置描述说明", examples=["网站名称"])


class PlatformConfigCreate(PlatformConfigBase):
    """创建平台配置"""

    pass


class PlatformConfigUpdate(BaseSchema):
    """更新平台配置"""

    value: str | None = Field(None, description="配置值")
    description: str | None = Field(None, description="配置描述说明")


class PlatformConfigResponse(PlatformConfigBase, IDSchema, TimestampSchema):
    """平台配置响应"""

    pass


# ==================== 邮件配置 ====================
class EmailConfigBase(BaseSchema):
    """邮件配置基础"""

    smtp_host: str = Field(
        ..., max_length=255, description="SMTP服务器地址", examples=["smtp.gmail.com"]
    )
    smtp_port: int = Field(587, ge=1, le=65535, description="SMTP端口", examples=[587, 465, 25])
    smtp_user: str = Field(
        ..., max_length=255, description="SMTP用户名/邮箱", examples=["user@gmail.com"]
    )
    smtp_password: str = Field(..., max_length=255, description="SMTP密码或应用专用密码")
    from_email: str = Field(
        ..., max_length=255, description="发件人邮箱地址", examples=["noreply@example.com"]
    )
    from_name: str | None = Field(
        None, max_length=100, description="发件人显示名称", examples=["Card Store"]
    )
    use_tls: bool = Field(True, description="是否使用TLS加密")


class EmailConfigCreate(EmailConfigBase):
    """创建邮件配置"""

    pass


class EmailConfigUpdate(BaseSchema):
    """更新邮件配置"""

    smtp_host: str | None = Field(None, description="SMTP服务器地址")
    smtp_port: int | None = Field(None, ge=1, le=65535, description="SMTP端口")
    smtp_user: str | None = Field(None, description="SMTP用户名")
    smtp_password: str | None = Field(None, description="SMTP密码")
    from_email: str | None = Field(None, description="发件人邮箱")
    from_name: str | None = Field(None, description="发件人名称")
    use_tls: bool | None = Field(None, description="是否使用TLS")


class EmailConfigResponse(IDSchema, TimestampSchema):
    """邮件配置响应（不返回密码）"""

    smtp_host: str = Field(..., description="SMTP服务器地址")
    smtp_port: int = Field(..., description="SMTP端口")
    smtp_user: str = Field(..., description="SMTP用户名")
    from_email: str = Field(..., description="发件人邮箱")
    from_name: str | None = Field(None, description="发件人名称")
    use_tls: bool = Field(..., description="是否使用TLS")
    is_verified: bool = Field(..., description="配置是否已验证可用")


# ==================== 公告 ====================
class AnnouncementBase(BaseSchema):
    """公告基础"""

    title: str = Field(..., max_length=255, description="公告标题", examples=["系统维护通知"])
    description: str | None = Field(
        None,
        max_length=500,
        description="公告简短描述",
        examples=["系统将于今晚进行维护升级"],
    )
    content: str = Field(
        ...,
        description="公告详细内容，支持HTML富文本",
        examples=["<h2>维护通知</h2><p>系统将于今晚22:00-24:00进行维护</p>"],
    )
    is_popup: bool = Field(False, description="是否弹窗显示（同时只有一个公告可以弹窗）")
    is_active: bool = Field(True, description="是否启用")
    sort_order: int = Field(0, ge=0, description="排序值，越小越靠前")


class AnnouncementCreate(AnnouncementBase):
    """创建公告"""

    pass


class AnnouncementUpdate(BaseSchema):
    """更新公告"""

    title: str | None = Field(None, description="公告标题")
    description: str | None = Field(None, description="公告描述")
    content: str | None = Field(None, description="公告内容")
    is_popup: bool | None = Field(None, description="是否弹窗显示")
    is_active: bool | None = Field(None, description="是否启用")
    sort_order: int | None = Field(None, description="排序值")


class AnnouncementResponse(AnnouncementBase, IDSchema, TimestampSchema):
    """公告响应"""

    pass


class AnnouncementListResponse(BaseSchema):
    """公告列表响应（简化版）"""

    id: int = Field(..., description="公告ID")
    title: str = Field(..., description="公告标题")
    description: str | None = Field(None, description="公告描述")
    is_popup: bool = Field(..., description="是否弹窗")
    created_at: datetime = Field(..., description="创建时间")


# ==================== Banner ====================
class BannerBase(BaseSchema):
    """Banner基础"""

    image_url: str = Field(
        ...,
        max_length=500,
        description="Banner图片URL",
        examples=["https://example.com/banner1.jpg"],
    )
    link_url: str | None = Field(
        None,
        max_length=500,
        description="点击跳转链接",
        examples=["https://example.com/promotion"],
    )
    title: str | None = Field(
        None, max_length=100, description="Banner标题/Alt文本", examples=["新年促销"]
    )
    sort_order: int = Field(0, ge=0, description="排序值，越小越靠前")
    is_active: bool = Field(True, description="是否启用")


class BannerCreate(BannerBase):
    """创建Banner"""

    pass


class BannerUpdate(BaseSchema):
    """更新Banner"""

    image_url: str | None = Field(None, description="图片URL")
    link_url: str | None = Field(None, description="跳转链接")
    title: str | None = Field(None, description="标题")
    sort_order: int | None = Field(None, description="排序值")
    is_active: bool | None = Field(None, description="是否启用")


class BannerResponse(BannerBase, IDSchema, TimestampSchema):
    """Banner响应"""

    pass


# ==================== 底部链接 ====================
class FooterLinkBase(BaseSchema):
    """底部链接基础"""

    title: str = Field(
        ..., max_length=100, description="链接标题", examples=["用户协议", "友情链接"]
    )
    url: str = Field(
        ..., max_length=500, description="链接地址", examples=["https://example.com/terms"]
    )
    link_type: FooterLinkType = Field(
        FooterLinkType.FRIEND_LINK,
        description="链接类型: agreement=协议, friend_link=友链",
    )
    sort_order: int = Field(0, ge=0, description="排序值，越小越靠前")
    is_active: bool = Field(True, description="是否启用")


class FooterLinkCreate(FooterLinkBase):
    """创建底部链接"""

    pass


class FooterLinkUpdate(BaseSchema):
    """更新底部链接"""

    title: str | None = Field(None, description="链接标题")
    url: str | None = Field(None, description="链接地址")
    link_type: FooterLinkType | None = Field(None, description="链接类型")
    sort_order: int | None = Field(None, description="排序值")
    is_active: bool | None = Field(None, description="是否启用")


class FooterLinkResponse(FooterLinkBase, IDSchema, TimestampSchema):
    """底部链接响应"""

    pass
