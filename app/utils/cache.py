"""缓存工具 - 支持 Redis 和内存缓存"""

import asyncio
import time
from typing import Any

from app.config import get_settings
from app.core.logger import logger

settings = get_settings()

# 内存缓存存储
_memory_cache: dict[str, tuple[Any, float]] = {}
_cache_lock = asyncio.Lock()

# Redis 客户端（延迟初始化）
_redis_client = None


async def get_redis():
    """获取 Redis 客户端"""
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    if not settings.redis_url:
        return None

    try:
        import redis.asyncio as redis

        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        # 测试连接
        await _redis_client.ping()
        logger.info("Redis 连接成功")
        return _redis_client
    except Exception as e:
        logger.warning(f"Redis 连接失败，使用内存缓存: {e}")
        return None


async def cache_get(key: str) -> Any | None:
    """获取缓存值"""
    redis = await get_redis()

    if redis:
        try:
            import json

            value = await redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Redis 获取失败: {e}")

    # 内存缓存
    async with _cache_lock:
        if key in _memory_cache:
            value, expire_at = _memory_cache[key]
            if expire_at > time.time():
                return value
            # 过期删除
            del _memory_cache[key]
        return None


async def cache_set(key: str, value: Any, ttl: int = 3600) -> bool:
    """设置缓存值"""
    redis = await get_redis()

    if redis:
        try:
            import json

            await redis.setex(key, ttl, json.dumps(value, ensure_ascii=False))
            return True
        except Exception as e:
            logger.warning(f"Redis 设置失败: {e}")

    # 内存缓存
    async with _cache_lock:
        expire_at = time.time() + ttl
        _memory_cache[key] = (value, expire_at)
        return True


async def cache_delete(key: str) -> bool:
    """删除缓存"""
    redis = await get_redis()

    if redis:
        try:
            await redis.delete(key)
        except Exception as e:
            logger.warning(f"Redis 删除失败: {e}")

    # 同时删除内存缓存
    async with _cache_lock:
        if key in _memory_cache:
            del _memory_cache[key]
    return True


async def cache_clear_prefix(prefix: str) -> int:
    """清除指定前缀的所有缓存"""
    count = 0
    redis = await get_redis()

    if redis:
        try:
            keys = []
            async for key in redis.scan_iter(f"{prefix}*"):
                keys.append(key)
            if keys:
                count = await redis.delete(*keys)
        except Exception as e:
            logger.warning(f"Redis 批量删除失败: {e}")

    # 内存缓存
    async with _cache_lock:
        keys_to_delete = [k for k in _memory_cache.keys() if k.startswith(prefix)]
        for k in keys_to_delete:
            del _memory_cache[k]
            count += 1

    return count


# ==================== 标签缓存 ====================
TAG_CACHE_KEY = "product:tags:suggestions"
TAG_CACHE_TTL = 3600  # 1小时


async def get_tag_suggestions() -> dict[str, list[str]]:
    """获取标签建议（key -> [values]）"""
    cached = await cache_get(TAG_CACHE_KEY)
    if cached:
        return cached
    return {}


async def update_tag_suggestions(tags: list[dict[str, str]]) -> None:
    """
    更新标签建议
    tags: [{"key": "国家", "value": "中国"}, ...]
    """
    current = await get_tag_suggestions()

    for tag in tags:
        key = tag.get("key", "").strip()
        value = tag.get("value", "").strip()
        if not key or not value:
            continue

        if key not in current:
            current[key] = []

        if value not in current[key]:
            current[key].append(value)
            # 限制每个 key 最多保存 50 个 value
            if len(current[key]) > 50:
                current[key] = current[key][-50:]

    await cache_set(TAG_CACHE_KEY, current, TAG_CACHE_TTL)


async def add_tag_suggestion(key: str, value: str) -> None:
    """添加单个标签建议"""
    await update_tag_suggestions([{"key": key, "value": value}])


async def get_tag_keys() -> list[str]:
    """获取所有标签键"""
    suggestions = await get_tag_suggestions()
    return list(suggestions.keys())


async def get_tag_values(key: str) -> list[str]:
    """获取指定键的所有值"""
    suggestions = await get_tag_suggestions()
    return suggestions.get(key, [])
