"""平台配置管理API"""

from fastapi import APIRouter

from app.core.exceptions import BadRequestException, NotFoundException
from app.core.logger import logger
from app.core.response import ResponseModel, success_response
from app.models.platform import (
    Announcement,
    Banner,
    EmailConfig,
    FooterLink,
    PlatformConfig,
)
from app.schemas.platform import (
    AnnouncementCreate,
    AnnouncementResponse,
    AnnouncementUpdate,
    BannerCreate,
    BannerResponse,
    BannerUpdate,
    EmailConfigCreate,
    EmailConfigResponse,
    FooterLinkCreate,
    FooterLinkResponse,
    FooterLinkUpdate,
    PlatformConfigCreate,
    PlatformConfigResponse,
    PlatformConfigUpdate,
)

router = APIRouter()


# ==================== 平台配置 ====================


@router.get("/site-config", response_model=ResponseModel, summary="获取站点配置")
async def get_site_config():
    """获取前台需要的站点配置"""
    logger.info("获取站点配置")
    config_keys = [
        "site_name",
        "site_description",
        "site_logo",
        "site_favicon",
        "currency",
        "currency_symbol",
        "contact_info",
    ]
    configs = await PlatformConfig.filter(key__in=config_keys)
    data = {c.key: c.value for c in configs}
    # 设置默认值
    data.setdefault("site_name", "CardStore")
    data.setdefault("site_description", "虚拟商品交易平台")
    data.setdefault("currency", "CNY")
    data.setdefault("currency_symbol", "$")
    data.setdefault("contact_info", "")
    logger.info(f"获取到站点配置: {list(data.keys())}")
    return success_response(data=data)


@router.get("/config", response_model=ResponseModel, summary="获取所有平台配置")
async def get_platform_configs():
    logger.info("获取所有平台配置")
    configs = await PlatformConfig.all()
    data = [PlatformConfigResponse.model_validate(c) for c in configs]
    return success_response(data=data)


@router.post("/config", response_model=ResponseModel, summary="创建平台配置")
async def create_platform_config(data: PlatformConfigCreate):
    logger.info(f"创建平台配置: key={data.key}")
    if await PlatformConfig.filter(key=data.key).exists():
        raise BadRequestException(message="配置键已存在")
    config = await PlatformConfig.create(**data.model_dump())
    logger.info(f"平台配置创建成功: id={config.id}")
    return success_response(data=PlatformConfigResponse.model_validate(config))


@router.put("/config/{key}", response_model=ResponseModel, summary="更新平台配置")
async def update_platform_config(key: str, data: PlatformConfigUpdate):
    logger.info(f"更新平台配置: key={key}")
    config = await PlatformConfig.filter(key=key).first()
    if not config:
        raise NotFoundException(message="配置不存在")
    update_data = data.model_dump(exclude_unset=True)
    await config.update_from_dict(update_data).save()
    logger.info(f"平台配置更新成功: key={key}")
    return success_response(data=PlatformConfigResponse.model_validate(config))


# ==================== 邮件配置 ====================
@router.get("/email-config", response_model=ResponseModel, summary="获取邮件配置")
async def get_email_config():
    logger.info("获取邮件配置")
    config = await EmailConfig.first()
    if config:
        return success_response(data=EmailConfigResponse.model_validate(config))
    return success_response(data=None)


@router.post("/email-config", response_model=ResponseModel, summary="创建或更新邮件配置")
async def create_or_update_email_config(data: EmailConfigCreate):
    logger.info("创建或更新邮件配置")
    config = await EmailConfig.first()
    config_data = data.model_dump()
    config_data["is_verified"] = False  # 配置变更后需要重新验证

    if config:
        await config.update_from_dict(config_data).save()
        logger.info("邮件配置已更新")
    else:
        config = await EmailConfig.create(**config_data)
        logger.info("邮件配置已创建")
    return success_response(data=EmailConfigResponse.model_validate(config))


