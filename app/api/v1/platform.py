"""平台配置前台API"""

from fastapi import APIRouter

from app.core.exceptions import NotFoundException
from app.core.logger import logger
from app.core.response import ResponseModel, success_response
from app.models.platform import Announcement, Banner, FooterLink, PlatformConfig
from app.schemas.platform import (
    AnnouncementResponse,
    BannerResponse,
    FooterLinkResponse,
    FooterLinkType,
)

router = APIRouter()


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


@router.get("/announcements", response_model=ResponseModel, summary="获取公告列表")
async def get_announcements():
    logger.info("获取公告列表")
    announcements = await Announcement.filter(is_active=True).order_by("-created_at")
    # 返回完整的公告信息，包括 content
    data = [AnnouncementResponse.model_validate(a) for a in announcements]
    logger.info(f"获取到 {len(data)} 条公告")
    return success_response(data=data)


@router.get("/announcements/popup", response_model=ResponseModel, summary="获取弹窗公告")
async def get_popup_announcement():
    logger.info("获取弹窗公告")
    announcement = await Announcement.filter(is_active=True, is_popup=True).first()
    if announcement:
        data = AnnouncementResponse.model_validate(announcement)
        logger.info(f"获取到弹窗公告: {announcement.title}")
        return success_response(data=data)
    logger.info("无弹窗公告")
    return success_response(data=None)


@router.get(
    "/announcements/{announcement_id}", response_model=ResponseModel, summary="获取公告详情"
)
async def get_announcement(announcement_id: int):
    logger.info(f"获取公告详情: id={announcement_id}")
    announcement = await Announcement.filter(id=announcement_id, is_active=True).first()
    if not announcement:
        logger.warning(f"公告不存在: id={announcement_id}")
        raise NotFoundException(message="公告不存在")
    data = AnnouncementResponse.model_validate(announcement)
    return success_response(data=data)


@router.get("/banners", response_model=ResponseModel, summary="获取Banner列表")
async def get_banners():
    logger.info("获取Banner列表")
    banners = await Banner.filter(is_active=True).order_by("sort_order")
    data = [BannerResponse.model_validate(b) for b in banners]
    logger.info(f"获取到 {len(data)} 个Banner")
    return success_response(data=data)


@router.get("/footer-links", response_model=ResponseModel, summary="获取底部链接")
async def get_footer_links(link_type: FooterLinkType | None = None):
    logger.info(f"获取底部链接: type={link_type}")
    query = FooterLink.filter(is_active=True)
    if link_type:
        query = query.filter(link_type=link_type)
    links = await query.order_by("link_type", "sort_order")
    data = [FooterLinkResponse.model_validate(link) for link in links]
    logger.info(f"获取到 {len(data)} 个底部链接")
    return success_response(data=data)
