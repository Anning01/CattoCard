"""应用配置"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 项目基本信息
    app_name: str = "Card Store"
    app_version: str = "0.1.0"
    debug: bool = False

    # API 路由前缀
    api_v1_prefix: str = "/api/v1"
    api_admin_prefix: str = "/api/admin"

    # 数据库配置
    database_url: str = "sqlite://./data/cardstore.db"

    # Redis 配置（可选，不配置则使用内存缓存）
    redis_url: str | None = None

    # JWT 配置
    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24小时

    # 文件上传配置
    upload_dir: Path = Path("uploads")
    upload_max_size: int = 10 * 1024 * 1024  # 10MB
    upload_allowed_extensions: set[str] = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico"}

    # 静态文件 URL 前缀
    static_url_prefix: str = "/api/static"

    # 默认货币
    default_currency: str = "USD"


@lru_cache
def get_settings() -> Settings:
    """获取缓存的配置实例"""
    return Settings()


# 初始化时确保上传目录存在
_settings = get_settings()
_settings.upload_dir.mkdir(parents=True, exist_ok=True)


# Tortoise ORM 配置
TORTOISE_ORM = {
    "connections": {
        "default": _settings.database_url,
    },
    "apps": {
        "models": {
            "models": [
                "app.models.admin",
                "app.models.platform",
                "app.models.product",
                "app.models.order",
                "aerich.models",
            ],
            "default_connection": "default",
        },
    },
}
