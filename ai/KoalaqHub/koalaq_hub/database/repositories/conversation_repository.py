"""
对话Repository
负责对话(conversations)和轮次(rounds)相关的所有数据库操作
"""

import datetime
import sqlite3
from typing import List, Optional

from ...core.logging_utils import ManagerLogger
from ...models.data_models import Conversation, Round
from ..base.base_repository import BaseRepository
from ..base.database_connection import DatabaseConnection


class ConversationRepository(BaseRepository):
    """对话和轮次数据访问对象"""
    def __init__(self, db_connection: DatabaseConnection):
        super().__init__(db_connection)
        self.logger = ManagerLogger("ConversationRepository")

    # ==================== 对话(Conversations)操作 ====================

    def create_conversation(self, user_id: str, conversation_id: str, application_name: str, 
                          is_agent_call: int = 0, parent_conversation_id: str = None) -> None:
        """创建新对话

        Args:
            user_id: 用户ID
            conversation_id: 对话ID
            application_name: 应用名称
            is_agent_call: 是否为agent调用创建的对话（默认0）
            parent_conversation_id: 父对话ID（如果是agent调用）
        """
        try:
            now = datetime.datetime.now().isoformat()
            sql = """
                INSERT INTO conversations (conversation_id, user_id, created_at, updated_at, 
                                         application_name, is_agent_call, parent_conversation_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            self._execute_insert(sql, (conversation_id, user_id, now, now, application_name, 
                                     is_agent_call, parent_conversation_id))
            self.logger.info(f"对话创建成功: {conversation_id}", {
                "is_agent_call": is_agent_call,
                "parent_conversation_id": parent_conversation_id
            })

        except sqlite3.IntegrityError:
            self.logger.warning(f"对话已存在: {conversation_id}")
        except Exception as e:
            self.logger.error(f"创建对话失败: {e}")
            raise e

    def get_conversation(self, conversation_id: str, user_id: str = None, application_name: str = None) -> Optional[Conversation]:
        """获取对话信息

        Args:
            conversation_id: 对话ID
            user_id: 用户ID（可选，用于权限验证）
            application_name: 应用名称（可选，用于过滤）
        Returns:
            Optional[Conversation]: 对话对象，如果不存在则返回None
        """
        try:
            if user_id:
                sql = """
                    SELECT conversation_id, user_id, title, summary, created_at, updated_at, tags, application_name, 
                           total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, is_agent_call, parent_conversation_id
                    FROM conversations
                    WHERE conversation_id = ? AND user_id = ? AND enabled = 1
                """
                params = (conversation_id, user_id)
            else:
                sql = """
                    SELECT conversation_id, user_id, title, summary, created_at, updated_at, tags, application_name, 
                           total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, is_agent_call, parent_conversation_id
                    FROM conversations
                    WHERE conversation_id = ? AND enabled = 1
                """
                params = (conversation_id,)

            row = self._fetch_one(sql, params)

            if row:
                conversation_data = self._row_to_dict(row)
                self.logger.debug(f"获取对话成功: {conversation_id}")
                return Conversation.from_dict(conversation_data)
            else:
                self.logger.warning(f"对话不存在: {conversation_id}")
                return None

        except Exception as e:
            self.logger.error(f"获取对话失败 (ID: {conversation_id}): {e}")
            raise e

    def get_conversation_recorder(self, user_id: str, conversation_id: str) -> Optional[Conversation]:
        """获取对话信息（兼容原方法名）

        Args:
            user_id: 用户ID
            conversation_id: 对话ID

        Returns:
            Optional[Conversation]: 对话对象，如果不存在则返回None
        """
        return self.get_conversation(conversation_id, user_id)

    def get_all_conversations_recorder(self, user_id: str) -> List[Conversation]:
        """获取用户的所有对话（兼容原方法名）

        Args:
            user_id: 用户ID

        Returns:
            List[Conversation]: 对话列表
        """
        return self.get_user_conversations(user_id)

    def get_user_conversations(self, user_id: str, application_names: List[str] = None, limit: int = 50, offset: int = 0) -> List[Conversation]:
        """获取用户的对话列表

        Args:
            user_id: 用户ID
            application_names: 应用名称列表，用于筛选对话
            limit: 返回记录数限制
            offset: 偏移量

        Returns:
            List[Conversation]: 对话列表
        """
        try:
            # 基础SQL查询（只查询未删除的对话，并过滤掉子对话）
            sql = """
                SELECT 
                    c.conversation_id, c.user_id, c.title, c.summary, 
                    c.created_at, c.updated_at, c.tags, c.application_name,
                    c.total_tokens, c.prompt_tokens, c.completion_tokens, c.reasoning_tokens,
                    c.is_agent_call, c.parent_conversation_id,
                    COALESCE(r.rounds_count, 0) as rounds_count
                FROM conversations c
                LEFT JOIN (
                    SELECT conversation_id, COUNT(*) as rounds_count
                    FROM rounds
                    GROUP BY conversation_id
                ) r ON c.conversation_id = r.conversation_id
                WHERE c.user_id = ? AND c.enabled = 1
                -- 过滤掉agent执行产生的子对话
                AND c.is_agent_call = 0
            """
            
            params = [user_id]
            
            # 如果指定了应用名称列表，添加筛选条件
            if application_names:
                placeholders = ",".join(["?" for _ in application_names])
                sql += f" AND c.application_name IN ({placeholders})"
                params.extend(application_names)
            
            sql += " ORDER BY c.updated_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            rows = self._fetch_all(sql, params)

            conversations = [Conversation.from_dict(self._row_to_dict(row)) for row in rows]
            self.logger.debug(f"获取用户对话列表成功: {user_id}, 应用筛选: {application_names}, 共{len(conversations)}个对话")
            return conversations

        except Exception as e:
            self.logger.error(f"获取用户对话列表失败 (用户ID: {user_id}, 应用筛选: {application_names}): {e}")
            raise e

    def get_user_conversations_count(self, user_id: str, application_names: List[str] = None) -> int:
        """获取用户的对话总数

        Args:
            user_id: 用户ID
            application_names: 应用名称列表，用于筛选对话

        Returns:
            int: 对话总数
        """
        try:
            sql = """
                SELECT COUNT(*) as count
                FROM conversations
                WHERE user_id = ? AND enabled = 1 AND is_agent_call = 0
            """
            params = [user_id]
            
            # 如果指定了应用名称列表，添加筛选条件
            if application_names:
                placeholders = ",".join(["?" for _ in application_names])
                sql += f" AND application_name IN ({placeholders})"
                params.extend(application_names)
            
            row = self._fetch_one(sql, params)
            count = row["count"] if row else 0

            self.logger.debug(f"获取用户对话总数: {user_id}, 应用筛选: {application_names}, 总数: {count}")
            return count

        except Exception as e:
            self.logger.error(f"获取用户对话总数失败 (用户ID: {user_id}, 应用筛选: {application_names}): {e}")
            raise e

    def update_conversation_title(self, conversation_id: str, title: str) -> None:
        """更新对话标题

        Args:
            conversation_id: 对话ID
            title: 新标题
        """
        try:
            now = datetime.datetime.now().isoformat()
            sql = """
                UPDATE conversations 
                SET title = ?, updated_at = ?
                WHERE conversation_id = ?
            """
            rows_affected = self._execute_update(sql, (title, now, conversation_id))

            if rows_affected > 0:
                self.logger.info(f"对话标题更新成功: {conversation_id}")
            else:
                self.logger.warning(f"对话不存在，标题更新失败: {conversation_id}")

        except Exception as e:
            self.logger.error(f"更新对话标题失败: {e}")
            raise e

    def update_coversation_summary(self, conversation_id: str, summary: str) -> None:
        """更新对话摘要（保持原方法名的拼写错误以兼容）

        Args:
            conversation_id: 对话ID
            summary: 新摘要
        """
        return self.update_conversation_summary(conversation_id, summary)

    def update_conversation_summary(self, conversation_id: str, summary: str) -> None:
        """更新对话摘要

        Args:
            conversation_id: 对话ID
            summary: 新摘要
        """
        try:
            now = datetime.datetime.now().isoformat()
            sql = """
                UPDATE conversations 
                SET summary = ?, updated_at = ?
                WHERE conversation_id = ?
            """
            rows_affected = self._execute_update(sql, (summary, now, conversation_id))

            if rows_affected > 0:
                self.logger.info(f"对话摘要更新成功: {conversation_id}")
            else:
                self.logger.warning(f"对话不存在，摘要更新失败: {conversation_id}")

        except Exception as e:
            self.logger.error(f"更新对话摘要失败: {e}")
            raise e

    def update_coversation_time(self, conversation_id: str) -> None:
        """更新对话的最后更新时间（保持原方法名的拼写错误以兼容）

        Args:
            conversation_id: 对话ID
        """
        return self.update_conversation_time(conversation_id)

    def update_conversation_time(self, conversation_id: str) -> None:
        """更新对话的最后更新时间

        Args:
            conversation_id: 对话ID
        """
        try:
            now = datetime.datetime.now().isoformat()
            sql = """
                UPDATE conversations 
                SET updated_at = ?
                WHERE conversation_id = ?
            """
            rows_affected = self._execute_update(sql, (now, conversation_id))

            if rows_affected > 0:
                self.logger.debug(f"对话时间更新成功: {conversation_id}")
            else:
                self.logger.warning(f"对话不存在，时间更新失败: {conversation_id}")

        except Exception as e:
            self.logger.error(f"更新对话时间失败: {e}")
            raise e

    def add_tokens_to_conversation(self, conversation_id: str, total_tokens: int, prompt_tokens: int = 0, completion_tokens: int = 0, reasoning_tokens: int = 0) -> None:
        """为对话累加Token数量

        Args:
            conversation_id: 对话ID
            total_tokens: 要累加的总Token数量
            prompt_tokens: 要累加的提示Token数量
            completion_tokens: 要累加的完成Token数量
            reasoning_tokens: 要累加的推理Token数量
        """
        try:
            now = datetime.datetime.now().isoformat()
            sql = """
                UPDATE conversations 
                SET total_tokens = total_tokens + ?, 
                    prompt_tokens = prompt_tokens + ?, 
                    completion_tokens = completion_tokens + ?, 
                    reasoning_tokens = reasoning_tokens + ?, 
                    updated_at = ?
                WHERE conversation_id = ?
            """
            rows_affected = self._execute_update(sql, (total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, now, conversation_id))

            if rows_affected > 0:
                self.logger.info(f"对话Token累加成功: {conversation_id}, total_tokens: {total_tokens}, prompt_tokens: {prompt_tokens}, completion_tokens: {completion_tokens}, reasoning_tokens: {reasoning_tokens}")
            else:
                self.logger.warning(f"对话不存在，Token累加失败: {conversation_id}")

        except Exception as e:
            self.logger.error(f"对话Token累加失败 (ID: {conversation_id}, total_tokens: {total_tokens}): {e}")
            raise e

    def delete_conversation(self, conversation_id: str) -> bool:
        """软删除对话（设置enabled=0，不真正删除数据）

        Args:
            conversation_id: 对话ID

        Returns:
            bool: 删除是否成功
        """
        try:
            now = datetime.datetime.now().isoformat()
            sql = """
                UPDATE conversations 
                SET enabled = 0, updated_at = ?
                WHERE conversation_id = ? AND enabled = 1
            """
            rows_affected = self._execute_update(sql, (now, conversation_id))

            if rows_affected > 0:
                self.logger.info(f"对话软删除成功: {conversation_id}")
                return True
            else:
                self.logger.warning(f"对话不存在或已删除，软删除失败: {conversation_id}")
                return False

        except Exception as e:
            self.logger.error(f"软删除对话失败 (ID: {conversation_id}): {e}")
            raise e

    def restore_conversation(self, conversation_id: str) -> bool:
        """恢复已删除的对话

        Args:
            conversation_id: 对话ID

        Returns:
            bool: 恢复是否成功
        """
        try:
            now = datetime.datetime.now().isoformat()
            sql = """
                UPDATE conversations 
                SET enabled = 1, updated_at = ?
                WHERE conversation_id = ? AND enabled = 0
            """
            rows_affected = self._execute_update(sql, (now, conversation_id))

            if rows_affected > 0:
                self.logger.info(f"对话恢复成功: {conversation_id}")
                return True
            else:
                self.logger.warning(f"对话不存在或未删除，恢复失败: {conversation_id}")
                return False

        except Exception as e:
            self.logger.error(f"恢复对话失败 (ID: {conversation_id}): {e}")
            raise e

    def permanently_delete_conversation(self, conversation_id: str) -> bool:
        """永久删除对话（级联删除相关轮次和消息）

        Args:
            conversation_id: 对话ID

        Returns:
            bool: 删除是否成功
        """
        try:
            # SQLite的外键约束会自动级联删除相关记录
            sql = "DELETE FROM conversations WHERE conversation_id = ?"
            rows_affected = self._execute_update(sql, (conversation_id,))

            if rows_affected > 0:
                self.logger.info(f"对话永久删除成功: {conversation_id}")
                return True
            else:
                self.logger.warning(f"对话不存在，永久删除失败: {conversation_id}")
                return False

        except Exception as e:
            self.logger.error(f"永久删除对话失败 (ID: {conversation_id}): {e}")
            raise e

    # ==================== 轮次(Rounds)操作 ====================

    def create_round(self, conversation_id: str, round_id: str) -> None:
        """创建新轮次

        Args:
            conversation_id: 对话ID
            round_id: 轮次ID
        """
        try:
            now = datetime.datetime.now().isoformat()
            sql = """
                INSERT INTO rounds (round_id, conversation_id, created_at)
                VALUES (?, ?, ?)
            """
            self._execute_insert(sql, (round_id, conversation_id, now))
            self.logger.info(f"轮次创建成功: {round_id}")

        except Exception as e:
            self.logger.error(f"创建轮次失败: {e}")
            raise e

    def get_round(self, round_id: str, conversation_id: str = None) -> Optional[Round]:
        """获取轮次信息

        Args:
            round_id: 轮次ID
            conversation_id: 对话ID（可选，用于验证）

        Returns:
            Optional[Round]: 轮次对象，如果不存在则返回None
        """
        try:
            if conversation_id:
                sql = """
                    SELECT round_id, conversation_id, summary, created_at, user_rating, extra_data, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, execution_time
                    FROM rounds
                    WHERE round_id = ? AND conversation_id = ?
                """
                params = (round_id, conversation_id)
            else:
                sql = """
                    SELECT round_id, conversation_id, summary, created_at, user_rating, extra_data, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, execution_time
                    FROM rounds
                    WHERE round_id = ?
                """
                params = (round_id,)

            row = self._fetch_one(sql, params)

            if row:
                round_data = self._row_to_dict(row)
                self.logger.debug(f"获取轮次成功: {round_id}")
                return Round.from_dict(round_data)
            else:
                self.logger.warning(f"轮次不存在: {round_id}")
                return None

        except Exception as e:
            self.logger.error(f"获取轮次失败 (ID: {round_id}): {e}")
            raise e

    def get_rounds_by_conversation(self, conversation_id: str, limit: int = None) -> List[Round]:
        """获取对话的所有轮次

        Args:
            conversation_id: 对话ID
            limit: 返回记录数限制（可选）

        Returns:
            List[Round]: 轮次列表
        """
        try:
            if limit:
                sql = """
                    SELECT round_id, conversation_id, summary, created_at, user_rating, extra_data, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, execution_time
                    FROM rounds
                    WHERE conversation_id = ?
                    ORDER BY created_at ASC
                    LIMIT ?
                """
                params = (conversation_id, limit)
            else:
                sql = """
                    SELECT round_id, conversation_id, summary, created_at, user_rating, extra_data, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, execution_time
                    FROM rounds
                    WHERE conversation_id = ?
                    ORDER BY created_at ASC
                """
                params = (conversation_id,)

            rows = self._fetch_all(sql, params)

            rounds = [Round.from_dict(self._row_to_dict(row)) for row in rows]
            self.logger.debug(f"获取对话轮次列表成功: {conversation_id}, 共{len(rounds)}个轮次")
            return rounds

        except Exception as e:
            self.logger.error(f"获取对话轮次列表失败 (对话ID: {conversation_id}): {e}")
            raise e

    def get_round_recorder(self, conversation_id: str, round_id: str) -> Optional[Round]:
        """获取轮次信息（兼容原方法名）

        Args:
            conversation_id: 对话ID
            round_id: 轮次ID

        Returns:
            Optional[Round]: 轮次对象，如果不存在则返回None
        """
        return self.get_round(round_id, conversation_id)

    def get_rounds_recorder_by_memory_window(self, conversation_id: str, memory_window: int) -> List[Round]:
        """获取对话的最近N个轮次（兼容原方法名）

        Args:
            conversation_id: 对话ID
            memory_window: 内存窗口大小

        Returns:
            List[Round]: 最近的轮次列表
        """
        return self.get_rounds_by_memory_window(conversation_id, memory_window)

    def get_all_rounds_recorder(self, conversation_id: str) -> List[Round]:
        """获取对话的所有轮次（兼容原方法名）

        Args:
            conversation_id: 对话ID

        Returns:
            List[Round]: 轮次列表
        """
        return self.get_rounds_by_conversation(conversation_id)
    
    def get_rounds_count(self, conversation_id: str) -> int:
        """获取指定会话的轮次数量"""
        try:
            sql = """
                SELECT COUNT(*) FROM rounds WHERE conversation_id = ?
            """
            params = (conversation_id,)
            result = self._fetch_one(sql, params)
            # _fetch_one返回元组，COUNT(*)结果在第一个位置
            return result[0] if result else 0
        except Exception as e:
            self.logger.error(f"获取轮次数量失败: {e}")
            return 0

    def get_rounds_by_memory_window(self, conversation_id: str, memory_window: int) -> List[Round]:
        """获取对话的最近N个轮次（用于内存窗口）

        Args:
            conversation_id: 对话ID
            memory_window: 内存窗口大小

        Returns:
            List[Round]: 最近的轮次列表（按时间倒序）
        """
        try:
            sql = """
                SELECT round_id, conversation_id, summary, created_at, user_rating, extra_data, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, execution_time
                FROM rounds
                WHERE conversation_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """
            rows = self._fetch_all(sql, (conversation_id, memory_window))

            rounds = [Round.from_dict(self._row_to_dict(row)) for row in rows]
            self.logger.debug(f"获取内存窗口轮次成功: {conversation_id}, 窗口大小: {memory_window}")
            return rounds

        except Exception as e:
            self.logger.error(f"获取内存窗口轮次失败 (对话ID: {conversation_id}): {e}")
            raise e

    def update_round_summary(self, round_id: str, summary: str) -> None:
        """更新轮次摘要

        Args:
            round_id: 轮次ID
            summary: 新摘要
        """
        try:
            sql = """
                UPDATE rounds 
                SET summary = ?
                WHERE round_id = ?
            """
            rows_affected = self._execute_update(sql, (summary, round_id))

            if rows_affected > 0:
                self.logger.info(f"轮次摘要更新成功: {round_id}")
            else:
                self.logger.warning(f"轮次不存在，摘要更新失败: {round_id}")

        except Exception as e:
            self.logger.error(f"更新轮次摘要失败: {e}")
            raise e

    def add_tokens_to_round(self, round_id: str, total_tokens: int, prompt_tokens: int = 0, completion_tokens: int = 0, reasoning_tokens: int = 0) -> None:
        """为轮次累加Token数量

        Args:
            round_id: 轮次ID
            total_tokens: 要累加的总Token数量
            prompt_tokens: 要累加的提示Token数量
            completion_tokens: 要累加的完成Token数量
            reasoning_tokens: 要累加的推理Token数量
        """
        try:
            sql = """
                UPDATE rounds 
                SET total_tokens = total_tokens + ?, 
                    prompt_tokens = prompt_tokens + ?, 
                    completion_tokens = completion_tokens + ?, 
                    reasoning_tokens = reasoning_tokens + ?
                WHERE round_id = ?
            """
            rows_affected = self._execute_update(sql, (total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, round_id))

            if rows_affected > 0:
                self.logger.info(f"轮次Token累加成功: {round_id}, total_tokens: {total_tokens}, prompt_tokens: {prompt_tokens}, completion_tokens: {completion_tokens}, reasoning_tokens: {reasoning_tokens}")
            else:
                self.logger.warning(f"轮次不存在，Token累加失败: {round_id}")

        except Exception as e:
            self.logger.error(f"轮次Token累加失败 (ID: {round_id}, total_tokens: {total_tokens}): {e}")
            raise e

    def update_round_execution_time(self, round_id: str, execution_time: float) -> None:
        """更新轮次执行时间

        Args:
            round_id: 轮次ID
            execution_time: 执行时间（秒）
        """
        try:
            # 保留两位小数
            execution_time_rounded = round(execution_time, 2)
            sql = """
                UPDATE rounds 
                SET execution_time = ?
                WHERE round_id = ?
            """
            rows_affected = self._execute_update(sql, (execution_time_rounded, round_id))

            if rows_affected > 0:
                self.logger.info(f"轮次执行时间更新成功: {round_id}, 执行时间: {execution_time_rounded}秒")
            else:
                self.logger.warning(f"轮次不存在，执行时间更新失败: {round_id}")

        except Exception as e:
            self.logger.error(f"更新轮次执行时间失败: {e}")
            raise e

    def update_round_rating(self, round_id: str, rating: int) -> None:
        """更新轮次用户评分

        Args:
            round_id: 轮次ID
            rating: 用户评分（1-5）
        """
        try:
            if rating < 1 or rating > 5:
                raise ValueError("评分必须在1-5之间")

            sql = """
                UPDATE rounds 
                SET user_rating = ?
                WHERE round_id = ?
            """
            rows_affected = self._execute_update(sql, (rating, round_id))

            if rows_affected > 0:
                self.logger.info(f"轮次评分更新成功: {round_id}, 评分: {rating}")
            else:
                self.logger.warning(f"轮次不存在，评分更新失败: {round_id}")

        except Exception as e:
            self.logger.error(f"更新轮次评分失败: {e}")
            raise e

    def get_conversation_round_count(self, conversation_id: str) -> int:
        """获取对话的轮次数量

        Args:
            conversation_id: 对话ID

        Returns:
            int: 轮次数量
        """
        try:
            sql = "SELECT COUNT(*) as count FROM rounds WHERE conversation_id = ?"
            row = self._fetch_one(sql, (conversation_id,))
            count = row["count"] if row else 0

            self.logger.debug(f"获取对话轮次数量: {conversation_id}, 数量: {count}")
            return count

        except Exception as e:
            self.logger.error(f"获取对话轮次数量失败 (对话ID: {conversation_id}): {e}")
            raise e
        
    def get_conversation_title(self, conversation_id: str) -> str:
        """获取对话标题

        Args:
            conversation_id: 对话ID
        """
        return self.get_conversation(conversation_id).title
