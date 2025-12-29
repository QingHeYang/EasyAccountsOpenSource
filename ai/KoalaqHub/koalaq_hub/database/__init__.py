"""
数据库层模块
提供基于Repository模式的数据访问层，支持多种数据库后端
"""

# 基础组件
from .base.base_repository import BaseRepository
from .base.database_connection import DatabaseConnection

# 工厂层
from .factory.repository_factory import RepositoryFactory
from .repositories.conversation_repository import ConversationRepository
from .repositories.message_repository import MessageRepository
from .repositories.summary_repository import SummaryRepository
from .repositories.token_repository import TokenRepository

# Repository层
from .repositories.user_repository import UserRepository

# 保持向后兼容性，但逐步废弃
from .sqlite_storage import SqliteStorage

__all__ = [
    # 基础组件
    "DatabaseConnection",
    "BaseRepository",
    # Repository层
    "UserRepository",
    "ConversationRepository",
    "MessageRepository",
    "SummaryRepository",
    "TokenRepository",
    # 工厂层
    "RepositoryFactory",
    # 兼容性（逐步废弃）
    "SqliteStorage",
]
