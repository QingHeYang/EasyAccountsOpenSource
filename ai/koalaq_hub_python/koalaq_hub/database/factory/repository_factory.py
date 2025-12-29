"""
Repository工厂类
统一管理所有Repository实例，提供单例模式和依赖注入
"""

from threading import Lock

from ...core.logging_utils import ManagerLogger
from ..base.database_connection import DatabaseConnection
from ..repositories.conversation_repository import ConversationRepository
from ..repositories.message_repository import MessageRepository
from ..repositories.summary_repository import SummaryRepository
from ..repositories.token_repository import TokenRepository
from ..repositories.user_repository import UserRepository


class RepositoryFactory:
    """Repository工厂类 - 单例模式，管理所有Repository实例"""

    _instance = None
    _lock = Lock()

    def __new__(cls, db_connection: DatabaseConnection = None):
        """单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_connection: DatabaseConnection = None):
        """初始化Repository工厂

        Args:
            db_connection: 数据库连接管理器，如果为None则创建新实例
        """
        self.logger = ManagerLogger("RepositoryFactory")
        if self._initialized:
            return

        if db_connection is None:
            self.db_connection = DatabaseConnection()
        else:
            self.db_connection = db_connection

        # Repository实例缓存
        self._repositories = {}
        self._lock = Lock()
        self._initialized = True

        self.logger.info("Repository工厂初始化完成")

    def _get_or_create_repository(self, repo_type: str, repo_class) -> object:
        """获取或创建Repository实例（线程安全）

        Args:
            repo_type: Repository类型标识
            repo_class: Repository类

        Returns:
            object: Repository实例
        """
        if repo_type not in self._repositories:
            with self._lock:
                if repo_type not in self._repositories:
                    self._repositories[repo_type] = repo_class(self.db_connection)
                    self.logger.debug(f"创建Repository实例: {repo_type}")

        return self._repositories[repo_type]

    def get_user_repository(self) -> UserRepository:
        """获取用户Repository实例

        Returns:
            UserRepository: 用户数据访问对象
        """
        return self._get_or_create_repository("user", UserRepository)

    def get_conversation_repository(self) -> ConversationRepository:
        """获取对话Repository实例

        Returns:
            ConversationRepository: 对话数据访问对象
        """
        return self._get_or_create_repository("conversation", ConversationRepository)

    def get_message_repository(self) -> MessageRepository:
        """获取消息Repository实例

        Returns:
            MessageRepository: 消息数据访问对象
        """
        return self._get_or_create_repository("message", MessageRepository)

    def get_summary_repository(self) -> SummaryRepository:
        """获取总结Repository实例

        Returns:
            SummaryRepository: 总结数据访问对象
        """
        return self._get_or_create_repository("summary", SummaryRepository)

    def close(self) -> None:
        """关闭数据库连接（兼容原SqliteStorage方法）"""
        return self.close_all_connections()

    def get_token_repository(self) -> TokenRepository:
        """获取Token统计Repository实例

        Returns:
            TokenRepository: Token统计数据访问对象
        """
        return self._get_or_create_repository("token", TokenRepository)

    def get_all_repositories(self) -> dict:
        """获取所有Repository实例的字典

        Returns:
            dict: 包含所有Repository实例的字典
        """
        return {"user": self.get_user_repository(), "conversation": self.get_conversation_repository(), "message": self.get_message_repository(), "summary": self.get_summary_repository(), "token": self.get_token_repository()}

    def clear_cache(self) -> None:
        """清除Repository实例缓存（主要用于测试）"""
        with self._lock:
            self._repositories.clear()
            self.logger.info("Repository缓存已清除")

    def close_all_connections(self) -> None:
        """关闭所有数据库连接"""
        try:
            self.db_connection.close()
            self.clear_cache()
            self.logger.info("所有数据库连接已关闭")
        except Exception as e:
            self.logger.error(f"关闭数据库连接失败: {e}")

    def health_check(self) -> dict:
        """检查所有Repository的健康状态

        Returns:
            dict: 健康检查结果
        """
        health_status = {"database_connection": False, "repositories": {}, "error_count": 0}

        try:
            # 检查数据库连接
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            health_status["database_connection"] = True

            # 检查各个Repository
            repositories = {"user": self.get_user_repository(), "conversation": self.get_conversation_repository(), "message": self.get_message_repository(), "summary": self.get_summary_repository(), "token": self.get_token_repository()}

            for name, repo in repositories.items():
                try:
                    # 简单测试Repository是否可用
                    if hasattr(repo, "connection") and repo.connection:
                        health_status["repositories"][name] = True
                    else:
                        health_status["repositories"][name] = False
                        health_status["error_count"] += 1
                except Exception as e:
                    health_status["repositories"][name] = False
                    health_status["error_count"] += 1
                    self.logger.warning(f"Repository健康检查失败: {name}, 错误: {e}")

            self.logger.debug("Repository工厂健康检查完成")

        except Exception as e:
            health_status["database_connection"] = False
            health_status["error_count"] += 1
            self.logger.error(f"数据库连接健康检查失败: {e}")

        return health_status

    def get_statistics(self) -> dict:
        """获取Repository工厂统计信息

        Returns:
            dict: 统计信息
        """
        try:
            stats = {"initialized_repositories": len(self._repositories), "available_repositories": ["user", "conversation", "message", "summary", "token"], "database_path": self.db_connection.db_path, "health_check": self.health_check()}

            self.logger.debug("获取Repository工厂统计信息成功")
            return stats

        except Exception as e:
            self.logger.error(f"获取Repository工厂统计信息失败: {e}")
            return {}

    # ==================== 便捷方法 ====================

    def execute_in_transaction(self, func, *args, **kwargs):
        """在事务中执行函数（未来扩展用）

        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            函数执行结果
        """
        # SQLite的自动提交模式下，每个语句都是一个事务
        # 这里预留接口，未来可以实现复杂的事务管理
        try:
            result = func(*args, **kwargs)
            self.logger.debug("事务执行成功")
            return result
        except Exception as e:
            self.logger.error(f"事务执行失败: {e}")
            raise

    def bulk_operations(self, operations: list):
        """批量执行操作（未来扩展用）

        Args:
            operations: 操作列表，每个操作包含(repository_name, method_name, args, kwargs)

        Returns:
            list: 操作结果列表
        """
        results = []
        repositories = self.get_all_repositories()

        for operation in operations:
            try:
                repo_name, method_name, args, kwargs = operation

                if repo_name not in repositories:
                    raise ValueError(f"未知的Repository: {repo_name}")

                repo = repositories[repo_name]
                method = getattr(repo, method_name)
                result = method(*args, **kwargs)
                results.append({"success": True, "result": result})

            except Exception as e:
                results.append({"success": False, "error": str(e)})
                self.logger.error(f"批量操作失败: {operation}, 错误: {e}")

        self.logger.info(f"批量操作完成，成功{sum(1 for r in results if r['success'])}个，失败{sum(1 for r in results if not r['success'])}个")
        return results

    def __del__(self):
        """析构函数，确保资源被正确释放"""
        try:
            self.close_all_connections()
        except:
            pass  # 忽略析构时的错误
