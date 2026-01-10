"""Redis 客户端工具 - 支付系统专用"""

import asyncio
import json
import time
from typing import Any

from app.config import get_settings
from app.core.logger import logger

settings = get_settings()

# Redis 客户端（延迟初始化）
_redis_client = None
_redis_lock = asyncio.Lock()


async def get_redis():
    """获取 Redis 客户端"""
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    async with _redis_lock:
        if _redis_client is not None:
            return _redis_client

        if not settings.redis_url:
            logger.warning("REDIS_URL 未配置")
            return None

        try:
            import redis.asyncio as redis

            _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
            await _redis_client.ping()
            logger.info("Redis 连接成功")
            return _redis_client
        except Exception as e:
            logger.warning(f"Redis 连接失败: {e}")
            return None


async def close_redis():
    """关闭 Redis 连接"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis 连接已关闭")


# ==================== 分布式锁 ====================
class DistributedLock:
    """Redis 分布式锁"""

    def __init__(self, key: str, ttl: int = 60):
        self.key = f"lock:{key}"
        self.ttl = ttl
        self._locked = False
        self._lock_value = f"{time.time()}"

    async def acquire(self) -> bool:
        """获取锁"""
        redis = await get_redis()
        if not redis:
            return False

        try:
            result = await redis.set(self.key, self._lock_value, nx=True, ex=self.ttl)
            self._locked = result is not None
            return self._locked
        except Exception as e:
            logger.error(f"获取分布式锁失败: {e}")
            return False

    async def release(self) -> bool:
        """释放锁"""
        if not self._locked:
            return False

        redis = await get_redis()
        if not redis:
            return False

        try:
            # 使用 Lua 脚本确保只删除自己的锁
            script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            result = await redis.eval(script, 1, self.key, self._lock_value)
            self._locked = False
            return result == 1
        except Exception as e:
            logger.error(f"释放分布式锁失败: {e}")
            return False

    async def extend(self, ttl: int | None = None) -> bool:
        """延长锁的过期时间"""
        if not self._locked:
            return False

        redis = await get_redis()
        if not redis:
            return False

        try:
            script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("expire", KEYS[1], ARGV[2])
            else
                return 0
            end
            """
            result = await redis.eval(script, 1, self.key, self._lock_value, ttl or self.ttl)
            return result == 1
        except Exception as e:
            logger.error(f"延长锁失败: {e}")
            return False

    async def __aenter__(self):
        if not await self.acquire():
            raise RuntimeError(f"无法获取锁: {self.key}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.release()


# ==================== 待支付订单管理 ====================
PENDING_ORDERS_KEY = "payment:pending_orders"
ORDER_TIMEOUT = 15 * 60  # 15分钟


async def add_pending_order(order_no: str, payment_provider: str, payment_data: dict) -> bool:
    """添加待支付订单到 Redis"""
    redis = await get_redis()
    if not redis:
        return False

    try:
        data = {
            "order_no": order_no,
            "provider": payment_provider,
            "payment_data": payment_data,
            "created_at": time.time(),
            "expires_at": time.time() + ORDER_TIMEOUT,
        }
        await redis.hset(PENDING_ORDERS_KEY, order_no, json.dumps(data))
        return True
    except Exception as e:
        logger.error(f"添加待支付订单失败: {e}")
        return False


async def get_pending_order(order_no: str) -> dict | None:
    """获取待支付订单"""
    redis = await get_redis()
    if not redis:
        return None

    try:
        data = await redis.hget(PENDING_ORDERS_KEY, order_no)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"获取待支付订单失败: {e}")
        return None


async def remove_pending_order(order_no: str) -> bool:
    """移除待支付订单"""
    redis = await get_redis()
    if not redis:
        return False

    try:
        await redis.hdel(PENDING_ORDERS_KEY, order_no)
        return True
    except Exception as e:
        logger.error(f"移除待支付订单失败: {e}")
        return False


async def get_all_pending_orders() -> list[dict]:
    """获取所有待支付订单"""
    redis = await get_redis()
    if not redis:
        return []

    try:
        all_data = await redis.hgetall(PENDING_ORDERS_KEY)
        orders = []
        for data in all_data.values():
            orders.append(json.loads(data))
        return orders
    except Exception as e:
        logger.error(f"获取所有待支付订单失败: {e}")
        return []


