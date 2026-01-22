"""文件上传服务"""

import hashlib
import os
import uuid
from datetime import datetime
from pathlib import Path

import aiofiles

from app.config import get_settings
from app.core.exceptions import BadRequestException
from app.core.logger import logger

settings = get_settings()


def get_file_hash(content: bytes) -> str:
    """计算文件MD5哈希"""
    return hashlib.md5(content).hexdigest()


def get_upload_path(filename: str, subdir: str = "") -> tuple[Path, str]:
    """
    生成上传文件路径

    按日期分目录存储: uploads/2024/01/15/uuid_filename.ext

    Returns:
        (完整文件路径, 相对URL路径)
    """
    # 获取文件扩展名
    ext = Path(filename).suffix.lower()

    # 验证扩展名
    if ext not in settings.upload_allowed_extensions:
        raise BadRequestException(
            message=f"不支持的文件类型: {ext}，允许的类型: {', '.join(settings.upload_allowed_extensions)}"
        )

    # 按日期生成目录
    date_path = datetime.now().strftime("%Y/%m/%d")

    # 生成唯一文件名
    unique_name = f"{uuid.uuid4().hex[:16]}{ext}"

    # 构建路径
    if subdir:
        dir_path = settings.upload_dir / subdir / date_path
        url_path = f"{settings.static_url_prefix}/{subdir}/{date_path}/{unique_name}"
    else:
        dir_path = settings.upload_dir / date_path
        url_path = f"{settings.static_url_prefix}/{date_path}/{unique_name}"

    # 确保目录存在
    dir_path.mkdir(parents=True, exist_ok=True)

    file_path = dir_path / unique_name

    return file_path, url_path


async def save_upload_file(content: bytes, filename: str, subdir: str = "") -> str:
    """
    保存上传的文件

    Args:
        content: 文件内容
        filename: 原始文件名
        subdir: 子目录（如 images, icons 等）

    Returns:
        文件访问URL
    """
    # 检查文件大小
    if len(content) > settings.upload_max_size:
        raise BadRequestException(
            message=f"文件大小超过限制: {settings.upload_max_size // 1024 // 1024}MB"
        )

    # 获取保存路径
    file_path, url_path = get_upload_path(filename, subdir)

    # 异步写入文件
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    logger.info(f"文件上传成功: {file_path} -> {url_path}")

    return url_path


def delete_upload_file(url_path: str) -> bool:
    """
    删除上传的文件

    Args:
        url_path: 文件URL路径（如 /static/2024/01/15/xxx.jpg）

    Returns:
        是否删除成功
    """
    # 从URL路径转换为文件系统路径
    if not url_path.startswith(settings.static_url_prefix):
        logger.warning(f"无效的文件路径: {url_path}")
        return False

    # 移除URL前缀，获取相对路径
    relative_path = url_path[len(settings.static_url_prefix) :].lstrip("/")
    file_path = settings.upload_dir / relative_path

    # 安全检查：确保路径在上传目录内
    try:
        file_path.resolve().relative_to(settings.upload_dir.resolve())
    except ValueError:
        logger.warning(f"路径安全检查失败: {url_path}")
        return False

    # 删除文件
    if file_path.exists() and file_path.is_file():
        os.remove(file_path)
        logger.info(f"文件删除成功: {file_path}")

        # 尝试清理空目录
        _cleanup_empty_dirs(file_path.parent)

        return True

    logger.warning(f"文件不存在: {file_path}")
    return False


def _cleanup_empty_dirs(dir_path: Path) -> None:
    """清理空目录（向上递归）"""
    try:
        while dir_path != settings.upload_dir:
            if dir_path.exists() and dir_path.is_dir() and not any(dir_path.iterdir()):
                dir_path.rmdir()
                logger.debug(f"清理空目录: {dir_path}")
                dir_path = dir_path.parent
            else:
                break
    except Exception as e:
        logger.debug(f"清理目录失败: {e}")
