"""日志配置"""

import sys
from pathlib import Path

from loguru import logger

# 移除默认处理器
logger.remove()

# 日志格式
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

# 简洁格式 (用于控制台)
CONSOLE_FORMAT = (
    "<green>{time:HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)


def setup_logging(
    level: str = "INFO",
    log_file: str | None = None,
    rotation: str = "10 MB",
    retention: str = "7 days",
) -> None:
    """
    配置日志系统

    Args:
        level: 日志级别
        log_file: 日志文件路径
        rotation: 日志轮转大小
        retention: 日志保留时间
    """
    # 控制台输出
    logger.add(
        sys.stdout,
        format=CONSOLE_FORMAT,
        level=level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # 文件输出
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # 常规日志
        logger.add(
            log_file,
            format=LOG_FORMAT,
            level=level,
            rotation=rotation,
            retention=retention,
            compression="zip",
            encoding="utf-8",
        )

        # 错误日志单独存放
        error_log = log_path.parent / f"{log_path.stem}_error{log_path.suffix}"
        logger.add(
            str(error_log),
            format=LOG_FORMAT,
            level="ERROR",
            rotation=rotation,
            retention=retention,
            compression="zip",
            encoding="utf-8",
        )

    logger.info("日志系统初始化完成")
