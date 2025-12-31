"""
消息Repository
负责消息(messages)相关的所有数据库操作
"""

import json
import warnings
from typing import Any, Dict, List, Optional

from ...core.logging_utils import ManagerLogger
from ...models.message import Message, MessageType
from ..base.base_repository import BaseRepository
from ..base.database_connection import DatabaseConnection


class MessageRepository(BaseRepository):
    """消息数据访问对象"""
    def __init__(self, db_connection: DatabaseConnection):
        super().__init__(db_connection)
        self.logger = ManagerLogger("MessageRepository")

    def _parse_message_row(self, row_dict: Dict[str, Any]) -> Dict[str, Any]:
        """解析消息行数据，处理 attachments JSON 反序列化

        Args:
            row_dict: 从数据库获取的行字典

        Returns:
            Dict[str, Any]: 处理后的字典，attachments 已转换为列表
        """
        if "attachments" in row_dict:
            attachments_str = row_dict.get("attachments")
            if attachments_str:
                try:
                    row_dict["attachments"] = json.loads(attachments_str)
                except (json.JSONDecodeError, TypeError):
                    row_dict["attachments"] = None
            else:
                row_dict["attachments"] = None
        return row_dict

    def _serialize_attachments(self, message: Message) -> str:
        """序列化 attachments 为 JSON 字符串

        Args:
            message: 消息对象

        Returns:
            str: JSON 字符串，无附件时返回空字符串
        """
        if message.attachments:
            return json.dumps([att.to_dict() for att in message.attachments], ensure_ascii=False)
        return ""

    def add_message(self, round_id: str, message: Message) -> int:
        """添加消息到数据库

        Args:
            round_id: 轮次ID
            message: 消息对象

        Returns:
            int: 新插入消息的ID
        """
        try:
            sql = """
                INSERT INTO messages (round_id, role, content, type, timestamp, tool_success, tool_call_ids, tool_call_raw, agent_id, tool_name, sub_conversation_id, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, platform, model, reasoning_content, attachments)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                round_id,
                message.role,
                message.content,
                message.type.value if isinstance(message.type, MessageType) else message.type,
                message.timestamp,
                1 if message.tool_success else 0 if message.tool_success is not None else None,
                message.tool_call_ids,
                message.tool_call_raw,
                message.agent_id,
                message.tool_name,
                message.sub_conversation_id,
                getattr(message, "total_tokens", 0),
                getattr(message, "prompt_tokens", 0),
                getattr(message, "completion_tokens", 0),
                getattr(message, "reasoning_tokens", 0),
                getattr(message, "platform", None),
                getattr(message, "model", None),
                getattr(message, "reasoning_content", ""),
                self._serialize_attachments(message),  # VL 附件
            )

            message_id = self._execute_insert(sql, params)
            # 日志：包含 VL 附件信息
            attachments_count = len(message.attachments) if message.attachments else 0
            self.logger.info(f"消息添加成功: message_id={message_id}, round_id={round_id}, role={message.role}, attachments={attachments_count}")
            return message_id

        except Exception as e:
            self.logger.error(f"添加消息失败: {e}")
            raise e

    def add_tokens_to_message(self, message_id: int, total_tokens: int, platform: str, model: str, prompt_tokens: int = 0, completion_tokens: int = 0, reasoning_tokens: int = 0) -> None:
        """更新消息的Token信息和平台模型信息（兼容原方法名）

        Args:
            message_id: 消息ID
            total_tokens: 总Token数量
            platform: 平台名称
            model: 模型名称
            prompt_tokens: 提示Token数量
            completion_tokens: 完成Token数量
            reasoning_tokens: 推理Token数量
        """
        return self.update_message_tokens(message_id, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, platform, model)

    def get_message(self, message_id: int) -> Optional[Message]:
        """根据消息ID获取消息

        .. deprecated::
            该方法目前未被使用，可能在未来版本中移除。

        Args:
            message_id: 消息ID

        Returns:
            Optional[Message]: 消息对象，如果不存在则返回None
        """
        warnings.warn(
            "get_message() 目前未被使用，可能在未来版本中移除",
            DeprecationWarning,
            stacklevel=2
        )
        try:
            sql = """
                SELECT message_id, round_id, role, content, type, timestamp, tool_success, tool_call_ids, tool_call_raw, agent_id, tool_name, sub_conversation_id, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, platform, model, reasoning_content, attachments
                FROM messages
                WHERE message_id = ?
            """
            row = self._fetch_one(sql, (message_id,))

            if row:
                message_data = self._parse_message_row(self._row_to_dict(row))
                self.logger.debug(f"获取消息成功: message_id={message_id}")
                return Message.from_dict(message_data)
            else:
                self.logger.warning(f"消息不存在: message_id={message_id}")
                return None

        except Exception as e:
            self.logger.error(f"获取消息失败 (ID: {message_id}): {e}")
            raise e

    def get_messages_recorder(self, round_id: str) -> List[Message]:
        """获取轮次的所有消息（兼容原方法名）

        Args:
            round_id: 轮次ID

        Returns:
            List[Message]: 消息列表
        """
        return self.get_messages_by_round(round_id)

    def get_messages_by_round(self, round_id: str) -> List[Message]:
        """获取轮次的所有消息

        Args:
            round_id: 轮次ID

        Returns:
            List[Message]: 消息列表
        """
        try:
            sql = """
                SELECT message_id, round_id, role, content, type, timestamp, tool_success, tool_call_ids, tool_call_raw, agent_id, tool_name, sub_conversation_id, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, platform, model, reasoning_content, attachments
                FROM messages
                WHERE round_id = ?
                ORDER BY message_id ASC
            """
            rows = self._fetch_all(sql, (round_id,))

            messages = [Message.from_dict(self._parse_message_row(self._row_to_dict(row))) for row in rows]
            self.logger.debug(f"获取轮次消息成功: round_id={round_id}, 共{len(messages)}条消息")
            return messages

        except Exception as e:
            self.logger.error(f"获取轮次消息失败 (round_id: {round_id}): {e}")
            return []  # 兼容原代码，失败时返回空列表

    def get_user_attachments_by_round(self, round_id: str) -> List[str]:
        """获取轮次中用户消息的附件文件名列表

        按顺序返回用户消息中的附件文件名，用于 Tool 根据索引获取文件名。

        Args:
            round_id: 轮次ID

        Returns:
            List[str]: 附件文件名列表（按顺序）
        """
        try:
            sql = """
                SELECT attachments
                FROM messages
                WHERE round_id = ? AND role = 'user' AND attachments IS NOT NULL AND attachments != ''
                ORDER BY message_id ASC
                LIMIT 1
            """
            row = self._fetch_one(sql, (round_id,))

            if not row or not row[0]:
                return []

            # 解析 attachments JSON
            import json
            attachments_data = json.loads(row[0])

            # 提取文件名列表
            filenames = [att.get("filename", "") for att in attachments_data if att.get("filename")]

            self.logger.debug(f"获取用户附件成功: round_id={round_id}, 共{len(filenames)}个附件")
            return filenames

        except Exception as e:
            self.logger.error(f"获取用户附件失败 (round_id: {round_id}): {e}")
            return []

    def get_messages_by_conversation(self, conversation_id: str, limit: int = None) -> List[Message]:
        """获取对话的所有消息（通过rounds关联）

        .. deprecated::
            该方法目前未被使用，可能在未来版本中移除。
            建议使用 get_conversation_messages_paginated() 替代。

        Args:
            conversation_id: 对话ID
            limit: 返回记录数限制（可选）

        Returns:
            List[Message]: 消息列表
        """
        warnings.warn(
            "get_messages_by_conversation() 目前未被使用，建议使用 get_conversation_messages_paginated()",
            DeprecationWarning,
            stacklevel=2
        )
        try:
            if limit:
                sql = """
                    SELECT m.message_id, m.round_id, m.role, m.content, m.type, m.timestamp,
                           m.tool_success, m.tool_call_ids, m.tool_call_raw, m.agent_id, m.tool_name, m.sub_conversation_id,
                           m.total_tokens, m.prompt_tokens, m.completion_tokens, m.reasoning_tokens, m.platform, m.model, m.reasoning_content, m.attachments
                    FROM messages m
                    JOIN rounds r ON m.round_id = r.round_id
                    WHERE r.conversation_id = ?
                    ORDER BY r.created_at ASC, m.message_id ASC
                    LIMIT ?
                """
                params = (conversation_id, limit)
            else:
                sql = """
                    SELECT m.message_id, m.round_id, m.role, m.content, m.type, m.timestamp,
                           m.tool_success, m.tool_call_ids, m.tool_call_raw, m.agent_id, m.tool_name, m.sub_conversation_id,
                           m.total_tokens, m.prompt_tokens, m.completion_tokens, m.reasoning_tokens, m.platform, m.model, m.reasoning_content, m.attachments
                    FROM messages m
                    JOIN rounds r ON m.round_id = r.round_id
                    WHERE r.conversation_id = ?
                    ORDER BY r.created_at ASC, m.message_id ASC
                """
                params = (conversation_id,)

            rows = self._fetch_all(sql, params)

            messages = [Message.from_dict(self._parse_message_row(self._row_to_dict(row))) for row in rows]
            self.logger.debug(f"获取对话消息成功: conversation_id={conversation_id}, 共{len(messages)}条消息")
            return messages

        except Exception as e:
            self.logger.error(f"获取对话消息失败 (conversation_id: {conversation_id}): {e}")
            raise e

    def get_messages_by_type(self, round_id: str, message_type: MessageType) -> List[Message]:
        """根据消息类型获取轮次的消息

        .. deprecated::
            该方法目前未被使用，可能在未来版本中移除。

        Args:
            round_id: 轮次ID
            message_type: 消息类型

        Returns:
            List[Message]: 指定类型的消息列表
        """
        warnings.warn(
            "get_messages_by_type() 目前未被使用，可能在未来版本中移除",
            DeprecationWarning,
            stacklevel=2
        )
        try:
            sql = """
                SELECT message_id, round_id, role, content, type, timestamp, tool_success, tool_call_ids, tool_call_raw, agent_id, tool_name, sub_conversation_id, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, platform, model, reasoning_content, attachments
                FROM messages
                WHERE round_id = ? AND type = ?
                ORDER BY message_id ASC
            """
            rows = self._fetch_all(sql, (round_id, message_type.value))

            messages = [Message.from_dict(self._parse_message_row(self._row_to_dict(row))) for row in rows]
            self.logger.debug(f"获取指定类型消息成功: round_id={round_id}, type={message_type.value}, 共{len(messages)}条")
            return messages

        except Exception as e:
            self.logger.error(f"获取指定类型消息失败 (round_id: {round_id}, type: {message_type}): {e}")
            raise e

    def update_message_tokens(self, message_id: int, total_tokens: int, prompt_tokens: int = 0, completion_tokens: int = 0, reasoning_tokens: int = 0, platform: str = None, model: str = None) -> None:
        """更新消息的Token信息和平台模型信息

        Args:
            message_id: 消息ID
            total_tokens: 总Token数量
            prompt_tokens: 提示Token数量
            completion_tokens: 完成Token数量
            reasoning_tokens: 推理Token数量
            platform: 平台名称（可选）
            model: 模型名称（可选）
        """
        try:
            if platform and model:
                sql = """
                    UPDATE messages 
                    SET total_tokens = ?, prompt_tokens = ?, completion_tokens = ?, reasoning_tokens = ?, platform = ?, model = ?
                    WHERE message_id = ?
                """
                params = (total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, platform, model, message_id)
            else:
                sql = """
                    UPDATE messages 
                    SET total_tokens = ?, prompt_tokens = ?, completion_tokens = ?, reasoning_tokens = ?
                    WHERE message_id = ?
                """
                params = (total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, message_id)

            rows_affected = self._execute_update(sql, params)

            if rows_affected > 0:
                self.logger.info(f"消息Token信息更新成功: message_id={message_id}, total_tokens={total_tokens}, prompt_tokens={prompt_tokens}, completion_tokens={completion_tokens}, reasoning_tokens={reasoning_tokens}")
            else:
                self.logger.warning(f"消息不存在，Token信息更新失败: message_id={message_id}")

        except Exception as e:
            self.logger.error(f"更新消息Token信息失败: {e}")
            raise e

    def update_message_content(self, message_id: int, content: str) -> None:
        """更新消息内容

        Args:
            message_id: 消息ID
            content: 新内容
        """
        try:
            sql = """
                UPDATE messages 
                SET content = ?
                WHERE message_id = ?
            """
            rows_affected = self._execute_update(sql, (content, message_id))

            if rows_affected > 0:
                self.logger.info(f"消息内容更新成功: message_id={message_id}")
            else:
                self.logger.warning(f"消息不存在，内容更新失败: message_id={message_id}")

        except Exception as e:
            self.logger.error(f"更新消息内容失败: {e}")
            raise e

    def delete_message(self, message_id: int) -> bool:
        """删除消息

        Args:
            message_id: 消息ID

        Returns:
            bool: 删除是否成功
        """
        try:
            sql = "DELETE FROM messages WHERE message_id = ?"
            rows_affected = self._execute_update(sql, (message_id,))

            if rows_affected > 0:
                self.logger.info(f"消息删除成功: message_id={message_id}")
                return True
            else:
                self.logger.warning(f"消息不存在，删除失败: message_id={message_id}")
                return False

        except Exception as e:
            self.logger.error(f"删除消息失败 (ID: {message_id}): {e}")
            raise e

    def delete_messages_by_round(self, round_id: str) -> int:
        """删除轮次的所有消息

        Args:
            round_id: 轮次ID

        Returns:
            int: 删除的消息数量
        """
        try:
            sql = "DELETE FROM messages WHERE round_id = ?"
            rows_affected = self._execute_update(sql, (round_id,))

            self.logger.info(f"轮次消息删除成功: round_id={round_id}, 删除数量={rows_affected}")
            return rows_affected

        except Exception as e:
            self.logger.error(f"删除轮次消息失败 (round_id: {round_id}): {e}")
            raise e

    # ==================== System Message 特殊操作（已废弃） ====================

    def create_system_message(self, conversation_id: str, message: Message) -> int:
        """创建系统消息（使用conversation_id作为round_id）

        .. deprecated::
            该方法目前未被使用，可能在未来版本中移除。
            系统消息现在由 Agent 动态生成，不再存储于数据库。

        Args:
            conversation_id: 对话ID
            message: 系统消息对象

        Returns:
            int: 新插入消息的ID
        """
        warnings.warn(
            "create_system_message() 目前未被使用，系统消息由 Agent 动态生成",
            DeprecationWarning,
            stacklevel=2
        )
        try:
            sql = """
                INSERT INTO messages (round_id, role, content, type, timestamp, tool_success, tool_call_ids, tool_call_raw, agent_id, reasoning_content)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                conversation_id,  # 系统消息使用conversation_id作为round_id
                message.role,
                message.content,
                message.type.value if isinstance(message.type, MessageType) else message.type,
                message.timestamp,
                1 if message.tool_success else 0 if message.tool_success is not None else None,
                message.tool_call_ids,  # 新字段
                message.tool_call_raw,  # 新字段
                message.agent_id,  # agent_id 字段
                getattr(message, "reasoning_content", ""),
            )

            message_id = self._execute_insert(sql, params)
            self.logger.info(f"系统消息创建成功: message_id={message_id}, conversation_id={conversation_id}")
            return message_id

        except Exception as e:
            self.logger.error(f"创建系统消息失败: {e}")
            raise e

    def get_system_message(self, conversation_id: str) -> Optional[Message]:
        """获取最新的系统消息

        .. deprecated::
            该方法目前未被使用，可能在未来版本中移除。
            系统消息现在由 Agent 动态生成，不再存储于数据库。

        Args:
            conversation_id: 对话ID

        Returns:
            Optional[Message]: 系统消息对象，如果不存在则返回None
        """
        warnings.warn(
            "get_system_message() 目前未被使用，系统消息由 Agent 动态生成",
            DeprecationWarning,
            stacklevel=2
        )
        try:
            sql = """
                SELECT message_id, round_id, role, content, type, timestamp, tool_success, tool_call_ids, tool_call_raw, agent_id, tool_name, sub_conversation_id, total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, platform, model, reasoning_content, attachments
                FROM messages
                WHERE round_id = ? AND role = 'system'
                ORDER BY timestamp DESC, message_id DESC
                LIMIT 1
            """
            row = self._fetch_one(sql, (conversation_id,))

            if row:
                message_data = self._parse_message_row(self._row_to_dict(row))
                self.logger.debug(f"获取系统消息成功: conversation_id={conversation_id}")
                return Message.from_dict(message_data)
            else:
                self.logger.debug(f"系统消息不存在: conversation_id={conversation_id}")
                return None

        except Exception as e:
            self.logger.error(f"获取系统消息失败: {e}")
            raise e

    def update_system_message(self, conversation_id: str, message: Message) -> None:
        """更新或插入系统消息

        .. deprecated::
            该方法目前未被使用，可能在未来版本中移除。
            系统消息现在由 Agent 动态生成，不再存储于数据库。

        Args:
            conversation_id: 对话ID
            message: 系统消息对象
        """
        warnings.warn(
            "update_system_message() 目前未被使用，系统消息由 Agent 动态生成",
            DeprecationWarning,
            stacklevel=2
        )
        try:
            # 检查是否已存在系统消息
            existing_sql = """
                SELECT message_id FROM messages 
                WHERE round_id = ? AND role = 'system'
            """
            existing_row = self._fetch_one(existing_sql, (conversation_id,))

            if existing_row:
                # 已存在，更新
                update_sql = """
                    UPDATE messages 
                    SET content = ?, timestamp = ?
                    WHERE message_id = ?
                """
                self._execute_update(update_sql, (message.content, message.timestamp, existing_row["message_id"]))
                self.logger.info(f"系统消息更新成功: conversation_id={conversation_id}")
            else:
                # 不存在，创建新的
                self.create_system_message(conversation_id, message)
                self.logger.info(f"系统消息创建成功: conversation_id={conversation_id}")

        except Exception as e:
            self.logger.error(f"更新/插入系统消息失败: {e}")
            raise e

    # ==================== 统计和查询 ====================

    def get_message_count_by_round(self, round_id: str) -> int:
        """获取轮次的消息数量

        Args:
            round_id: 轮次ID

        Returns:
            int: 消息数量
        """
        try:
            sql = "SELECT COUNT(*) as count FROM messages WHERE round_id = ?"
            row = self._fetch_one(sql, (round_id,))
            count = row["count"] if row else 0

            self.logger.debug(f"获取轮次消息数量: round_id={round_id}, 数量={count}")
            return count

        except Exception as e:
            self.logger.error(f"获取轮次消息数量失败 (round_id: {round_id}): {e}")
            raise e

    def get_message_stats_by_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """获取对话的消息统计信息

        Args:
            conversation_id: 对话ID

        Returns:
            Dict[str, Any]: 消息统计信息
        """
        try:
            sql = """
                SELECT 
                    COUNT(*) as total_messages,
                    COUNT(CASE WHEN role = 'user' THEN 1 END) as user_messages,
                    COUNT(CASE WHEN role = 'assistant' THEN 1 END) as assistant_messages,
                    COUNT(CASE WHEN role = 'system' THEN 1 END) as system_messages,
                    COUNT(CASE WHEN type = 'tool_call' THEN 1 END) as tool_calls,
                    COUNT(CASE WHEN type = 'tool_response' THEN 1 END) as tool_responses,
                    SUM(total_tokens) as total_tokens,
                    COUNT(DISTINCT platform) as platforms_used
                FROM messages m
                JOIN rounds r ON m.round_id = r.round_id
                WHERE r.conversation_id = ?
            """
            row = self._fetch_one(sql, (conversation_id,))

            if row:
                stats = self._row_to_dict(row)
                # 处理NULL值
                for key, value in stats.items():
                    if value is None:
                        stats[key] = 0

                self.logger.debug(f"获取对话消息统计成功: conversation_id={conversation_id}")
                return stats
            else:
                return {}

        except Exception as e:
            self.logger.error(f"获取对话消息统计失败 (conversation_id: {conversation_id}): {e}")
            raise e

    def search_messages(self, query: str, user_id: str = None, limit: int = 100) -> List[Message]:
        """搜索消息内容

        .. deprecated::
            该方法目前未被使用，可能在未来版本中移除。

        Args:
            query: 搜索关键词
            user_id: 用户ID（可选，限制搜索范围）
            limit: 返回记录数限制

        Returns:
            List[Message]: 匹配的消息列表
        """
        warnings.warn(
            "search_messages() 目前未被使用，可能在未来版本中移除",
            DeprecationWarning,
            stacklevel=2
        )
        try:
            if user_id:
                sql = """
                    SELECT m.message_id, m.round_id, m.role, m.content, m.type, m.timestamp,
                           m.tool_success, m.tool_call_ids, m.tool_call_raw, m.agent_id, m.tool_name, m.sub_conversation_id,
                           m.total_tokens, m.prompt_tokens, m.completion_tokens, m.reasoning_tokens, m.platform, m.model, m.reasoning_content, m.attachments
                    FROM messages m
                    JOIN rounds r ON m.round_id = r.round_id
                    JOIN conversations c ON r.conversation_id = c.conversation_id
                    WHERE c.user_id = ? AND m.content LIKE ?
                    ORDER BY m.timestamp DESC
                    LIMIT ?
                """
                params = (user_id, f"%{query}%", limit)
            else:
                sql = """
                    SELECT message_id, round_id, role, content, type, timestamp,
                           tool_success, tool_call_ids, tool_call_raw, agent_id, tool_name, sub_conversation_id,
                           total_tokens, prompt_tokens, completion_tokens, reasoning_tokens, platform, model, reasoning_content, attachments
                    FROM messages
                    WHERE content LIKE ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """
                params = (f"%{query}%", limit)

            rows = self._fetch_all(sql, params)

            messages = [Message.from_dict(self._parse_message_row(self._row_to_dict(row))) for row in rows]
            self.logger.debug(f"搜索消息成功: 关键词='{query}', 找到{len(messages)}条消息")
            return messages

        except Exception as e:
            self.logger.error(f"搜索消息失败 (query: {query}): {e}")
            raise e

    def get_conversation_messages_paginated(self, conversation_id: str, before_round_id: str = None, limit: int = 20) -> List[Message]:
        """获取对话消息（按轮次分页）- 按round时间倒序，每个round包含所有消息

        Args:
            conversation_id: 对话ID
            before_round_id: 获取此轮次ID之前的轮次（可选）
            limit: 返回轮次数量限制，默认20

        Returns:
            List[Message]: 消息对象列表，按时间倒序（最新在前）
        """
        try:
            # 先获取符合条件的轮次列表
            if before_round_id:
                round_sql = """
                    SELECT r.round_id, r.created_at as round_timestamp
                    FROM rounds r
                    WHERE r.conversation_id = ? AND r.created_at < (
                        SELECT created_at FROM rounds WHERE round_id = ?
                    )
                    ORDER BY r.created_at DESC
                    LIMIT ?
                """
                round_params = (conversation_id, before_round_id, limit)
            else:
                round_sql = """
                    SELECT r.round_id, r.created_at as round_timestamp
                    FROM rounds r
                    WHERE r.conversation_id = ?
                    ORDER BY r.created_at DESC
                    LIMIT ?
                """
                round_params = (conversation_id, limit)

            # 获取轮次列表
            round_rows = self._fetch_all(round_sql, round_params)

            if not round_rows:
                self.logger.debug(f"没有找到符合条件的轮次: conversation_id={conversation_id}, before_round_id={before_round_id}")
                return []

            # 获取这些轮次的所有消息
            round_ids = [row["round_id"] for row in round_rows]
            placeholders = ",".join(["?"] * len(round_ids))

            message_sql = f"""
                SELECT m.message_id, m.round_id, m.role, m.content, m.type, m.timestamp,
                       m.tool_success, m.tool_call_ids, m.tool_call_raw, m.agent_id, m.tool_name, m.sub_conversation_id,
                       m.total_tokens, m.prompt_tokens, m.completion_tokens, m.reasoning_tokens, m.platform, m.model, m.reasoning_content, m.attachments,
                       r.created_at as round_created_at
                FROM messages m
                JOIN rounds r ON m.round_id = r.round_id
                WHERE m.round_id IN ({placeholders})
                ORDER BY r.created_at DESC, m.message_id DESC
            """

            message_rows = self._fetch_all(message_sql, round_ids)

            # 返回 Message 对象列表
            messages = [Message.from_dict(self._parse_message_row(self._row_to_dict(row))) for row in message_rows]
            self.logger.debug(f"获取对话消息分页成功: conversation_id={conversation_id}, before_round_id={before_round_id}, 共{len(messages)}条消息，来自{len(round_ids)}个轮次")
            return messages

        except Exception as e:
            self.logger.error(f"获取对话消息分页失败 (conversation_id: {conversation_id}): {e}")
            raise e

    def get_user_tool_call_count(self, user_id: str) -> int:
        """获取用户的工具调用总数

        Args:
            user_id: 用户ID

        Returns:
            int: 工具调用数量（type='tool_result'）
        """
        try:
            sql = """
                SELECT COUNT(*) as count
                FROM messages m
                JOIN rounds r ON m.round_id = r.round_id
                JOIN conversations c ON r.conversation_id = c.conversation_id
                WHERE c.user_id = ? AND m.type = 'tool_result'
            """
            row = self._fetch_one(sql, (user_id,))
            count = row["count"] if row else 0

            self.logger.debug(f"获取用户工具调用数: user_id={user_id}, count={count}")
            return count

        except Exception as e:
            self.logger.error(f"获取用户工具调用数失败 (user_id: {user_id}): {e}")
            raise e
