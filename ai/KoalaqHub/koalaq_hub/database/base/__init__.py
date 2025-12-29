"""
数据库基础层
提供数据库连接管理和基础Repository抽象类
"""

from .base_repository import BaseRepository
from .database_connection import DatabaseConnection

__all__ = ["DatabaseConnection", "BaseRepository"]
