"""核心模块"""

from app.core.deps import get_current_admin, get_current_superuser
from app.core.exceptions import (
    AppException,
    BadRequestException,
    ConflictException,
    ForbiddenException,
    InternalServerException,
    NotFoundException,
    UnauthorizedException,
)
from app.core.logger import logger, setup_logging
from app.core.response import PaginatedData, ResponseModel, error_response, success_response
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

__all__ = [
    # Logger
    "logger",
    "setup_logging",
    # Response
    "ResponseModel",
    "PaginatedData",
    "success_response",
    "error_response",
    # Exceptions
    "AppException",
    "BadRequestException",
    "NotFoundException",
    "UnauthorizedException",
    "ForbiddenException",
    "ConflictException",
    "InternalServerException",
    # Security
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    # Dependencies
    "get_current_admin",
    "get_current_superuser",
]
