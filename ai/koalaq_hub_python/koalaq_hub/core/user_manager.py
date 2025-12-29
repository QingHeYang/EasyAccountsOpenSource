import datetime
import uuid
from typing import List, Optional

from ..database.repository_adapter import RepositoryAdapter
from ..models.data_models import User
from .logging_utils import ManagerLogger


class UserManager:
    def __init__(self, storage: RepositoryAdapter):
        self.storage = storage
        # 初始化日志记录器
        self.logger = ManagerLogger("UserManager")

    def register_user(self, username: str) -> User:
        """
        注册一个新用户，并将其存入数据库。
        - 生成唯一的 user_id。
        - 设置创建时间。
        - 调用 storage 保存用户。
        """
        if not username:
            self.logger.error("用户名不能为空")
            raise ValueError("Username cannot be empty")

        new_user = User(user_id=f"user_{str(uuid.uuid4())}", username=username, created_at=datetime.datetime.now().isoformat(), extra_data=None)
        self.storage.add_user(new_user)
        self.logger.info("用户注册成功", {"user_id": new_user.user_id, "username": username})
        return new_user

    def get_user(self, user_id: str) -> Optional[User]:
        """根据 user_id 获取用户信息。"""
        user = self.storage.get_user(user_id)
        if user:
            self.logger.debug("获取用户信息成功", {"user_id": user_id, "username": user.username})
        else:
            self.logger.warning("用户不存在", {"user_id": user_id})
        return user

    def list_users(self, limit: int = 100) -> List[User]:
        """
        获取用户列表

        Args:
            limit: 返回用户数量限制，默认100

        Returns:
            用户列表
        """
        try:
            # 通过RepositoryAdapter获取用户列表
            users = self.storage.get_all_users(limit=limit)
            self.logger.info("获取用户列表成功", {"count": len(users), "limit": limit})
            return users
        except Exception as e:
            self.logger.error("获取用户列表失败", exception=e)
            return []

    def get_user_count(self) -> int:
        """
        获取用户总数

        Returns:
            用户总数
        """
        try:
            count = self.storage.get_user_count()
            self.logger.debug("获取用户总数成功", {"count": count})
            return count
        except Exception as e:
            self.logger.error("获取用户总数失败", exception=e)
            return 0
