"""
用户Repository
负责用户相关的所有数据库操作
"""

import sqlite3
from typing import Any, Dict, List, Optional

from ...core.logging_utils import ManagerLogger
from ...models.data_models import User
from ..base.base_repository import BaseRepository
from ..base.database_connection import DatabaseConnection


class UserRepository(BaseRepository):
    """用户数据访问对象"""
    def __init__(self, db_connection: DatabaseConnection):
        super().__init__(db_connection)
        self.logger = ManagerLogger("UserRepository")

    def add_user(self, user: User) -> None:
        """添加新用户到数据库

        Args:
            user: 用户对象

        Raises:
            sqlite3.IntegrityError: 用户ID已存在
            Exception: 其他数据库错误
        """
        try:
            sql = """
                INSERT INTO users (user_id, username, created_at, extra_data, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                user.user_id,
                user.username,
                user.created_at,
                user.extra_data,
                getattr(user, "total_tokens", 0),
                getattr(user, "prompt_tokens", 0),
                getattr(user, "completion_tokens", 0),
                getattr(user, "reasoning_tokens", 0),
            )

            self._execute_insert(sql, params)
            self.logger.info(f"用户添加成功: {user.username} (ID: {user.user_id})")

        except sqlite3.IntegrityError as e:
            self.logger.warning(f"用户ID已存在: {user.user_id}")
            raise e
        except Exception as e:
            self.logger.error(f"添加用户失败: {e}")
            raise e

    def get_user(self, user_id: str) -> Optional[User]:
        """根据用户ID获取用户信息

        Args:
            user_id: 用户ID

        Returns:
            Optional[User]: 用户对象，如果不存在则返回None
        """
        try:
            sql = """
                SELECT user_id, username, created_at, extra_data, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens
                FROM users 
                WHERE user_id = ?
            """
            row = self._fetch_one(sql, (user_id,))

            if row:
                user_data = self._row_to_dict(row)
                self.logger.debug(f"获取用户成功: {user_data['username']} (ID: {user_id})")
                return User.from_dict(user_data)
            else:
                self.logger.warning(f"用户不存在: {user_id}")
                return None

        except Exception as e:
            self.logger.error(f"获取用户失败 (ID: {user_id}): {e}")
            raise e

    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户信息

        Args:
            username: 用户名

        Returns:
            Optional[User]: 用户对象，如果不存在则返回None
        """
        try:
            sql = """
                SELECT user_id, username, created_at, extra_data, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens
                FROM users 
                WHERE username = ?
            """
            row = self._fetch_one(sql, (username,))

            if row:
                user_data = self._row_to_dict(row)
                self.logger.debug(f"根据用户名获取用户成功: {username}")
                return User.from_dict(user_data)
            else:
                self.logger.warning(f"用户名不存在: {username}")
                return None

        except Exception as e:
            self.logger.error(f"根据用户名获取用户失败 ({username}): {e}")
            raise e

    def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """更新用户信息

        Args:
            user_id: 用户ID
            updates: 要更新的字段字典

        Returns:
            bool: 更新是否成功
        """
        try:
            if not updates:
                self.logger.warning("没有要更新的字段")
                return False

            set_clause, params = self._build_update_clause(updates)
            sql = f"UPDATE users {set_clause} WHERE user_id = ?"
            params = params + (user_id,)

            rows_affected = self._execute_update(sql, params)

            if rows_affected > 0:
                self.logger.info(f"用户更新成功: {user_id}, 字段: {list(updates.keys())}")
                return True
            else:
                self.logger.warning(f"用户不存在或无需更新: {user_id}")
                return False

        except Exception as e:
            self.logger.error(f"更新用户失败 (ID: {user_id}): {e}")
            raise e

    def add_tokens_to_user(self, user_id: str, total_tokens: int, prompt_tokens: int = 0, completion_tokens: int = 0, reasoning_tokens: int = 0) -> None:
        """为用户累加Token数量

        Args:
            user_id: 用户ID
            total_tokens: 要累加的总Token数量
            prompt_tokens: 要累加的提示Token数量
            completion_tokens: 要累加的完成Token数量
            reasoning_tokens: 要累加的推理Token数量
        """
        try:
            sql = """
                UPDATE users 
                SET total_tokens = total_tokens + ?, 
                    prompt_tokens = prompt_tokens + ?, 
                    completion_tokens = completion_tokens + ?, 
                    reasoning_tokens = reasoning_tokens + ?
                WHERE user_id = ?
            """
            rows_affected = self._execute_update(sql, (total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, user_id))

            if rows_affected > 0:
                self.logger.info(f"用户Token累加成功: {user_id}, total_tokens: {total_tokens}, prompt_tokens: {prompt_tokens}, completion_tokens: {completion_tokens}, reasoning_tokens: {reasoning_tokens}")
            else:
                self.logger.warning(f"用户不存在，Token累加失败: {user_id}")

        except Exception as e:
            self.logger.error(f"用户Token累加失败 (ID: {user_id}, total_tokens: {total_tokens}): {e}")
            raise e

    def get_user_token_stats(self, user_id: str) -> Dict[str, Any]:
        """获取用户Token统计信息

        Args:
            user_id: 用户ID

        Returns:
            Dict[str, Any]: 用户Token统计信息
        """
        try:
            # 获取用户基本信息和总Token数
            sql = """
                SELECT username, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, created_at
                FROM users 
                WHERE user_id = ?
            """
            user_row = self._fetch_one(sql, (user_id,))

            if not user_row:
                return {}

            # 获取用户的对话数量
            conversation_sql = """
                SELECT COUNT(*) as conversation_count, SUM(total_tokens) as conversation_tokens
                FROM conversations 
                WHERE user_id = ?
            """
            conv_row = self._fetch_one(conversation_sql, (user_id,))

            # 获取用户的消息数量（通过rounds关联）
            message_sql = """
                SELECT COUNT(m.message_id) as message_count
                FROM messages m
                JOIN rounds r ON m.round_id = r.round_id
                JOIN conversations c ON r.conversation_id = c.conversation_id
                WHERE c.user_id = ?
            """
            msg_row = self._fetch_one(message_sql, (user_id,))

            stats = {
                "user_id": user_id,
                "username": user_row["username"],
                "total_tokens": user_row["total_tokens"] or 0,
                "prompt_tokens": user_row["prompt_tokens"] or 0,
                "completion_tokens": user_row["completion_tokens"] or 0,
                "reasoning_tokens": user_row["reasoning_tokens"] or 0,
                "created_at": user_row["created_at"],
                "conversation_count": conv_row["conversation_count"] or 0,
                "conversation_tokens": conv_row["conversation_tokens"] or 0,
                "message_count": msg_row["message_count"] or 0,
            }

            self.logger.debug(f"获取用户Token统计成功: {user_id}")
            return stats

        except Exception as e:
            self.logger.error(f"获取用户Token统计失败 (ID: {user_id}): {e}")
            raise e

    def delete_user(self, user_id: str) -> bool:
        """删除用户（软删除，实际项目中可能需要保留数据）

        Args:
            user_id: 用户ID

        Returns:
            bool: 删除是否成功
        """
        try:
            sql = "DELETE FROM users WHERE user_id = ?"
            rows_affected = self._execute_update(sql, (user_id,))

            if rows_affected > 0:
                self.logger.info(f"用户删除成功: {user_id}")
                return True
            else:
                self.logger.warning(f"用户不存在，删除失败: {user_id}")
                return False

        except Exception as e:
            self.logger.error(f"删除用户失败 (ID: {user_id}): {e}")
            raise e

    def list_users(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """获取用户列表

        Args:
            limit: 返回记录数限制
            offset: 偏移量

        Returns:
            List[Dict[str, Any]]: 用户列表
        """
        try:
            sql = """
                SELECT user_id, username, created_at, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens
                FROM users 
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            rows = self._fetch_all(sql, (limit, offset))

            users = [self._row_to_dict(row) for row in rows]
            self.logger.debug(f"获取用户列表成功，共{len(users)}个用户")
            return users

        except Exception as e:
            self.logger.error(f"获取用户列表失败: {e}")
            raise e

    def get_user_count(self) -> int:
        """获取用户总数

        Returns:
            int: 用户总数
        """
        try:
            sql = "SELECT COUNT(*) as count FROM users"
            row = self._fetch_one(sql)
            count = row["count"] if row else 0

            self.logger.debug(f"获取用户总数: {count}")
            return count

        except Exception as e:
            self.logger.error(f"获取用户总数失败: {e}")
            raise e