async def get_expired_orders() -> list[dict]:
    """获取已过期的待支付订单"""
    orders = await get_all_pending_orders()
    now = time.time()
    return [o for o in orders if o.get("expires_at", 0) < now]


# ==================== TRC20 扫描相关 ====================
TRC20_PROCESSED_TXS_KEY = "payment:trc20:processed_txs"
TRC20_SCAN_LOGS_KEY = "payment:trc20:scan_logs"
SCAN_LOGS_TTL = 3 * 24 * 60 * 60  # 3天


async def is_tx_processed(tx_id: str) -> bool:
    """检查交易是否已处理"""
    redis = await get_redis()
    if not redis:
        return False

    try:
        return await redis.sismember(TRC20_PROCESSED_TXS_KEY, tx_id)
    except Exception as e:
        logger.error(f"检查交易是否已处理失败: {e}")
        return False


async def mark_tx_processed(tx_id: str) -> bool:
    """标记交易为已处理"""
    redis = await get_redis()
    if not redis:
        return False

    try:
        await redis.sadd(TRC20_PROCESSED_TXS_KEY, tx_id)
        # 设置过期时间 7 天
        await redis.expire(TRC20_PROCESSED_TXS_KEY, 7 * 24 * 60 * 60)
        return True
    except Exception as e:
        logger.error(f"标记交易为已处理失败: {e}")
        return False


async def add_scan_log(log_data: dict) -> bool:
    """添加扫描日志（使用 Sorted Set，按时间排序）"""
    redis = await get_redis()
    if not redis:
        return False

    try:
        score = time.time()
        await redis.zadd(TRC20_SCAN_LOGS_KEY, {json.dumps(log_data): score})
        # 清理 3 天前的日志
        cutoff = time.time() - SCAN_LOGS_TTL
        await redis.zremrangebyscore(TRC20_SCAN_LOGS_KEY, "-inf", cutoff)
        return True
    except Exception as e:
        logger.error(f"添加扫描日志失败: {e}")
        return False


async def get_scan_logs(limit: int = 100, offset: int = 0) -> list[dict]:
    """获取扫描日志（最新的在前）"""
    redis = await get_redis()
    if not redis:
        return []

    try:
        data = await redis.zrevrange(TRC20_SCAN_LOGS_KEY, offset, offset + limit - 1)
        return [json.loads(item) for item in data]
    except Exception as e:
        logger.error(f"获取扫描日志失败: {e}")
        return []


async def get_scan_logs_count() -> int:
    """获取扫描日志总数"""
    redis = await get_redis()
    if not redis:
        return 0

    try:
        return await redis.zcard(TRC20_SCAN_LOGS_KEY)
    except Exception as e:
        logger.error(f"获取扫描日志总数失败: {e}")
        return 0


# ==================== TRC20 待匹配订单 ====================
TRC20_PENDING_AMOUNTS_KEY = "payment:trc20:pending_amounts"


async def add_trc20_pending_amount(amount: str, order_no: str) -> bool:
    """添加待匹配的金额（金额 -> 订单号映射）"""
    redis = await get_redis()
    if not redis:
        return False

    try:
        # 使用 amount 作为 key，存储订单号
        key = f"{TRC20_PENDING_AMOUNTS_KEY}:{amount}"
        await redis.set(key, order_no, ex=ORDER_TIMEOUT)
        return True
    except Exception as e:
        logger.error(f"添加待匹配金额失败: {e}")
        return False


async def get_order_by_trc20_amount(amount: str) -> str | None:
    """通过金额查找订单号"""
    redis = await get_redis()
    if not redis:
        return None

    try:
        key = f"{TRC20_PENDING_AMOUNTS_KEY}:{amount}"
        return await redis.get(key)
    except Exception as e:
        logger.error(f"通过金额查找订单失败: {e}")
        return None


async def remove_trc20_pending_amount(amount: str) -> bool:
    """移除待匹配金额"""
    redis = await get_redis()
    if not redis:
        return False

    try:
        key = f"{TRC20_PENDING_AMOUNTS_KEY}:{amount}"
        await redis.delete(key)
        return True
    except Exception as e:
        logger.error(f"移除待匹配金额失败: {e}")
        return False