@router.post("/email-config/test", response_model=ResponseModel, summary="测试邮件配置")
async def test_email_config(test_email: str):
    """发送测试邮件，成功则标记配置为已验证"""
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    import aiosmtplib

    logger.info(f"测试邮件配置: to={test_email}")
    config = await EmailConfig.first()
    if not config:
        raise NotFoundException(message="邮件配置不存在")

    try:
        message = MIMEMultipart("alternative")
        message["From"] = f"{config.from_name or 'System'} <{config.from_email}>"
        message["To"] = test_email
        message["Subject"] = "邮件配置测试"

        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #28a745;">✅ 邮件配置测试成功</h2>
            <p>如果您收到这封邮件，说明邮件服务器配置正确。</p>
        </body>
        </html>
        """
        html_part = MIMEText(html_content, "html", "utf-8")
        message.attach(html_part)

        await aiosmtplib.send(
            message,
            hostname=config.smtp_host,
            port=config.smtp_port,
            username=config.smtp_user,
            password=config.smtp_password,
            use_tls=config.use_tls,
        )

        # 测试成功，标记为已验证
        config.is_verified = True
        await config.save()

        logger.info("邮件测试成功，配置已验证")
        return success_response(message="测试邮件发送成功，配置已验证")

    except Exception as e:
        logger.error(f"邮件测试失败: {e}")
        raise BadRequestException(message=f"邮件发送失败: {str(e)}")


# ==================== 公告管理 ====================
@router.get("/announcements", response_model=ResponseModel, summary="获取所有公告")
async def get_announcements():
    logger.info("获取所有公告(管理)")
    announcements = await Announcement.all().order_by("-created_at")
    data = [AnnouncementResponse.model_validate(a) for a in announcements]
    return success_response(data=data)


@router.post("/announcements", response_model=ResponseModel, summary="创建公告")
async def create_announcement(data: AnnouncementCreate):
    logger.info(f"创建公告: title={data.title}")
    if data.is_popup:
        await Announcement.filter(is_popup=True).update(is_popup=False)
    announcement = await Announcement.create(**data.model_dump())
    logger.info(f"公告创建成功: id={announcement.id}")
    return success_response(data=AnnouncementResponse.model_validate(announcement))


@router.put("/announcements/{announcement_id}", response_model=ResponseModel, summary="更新公告")
async def update_announcement(announcement_id: int, data: AnnouncementUpdate):
    logger.info(f"更新公告: id={announcement_id}")
    announcement = await Announcement.filter(id=announcement_id).first()
    if not announcement:
        raise NotFoundException(message="公告不存在")

    update_data = data.model_dump(exclude_unset=True)
    if update_data.get("is_popup"):
        await Announcement.filter(is_popup=True).exclude(id=announcement_id).update(is_popup=False)

    await announcement.update_from_dict(update_data).save()
    logger.info(f"公告更新成功: id={announcement_id}")
    return success_response(data=AnnouncementResponse.model_validate(announcement))


@router.delete("/announcements/{announcement_id}", response_model=ResponseModel, summary="删除公告")
async def delete_announcement(announcement_id: int):
    logger.info(f"删除公告: id={announcement_id}")
    deleted = await Announcement.filter(id=announcement_id).delete()
    if not deleted:
        raise NotFoundException(message="公告不存在")
    logger.info(f"公告删除成功: id={announcement_id}")
    return success_response(message="删除成功")


# ==================== Banner管理 ====================
@router.get("/banners", response_model=ResponseModel, summary="获取所有Banner")
async def get_banners():
    logger.info("获取所有Banner(管理)")
    banners = await Banner.all().order_by("sort_order")
    data = [BannerResponse.model_validate(b) for b in banners]
    return success_response(data=data)


@router.post("/banners", response_model=ResponseModel, summary="创建Banner")
async def create_banner(data: BannerCreate):
    logger.info(f"创建Banner: title={data.title}")
    banner = await Banner.create(**data.model_dump())
    logger.info(f"Banner创建成功: id={banner.id}")
    return success_response(data=BannerResponse.model_validate(banner))


@router.put("/banners/{banner_id}", response_model=ResponseModel, summary="更新Banner")
async def update_banner(banner_id: int, data: BannerUpdate):
    logger.info(f"更新Banner: id={banner_id}")
    banner = await Banner.filter(id=banner_id).first()
    if not banner:
        raise NotFoundException(message="Banner不存在")
    update_data = data.model_dump(exclude_unset=True)
    await banner.update_from_dict(update_data).save()
    logger.info(f"Banner更新成功: id={banner_id}")
    return success_response(data=BannerResponse.model_validate(banner))


@router.delete("/banners/{banner_id}", response_model=ResponseModel, summary="删除Banner")
async def delete_banner(banner_id: int):
    logger.info(f"删除Banner: id={banner_id}")
    deleted = await Banner.filter(id=banner_id).delete()
    if not deleted:
        raise NotFoundException(message="Banner不存在")
    logger.info(f"Banner删除成功: id={banner_id}")
    return success_response(message="删除成功")


# ==================== 底部链接管理 ====================
@router.get("/footer-links", response_model=ResponseModel, summary="获取所有底部链接")
async def get_footer_links():
    logger.info("获取所有底部链接(管理)")
    links = await FooterLink.all().order_by("link_type", "sort_order")
    data = [FooterLinkResponse.model_validate(link) for link in links]
    return success_response(data=data)


@router.post("/footer-links", response_model=ResponseModel, summary="创建底部链接")
async def create_footer_link(data: FooterLinkCreate):
    logger.info(f"创建底部链接: title={data.title}")
    link = await FooterLink.create(**data.model_dump())
    logger.info(f"底部链接创建成功: id={link.id}")
    return success_response(data=FooterLinkResponse.model_validate(link))


@router.put("/footer-links/{link_id}", response_model=ResponseModel, summary="更新底部链接")
async def update_footer_link(link_id: int, data: FooterLinkUpdate):
    logger.info(f"更新底部链接: id={link_id}")
    link = await FooterLink.filter(id=link_id).first()
    if not link:
        raise NotFoundException(message="链接不存在")
    update_data = data.model_dump(exclude_unset=True)
    await link.update_from_dict(update_data).save()
    logger.info(f"底部链接更新成功: id={link_id}")
    return success_response(data=FooterLinkResponse.model_validate(link))


@router.delete("/footer-links/{link_id}", response_model=ResponseModel, summary="删除底部链接")
async def delete_footer_link(link_id: int):
    logger.info(f"删除底部链接: id={link_id}")
    deleted = await FooterLink.filter(id=link_id).delete()
    if not deleted:
        raise NotFoundException(message="链接不存在")
    logger.info(f"底部链接删除成功: id={link_id}")
    return success_response(message="删除成功")
