"""平台配置相关模型"""

from tortoise import fields

from app.models.base import BaseModel
from app.schemas.platform import FooterLinkType


class PlatformConfig(BaseModel):
    """平台配置"""

    key = fields.CharField(max_length=100, unique=True, description="配置键")
    value = fields.TextField(description="配置值")
    description = fields.CharField(max_length=255, null=True, description="配置描述")

    class Meta:
        table = "platform_config"
        table_description = "平台配置表"


class EmailConfig(BaseModel):
    """邮件服务器配置"""

    smtp_host = fields.CharField(max_length=255, description="SMTP服务器地址")
    smtp_port = fields.IntField(default=587, description="SMTP端口")
    smtp_user = fields.CharField(max_length=255, description="SMTP用户名")
    smtp_password = fields.CharField(max_length=255, description="SMTP密码")
    from_email = fields.CharField(max_length=255, description="发件人邮箱")
    from_name = fields.CharField(max_length=100, null=True, description="发件人名称")
    use_tls = fields.BooleanField(default=True, description="是否使用TLS")
    is_verified = fields.BooleanField(default=False, description="是否已验证")

    class Meta:
        table = "email_config"
        table_description = "邮件服务器配置表"


class Announcement(BaseModel):
    """平台公告"""

    title = fields.CharField(max_length=255, description="公告标题")
    description = fields.CharField(max_length=500, null=True, description="公告描述")
    content = fields.TextField(description="公告内容(富文本HTML)")
    is_popup = fields.BooleanField(default=False, description="是否弹窗显示")
    is_active = fields.BooleanField(default=True, description="是否启用")
    sort_order = fields.IntField(default=0, description="排序")

    class Meta:
        table = "announcement"
        table_description = "平台公告表"
        ordering = ["-created_at"]


class Banner(BaseModel):
    """首页Banner"""

    image_url = fields.CharField(max_length=500, description="图片URL")
    link_url = fields.CharField(max_length=500, null=True, description="跳转链接")
    title = fields.CharField(max_length=100, null=True, description="Banner标题")
    sort_order = fields.IntField(default=0, description="排序")
    is_active = fields.BooleanField(default=True, description="是否启用")

    class Meta:
        table = "banner"
        table_description = "首页Banner表"
        ordering = ["sort_order"]


class FooterLink(BaseModel):
    """底部链接(协议与友链)"""

    title = fields.CharField(max_length=100, description="链接标题")
    url = fields.CharField(max_length=500, description="链接地址")
    link_type = fields.CharEnumField(
        FooterLinkType, default=FooterLinkType.FRIEND_LINK, description="链接类型"
    )
    sort_order = fields.IntField(default=0, description="排序")
    is_active = fields.BooleanField(default=True, description="是否启用")

    class Meta:
        table = "footer_link"
        table_description = "底部链接表"
        ordering = ["link_type", "sort_order"]
