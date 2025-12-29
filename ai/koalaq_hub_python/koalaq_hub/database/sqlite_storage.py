import datetime
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Union

from ..config.settings import Configuration
from ..models.data_models import Conversation, Round, SummaryLog, User
from ..models.message import Message


class SqliteStorage:
    def __init__(self, db_path: str = None):
        """初始化数据库管理器

        Args:
            db_path: 数据库文件路径，如果为None则使用当前配置的路径
        """
        if db_path:
            self.db_path = db_path
        else:
            # 动态获取配置，确保使用最新的环境变量
            current_config = Configuration()
            self.db_path = current_config.get_database_path()
        self.conn = None
        self._init_db()

    def _init_db(self):
        """初始化数据库连接和表结构"""
        try:
            # 确保数据库目录存在
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)

            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # 关键：让 fetchone/fetchall 返回 dict-like
            cursor = self.conn.cursor()

            # 创建 users 表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    created_at TEXT,
                    extra_data TEXT,
                    tokens INTEGER DEFAULT 0
                )
            """)

            # 创建 conversations 表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    title TEXT,
                    summary TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    tags TEXT,
                    tokens INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)

            # 创建 rounds 表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rounds (
                    round_id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    summary TEXT,
                    created_at TEXT,
                    user_rating INTEGER,
                    extra_data TEXT,
                    tokens INTEGER DEFAULT 0,
                    execution_time REAL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (conversation_id)
                )
            """)

            # 创建 messages 表 (根据 Table.md 更新)
            # 注意: 此处仅保证表存在。如果旧表结构不兼容，可能需要手动迁移数据。
            # 为了简单起见，这里假设是初始化场景或可以重建。
            # cursor.execute('''DROP TABLE IF EXISTS messages''') # 确保能使用新结构
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    round_id TEXT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    tool_name TEXT,
                    tool_success INTEGER,
                    platform TEXT,
                    model TEXT,
                    tokens INTEGER DEFAULT 0,
                    FOREIGN KEY (round_id) REFERENCES rounds (round_id)
                )
            """)

            # 创建 summary_snapshots 表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS summary_snapshots (
                    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT,
                    based_on_round_id TEXT,
                    context_summary TEXT,
                    created_at TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (conversation_id),
                    FOREIGN KEY (based_on_round_id) REFERENCES rounds (round_id)
                )
            """)

            # 创建 summary_log 表 - 用于记录总结操作的日志
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS summary_log (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    summary_content TEXT NOT NULL,
                    summary_result TEXT,
                    status TEXT NOT NULL,
                    conversation_id TEXT,
                    round_id TEXT,
                    snapshot_id INTEGER,
                    platform TEXT,
                    model TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    error_message TEXT,
                    execution_time REAL,
                    total_tokens INTEGER,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (conversation_id),
                    FOREIGN KEY (round_id) REFERENCES rounds (round_id),
                    FOREIGN KEY (snapshot_id) REFERENCES summary_snapshots (snapshot_id)
                )
            """)

            # 创建 models 表 - 用于统计各模型的token使用量
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS models (
                    model_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    model TEXT NOT NULL,
                    tokens INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(platform, model)
                )
            """)

            self.conn.commit()
            logging.info("数据库初始化成功")

        except Exception as e:
            logging.error(f"数据库初始化失败: {e}")
            raise

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def add_user(self, user: User):
        """将用户添加到数据库"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (user_id, username, created_at, extra_data)
                VALUES (?, ?, ?, ?)
            """,
                (user.user_id, user.username, user.created_at, user.extra_data),
            )
            self.conn.commit()
            logging.info(f"用户 {user.username} (ID: {user.user_id}) 已添加")
        except sqlite3.IntegrityError:
            logging.warning(f"尝试添加已存在的用户 (ID: {user.user_id})")
            raise
        except Exception as e:
            logging.error(f"添加用户失败: {e}")
            raise

    def get_user(self, user_id: str) -> Optional[User]:
        """根据user_id从数据库获取用户"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT user_id, username, created_at, extra_data FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return User.from_dict(dict(row))
            return None
        except Exception as e:
            logging.error(f"获取用户 (ID: {user_id}) 失败: {e}")
            raise

    def create_conversation(self, user_id: str, conversation_id: str):
        """创建一个会话"""
        try:
            cursor = self.conn.cursor()
            now = datetime.datetime.now().isoformat()
            cursor.execute(
                """
                INSERT INTO conversations (conversation_id, user_id, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """,
                (conversation_id, user_id, now, now),
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            logging.warning(f"会话已存在: {conversation_id}")
        except Exception as e:
            logging.error(f"创建会话失败: {e}")
            raise

    def update_coversation_time(self, conversation_id: str):
        """更新会话的更新时间"""
        try:
            cursor = self.conn.cursor()
            now = datetime.datetime.now().isoformat()
            cursor.execute(
                """
                UPDATE conversations SET updated_at = ? WHERE conversation_id = ?
            """,
                (now, conversation_id),
            )
            self.conn.commit()
        except Exception as e:
            logging.error(f"更新会话时间失败: {e}")
            raise

    def update_conversation_title(self, conversation_id: str, title: str):
        """更新会话的标题"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                UPDATE conversations SET title = ? WHERE conversation_id = ?
            """,
                (title, conversation_id),
            )
            self.conn.commit()
        except Exception as e:
            logging.error(f"更新会话标题失败: {e}")
            raise

    def update_coversation_summary(self, conversation_id: str, summary: str):
        """更新会话的摘要"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                UPDATE conversations SET summary = ? WHERE conversation_id = ?
            """,
                (summary, conversation_id),
            )
            self.conn.commit()
        except Exception as e:
            logging.error(f"更新会话摘要失败: {e}")
            raise

    def get_conversation_recorder(self, user_id: str, conversation_id: str) -> Conversation:
        """获取一个会话"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT conversation_id, user_id, title, summary, created_at, updated_at, tags
                FROM conversations
                WHERE conversation_id = ? AND user_id = ?
            """,
                (conversation_id, user_id),
            )
            row = cursor.fetchone()
            if row:
                return Conversation.from_dict(dict(row))
            return None
        except Exception as e:
            logging.error(f"获取会话失败: {e}")
            raise

    def get_all_conversations_recorder(self, user_id: str) -> List[Conversation]:
        """获取用户所有会话"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT conversation_id, user_id, title, summary, created_at, updated_at, tags
                FROM conversations
                WHERE user_id = ?
            """,
                (user_id,),
            )
            rows = cursor.fetchall()
            return [Conversation.from_dict(dict(row)) for row in rows]
        except Exception as e:
            logging.error(f"获取用户所有会话失败: {e}")
            raise

    def create_round(self, conversation_id: str, round_id: str):
        """创建一个轮次"""
        try:
            cursor = self.conn.cursor()
            now = datetime.datetime.now().isoformat()
            cursor.execute(
                """
                INSERT INTO rounds (round_id, conversation_id, created_at)
                VALUES (?, ?, ?)
            """,
                (round_id, conversation_id, now),
            )
            self.conn.commit()
        except Exception as e:
            logging.error(f"创建轮次失败: {e}")
            raise

    def update_round_summary(self, conversation_id: str, round_id: str, summary: str):
        """更新轮次的摘要"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                UPDATE rounds SET summary = ? WHERE conversation_id = ? AND round_id = ?
            """,
                (summary, conversation_id, round_id),
            )
            self.conn.commit()
        except Exception as e:
            logging.error(f"更新轮次摘要失败: {e}")
            raise

    def get_round_recorder(self, conversation_id: str, round_id: str) -> Round:
        """获取一个轮次"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT round_id, conversation_id, summary, created_at, user_rating, extra_data
                FROM rounds
                WHERE conversation_id = ? AND round_id = ?
            """,
                (conversation_id, round_id),
            )
            row = cursor.fetchone()
            if row:
                return Round.from_dict(dict(row))
            return None
        except Exception as e:
            logging.error(f"获取轮次失败: {e}")
            raise

    def get_rounds_recorder_by_memory_window(self, conversation_id: str, memory_window: int) -> List[Round]:
        """获取一个会话的最近memory_window轮次"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT round_id, conversation_id, summary, created_at, user_rating, extra_data
                FROM rounds
                WHERE conversation_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (conversation_id, memory_window),
            )
            rows = cursor.fetchall()
            return [Round.from_dict(dict(row)) for row in rows]
        except Exception as e:
            logging.error(f"获取最近轮次失败: {e}")
            raise

    def get_all_rounds_recorder(self, conversation_id: str) -> List[Round]:
        """获取一个会话的所有轮次"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT round_id, conversation_id, summary, created_at, user_rating, extra_data
                FROM rounds
                WHERE conversation_id = ?
            """,
                (conversation_id,),
            )
            rows = cursor.fetchall()
            return [Round.from_dict(dict(row)) for row in rows]
        except Exception as e:
            logging.error(f"获取所有轮次失败: {e}")
            raise

    def add_message(self, round_id: str, message: Message):
        """添加一条消息"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO messages (round_id, role, content, type, timestamp, tool_name, tool_success)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (round_id, message.role, message.content, message.type.value, message.timestamp, message.tool_name, message.tool_success),
            )
            self.conn.commit()
        except Exception as e:
            logging.error(f"添加消息失败: {e}")
            raise

    def get_messages_recorder(self, round_id: str) -> List[Message]:
        """获取一个轮次的所有消息"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT message_id, round_id, role, content, type, timestamp, tool_name, tool_success
                FROM messages
                WHERE round_id = ?
            """,
                (round_id,),
            )
            rows = cursor.fetchall()
            return [Message.from_dict(dict(row)) for row in rows]
        except Exception as e:
            logging.error(f"获取消息失败: {e}")
            return []

    def create_system_message(self, conversation_id: str, message: Message):
        """创建一个system message"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO messages (round_id, role, content, type, timestamp, tool_name, tool_success)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (conversation_id, message.role, message.content, message.type.value, message.timestamp, message.tool_name, message.tool_success),
            )
            self.conn.commit()
        except Exception as e:
            logging.error(f"创建system message失败: {e}")
            raise

    def get_system_message(self, conversation_id: str) -> Message:
        """
        查询指定conversation_id下最新一条system message。
        返回message字典，未找到则返回空字典。
        """
        try:
            cursor = self.conn.cursor()
            # 查找该conversation下round_id等于conversation_id的system消息
            query = """
                SELECT message_id, role, content, type, timestamp, tool_name, tool_success
                FROM messages 
                WHERE round_id = ? AND role = 'system'
                ORDER BY timestamp DESC, message_id DESC
                LIMIT 1
            """
            cursor.execute(query, (conversation_id,))
            row = cursor.fetchone()
            if row:
                return Message.from_dict(dict(row))
            return None
        except Exception as e:
            logging.error(f"查询system message失败: {e}")
            raise

    def update_system_message(self, conversation_id: str, message: Message):
        """更新或插入 system message（round_id=conversation_id, role=system）"""
        try:
            cursor = self.conn.cursor()
            # 检查是否已存在
            cursor.execute(
                """
                SELECT message_id FROM messages WHERE round_id = ? AND role = 'system'
            """,
                (conversation_id,),
            )
            row = cursor.fetchone()
            if row:
                # 已存在，更新
                cursor.execute(
                    """
                    UPDATE messages SET content = ? WHERE message_id = ?
                """,
                    (message.content, row[0]),
                )
            else:
                # 不存在，插入
                self.create_system_message(conversation_id, message)
            self.conn.commit()
        except Exception as e:
            logging.error(f"更新/插入 system message 失败: {e}")
            raise

    # =============== Summary Log 相关方法 ===============

    def create_summary_log(self, summary_log: SummaryLog) -> int:
        """创建总结日志记录

        Args:
            summary_log: 总结日志对象

        Returns:
            int: 创建的日志记录ID
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO summary_log (
                    summary_content, summary_result, status, conversation_id, 
                    round_id, snapshot_id, platform, model, created_at, updated_at, 
                    error_message, execution_time, total_tokens
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    summary_log.summary_content,
                    summary_log.summary_result,
                    summary_log.status,
                    summary_log.conversation_id,
                    summary_log.round_id,
                    summary_log.snapshot_id,
                    summary_log.platform,
                    summary_log.model,
                    summary_log.created_at,
                    summary_log.updated_at,
                    summary_log.error_message,
                    summary_log.execution_time,
                    summary_log.total_tokens,
                ),
            )
            log_id = cursor.lastrowid
            self.conn.commit()
            logging.info(f"创建总结日志成功，log_id: {log_id}")
            return log_id
        except Exception as e:
            logging.error(f"创建总结日志失败: {e}")
            raise

    def update_summary_log(self, log_id: int, summary_result: str = None, status: str = None, error_message: str = None, execution_time: float = None, total_tokens: int = None) -> bool:
        """更新总结日志记录

        Args:
            log_id: 日志记录ID
            summary_result: 总结结果
            status: 状态
            error_message: 错误信息
            execution_time: 执行时间
            total_tokens: 总token数量

        Returns:
            bool: 更新是否成功
        """
        try:
            cursor = self.conn.cursor()

            # 构建动态更新语句
            update_fields = []
            update_values = []

            if summary_result is not None:
                update_fields.append("summary_result = ?")
                update_values.append(summary_result)

            if status is not None:
                update_fields.append("status = ?")
                update_values.append(status)

            if error_message is not None:
                update_fields.append("error_message = ?")
                update_values.append(error_message)

            if execution_time is not None:
                update_fields.append("execution_time = ?")
                update_values.append(execution_time)

            if total_tokens is not None:
                update_fields.append("total_tokens = ?")
                update_values.append(total_tokens)

            # 总是更新 updated_at
            update_fields.append("updated_at = ?")
            update_values.append(datetime.datetime.now().isoformat())

            if not update_fields:
                logging.warning("没有字段需要更新")
                return False

            update_values.append(log_id)

            sql = f"UPDATE summary_log SET {', '.join(update_fields)} WHERE log_id = ?"
            cursor.execute(sql, update_values)

            rows_affected = cursor.rowcount
            self.conn.commit()

            if rows_affected > 0:
                logging.info(f"更新总结日志成功，log_id: {log_id}")
                return True
            else:
                logging.warning(f"未找到要更新的总结日志记录，log_id: {log_id}")
                return False

        except Exception as e:
            logging.error(f"更新总结日志失败: {e}")
            raise

    def get_summary_log(self, log_id: int) -> Optional[SummaryLog]:
        """根据log_id获取总结日志记录

        Args:
            log_id: 日志记录ID

        Returns:
            SummaryLog: 总结日志对象，如果不存在则返回None
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT log_id, summary_content, summary_result, status, 
                       conversation_id, round_id, snapshot_id, llm_choose, platform, model,
                       created_at, updated_at, error_message, execution_time, total_tokens
                FROM summary_log
                WHERE log_id = ?
            """,
                (log_id,),
            )

            row = cursor.fetchone()
            if row:
                return SummaryLog.from_dict(dict(row))
            return None

        except Exception as e:
            logging.error(f"获取总结日志失败: {e}")
            raise

    def get_summary_logs_by_conversation(self, conversation_id: str, limit: int = 50) -> List[SummaryLog]:
        """获取指定会话的总结日志记录

        Args:
            conversation_id: 会话ID
            limit: 返回记录数限制

        Returns:
            List[SummaryLog]: 总结日志列表
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT log_id, summary_content, summary_result, status, 
                       conversation_id, round_id, snapshot_id, llm_choose, platform, model,
                       created_at, updated_at, error_message, execution_time, total_tokens
                FROM summary_log
                WHERE conversation_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (conversation_id, limit),
            )

            rows = cursor.fetchall()
            return [SummaryLog.from_dict(dict(row)) for row in rows]

        except Exception as e:
            logging.error(f"获取会话总结日志失败: {e}")
            raise

    def get_summary_logs_by_status(self, status: str, limit: int = 100) -> List[SummaryLog]:
        """根据状态获取总结日志记录

        Args:
            status: 状态 ('pending', 'success', 'failed')
            limit: 返回记录数限制

        Returns:
            List[SummaryLog]: 总结日志列表
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT log_id, summary_content, summary_result, status, 
                       conversation_id, round_id, snapshot_id, llm_choose, platform, model,
                       created_at, updated_at, error_message, execution_time, total_tokens
                FROM summary_log
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (status, limit),
            )

            rows = cursor.fetchall()
            return [SummaryLog.from_dict(dict(row)) for row in rows]

        except Exception as e:
            logging.error(f"根据状态获取总结日志失败: {e}")
            raise

    def get_summary_logs_by_llm_config(self, llm_choose: str, limit: int = 100) -> List[SummaryLog]:
        """根据LLM配置获取总结日志记录

        Args:
            llm_choose: LLM配置名称
            limit: 返回记录数限制

        Returns:
            List[SummaryLog]: 总结日志列表
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT log_id, summary_content, summary_result, status, 
                       conversation_id, round_id, snapshot_id, llm_choose, platform, model,
                       created_at, updated_at, error_message, execution_time, total_tokens
                FROM summary_log
                WHERE llm_choose = ?
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (llm_choose, limit),
            )

            rows = cursor.fetchall()
            return [SummaryLog.from_dict(dict(row)) for row in rows]

        except Exception as e:
            logging.error(f"根据LLM配置获取总结日志失败: {e}")
            raise

    def delete_summary_log(self, log_id: int) -> bool:
        """删除总结日志记录

        Args:
            log_id: 日志记录ID

        Returns:
            bool: 删除是否成功
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM summary_log WHERE log_id = ?", (log_id,))
            rows_affected = cursor.rowcount
            self.conn.commit()

            if rows_affected > 0:
                logging.info(f"删除总结日志成功，log_id: {log_id}")
                return True
            else:
                logging.warning(f"未找到要删除的总结日志记录，log_id: {log_id}")
                return False

        except Exception as e:
            logging.error(f"删除总结日志失败: {e}")
            raise

    def get_summary_log_statistics(self) -> Dict[str, Union[int, float, Dict]]:
        """获取总结日志统计信息

        Returns:
            Dict[str, int]: 统计信息字典
        """
        try:
            cursor = self.conn.cursor()

            # 统计各状态的记录数
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM summary_log
                GROUP BY status
            """)
            status_stats = dict(cursor.fetchall())

            # 统计各LLM配置的使用次数
            cursor.execute("""
                SELECT llm_choose, COUNT(*) as count
                FROM summary_log
                GROUP BY llm_choose
            """)
            llm_stats = dict(cursor.fetchall())

            # 总记录数
            cursor.execute("SELECT COUNT(*) FROM summary_log")
            total_count = cursor.fetchone()[0]

            # 平均执行时间
            cursor.execute("""
                SELECT AVG(execution_time) 
                FROM summary_log 
                WHERE execution_time IS NOT NULL AND status = 'success'
            """)
            avg_execution_time = cursor.fetchone()[0] or 0

            return {"total_count": total_count, "status_stats": status_stats, "llm_stats": llm_stats, "avg_execution_time": round(avg_execution_time, 3)}

        except Exception as e:
            logging.error(f"获取总结日志统计信息失败: {e}")
            raise

    # ===== Snapshot 快照总结相关方法 =====

    def create_snapshot(self, conversation_id: str, based_on_round_id: str, context_summary: str) -> int:
        """创建快照总结记录

        Args:
            conversation_id: 会话ID
            based_on_round_id: 基于的最后轮次ID
            context_summary: 快照总结内容

        Returns:
            新创建的快照ID
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO summary_snapshots (conversation_id, based_on_round_id, context_summary, created_at)
                VALUES (?, ?, ?, ?)
            """,
                (conversation_id, based_on_round_id, context_summary, datetime.datetime.now().isoformat()),
            )

            self.conn.commit()
            return cursor.lastrowid

        except Exception as e:
            logging.error(f"创建快照总结失败: {e}")
            raise

    def get_latest_snapshot(self, conversation_id: str) -> Optional[Dict]:
        """获取指定会话的最新快照

        Args:
            conversation_id: 会话ID

        Returns:
            最新的快照记录，如果没有则返回None
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT snapshot_id, conversation_id, based_on_round_id, context_summary, created_at
                FROM summary_snapshots 
                WHERE conversation_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """,
                (conversation_id,),
            )

            row = cursor.fetchone()
            if row:
                return {"snapshot_id": row[0], "conversation_id": row[1], "based_on_round_id": row[2], "context_summary": row[3], "created_at": row[4]}
            return None

        except Exception as e:
            logging.error(f"获取最新快照失败: {e}")
            raise

    def get_all_snapshots(self, conversation_id: str) -> List[Dict]:
        """获取指定会话的所有快照

        Args:
            conversation_id: 会话ID

        Returns:
            所有快照记录列表
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT snapshot_id, conversation_id, based_on_round_id, context_summary, created_at
                FROM summary_snapshots 
                WHERE conversation_id = ?
                ORDER BY created_at ASC
            """,
                (conversation_id,),
            )

            snapshots = []
            for row in cursor.fetchall():
                snapshots.append({"snapshot_id": row[0], "conversation_id": row[1], "based_on_round_id": row[2], "context_summary": row[3], "created_at": row[4]})
            return snapshots

        except Exception as e:
            logging.error(f"获取所有快照失败: {e}")
            raise

    def get_recent_snapshots(self, conversation_id: str, limit: int = 2) -> List[Dict]:
        """获取指定会话的最近N个快照

        Args:
            conversation_id: 会话ID
            limit: 返回快照数量限制

        Returns:
            最近的快照记录列表，按时间倒序
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT snapshot_id, conversation_id, based_on_round_id, context_summary, created_at
                FROM summary_snapshots 
                WHERE conversation_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (conversation_id, limit),
            )

            snapshots = []
            for row in cursor.fetchall():
                snapshots.append({"snapshot_id": row[0], "conversation_id": row[1], "based_on_round_id": row[2], "context_summary": row[3], "created_at": row[4]})
            return snapshots

        except Exception as e:
            logging.error(f"获取最近快照失败: {e}")
            raise

    def get_snapshots_count(self, conversation_id: str) -> int:
        """获取指定会话的快照数量

        Args:
            conversation_id: 会话ID

        Returns:
            快照数量
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) FROM summary_snapshots WHERE conversation_id = ?
            """,
                (conversation_id,),
            )

            return cursor.fetchone()[0]

        except Exception as e:
            logging.error(f"获取快照数量失败: {e}")
            raise

    def get_rounds_since_last_snapshot(self, conversation_id: str) -> List[Dict]:
        """获取自上次快照后的所有轮次记录

        Args:
            conversation_id: 会话ID

        Returns:
            轮次记录列表
        """
        try:
            cursor = self.conn.cursor()

            # 先获取最新快照的基准轮次ID
            latest_snapshot = self.get_latest_snapshot(conversation_id)

            if latest_snapshot:
                # 获取基准轮次后的所有轮次
                cursor.execute(
                    """
                    SELECT r.round_id, r.conversation_id, r.summary, r.created_at, r.user_rating, r.extra_data
                    FROM rounds r
                    WHERE r.conversation_id = ? AND r.created_at > (
                        SELECT created_at FROM rounds WHERE round_id = ?
                    )
                    ORDER BY r.created_at ASC
                """,
                    (conversation_id, latest_snapshot["based_on_round_id"]),
                )
            else:
                # 如果没有快照，获取所有轮次
                cursor.execute(
                    """
                    SELECT round_id, conversation_id, summary, created_at, user_rating, extra_data
                    FROM rounds 
                    WHERE conversation_id = ?
                    ORDER BY created_at ASC
                """,
                    (conversation_id,),
                )

            rounds = []
            for row in cursor.fetchall():
                rounds.append({"round_id": row[0], "conversation_id": row[1], "summary": row[2], "created_at": row[3], "user_rating": row[4], "extra_data": row[5]})
            return rounds

        except Exception as e:
            logging.error(f"获取快照后轮次失败: {e}")
            raise

    def update_conversation_summary(self, conversation_id: str, summary: str):
        """更新会话总结

        Args:
            conversation_id: 会话ID
            summary: 新的总结内容
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                UPDATE conversations 
                SET summary = ?, updated_at = ?
                WHERE conversation_id = ?
            """,
                (summary, datetime.datetime.now().isoformat(), conversation_id),
            )

            self.conn.commit()

        except Exception as e:
            logging.error(f"更新会话总结失败: {e}")
            raise

    # ===== Model 统计相关方法 =====

    def create_or_update_model(self, platform: str, model: str) -> int:
        """创建或获取模型记录

        Args:
            platform: 平台名称
            model: 模型名称

        Returns:
            模型ID
        """
        try:
            cursor = self.conn.cursor()
            now = datetime.datetime.now().isoformat()

            # 尝试插入，如果已存在则忽略
            cursor.execute(
                """
                INSERT OR IGNORE INTO models (platform, model, tokens, created_at, updated_at)
                VALUES (?, ?, 0, ?, ?)
            """,
                (platform, model, now, now),
            )

            # 获取模型ID
            cursor.execute(
                """
                SELECT model_id FROM models WHERE platform = ? AND model = ?
            """,
                (platform, model),
            )

            result = cursor.fetchone()
            self.conn.commit()

            return result[0] if result else None

        except Exception as e:
            logging.error(f"创建或更新模型记录失败: {e}")
            raise

    def add_tokens_to_model(self, platform: str, model: str, tokens: int):
        """为指定模型累加token数量

        Args:
            platform: 平台名称
            model: 模型名称
            tokens: 要累加的token数量
        """
        try:
            cursor = self.conn.cursor()
            now = datetime.datetime.now().isoformat()

            # 确保模型记录存在
            self.create_or_update_model(platform, model)

            # 累加token数量
            cursor.execute(
                """
                UPDATE models 
                SET tokens = tokens + ?, updated_at = ?
                WHERE platform = ? AND model = ?
            """,
                (tokens, now, platform, model),
            )

            self.conn.commit()

        except Exception as e:
            logging.error(f"累加模型token失败: {e}")
            raise

    def get_model_statistics(self) -> List[Dict]:
        """获取所有模型的token使用统计

        Returns:
            模型统计列表
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT model_id, platform, model, tokens, created_at, updated_at
                FROM models
                ORDER BY tokens DESC
            """)

            results = []
            for row in cursor.fetchall():
                results.append({"model_id": row[0], "platform": row[1], "model": row[2], "tokens": row[3], "created_at": row[4], "updated_at": row[5]})
            return results

        except Exception as e:
            logging.error(f"获取模型统计失败: {e}")
            raise

    def get_platform_statistics(self) -> List[Dict]:
        """获取各平台的token使用统计

        Returns:
            平台统计列表
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT platform, SUM(tokens) as total_tokens, COUNT(*) as model_count
                FROM models
                GROUP BY platform
                ORDER BY total_tokens DESC
            """)

            results = []
            for row in cursor.fetchall():
                results.append({"platform": row[0], "total_tokens": row[1], "model_count": row[2]})
            return results

        except Exception as e:
            logging.error(f"获取平台统计失败: {e}")
            raise

    # ===== 对话层级Token统计方法 =====

    def add_tokens_to_user(self, user_id: str, tokens: int):
        """为用户累加token数量

        Args:
            user_id: 用户ID
            tokens: 要累加的token数量
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                UPDATE users 
                SET tokens = tokens + ?
                WHERE user_id = ?
            """,
                (tokens, user_id),
            )

            self.conn.commit()

        except Exception as e:
            logging.error(f"累加用户token失败: {e}")
            raise

    def add_tokens_to_conversation(self, conversation_id: str, tokens: int):
        """为会话累加token数量

        Args:
            conversation_id: 会话ID
            tokens: 要累加的token数量
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                UPDATE conversations 
                SET tokens = tokens + ?, updated_at = ?
                WHERE conversation_id = ?
            """,
                (tokens, datetime.datetime.now().isoformat(), conversation_id),
            )

            self.conn.commit()

        except Exception as e:
            logging.error(f"累加会话token失败: {e}")
            raise

    def add_tokens_to_round(self, round_id: str, tokens: int):
        """为轮次累加token数量

        Args:
            round_id: 轮次ID
            tokens: 要累加的token数量
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                UPDATE rounds 
                SET tokens = tokens + ?
                WHERE round_id = ?
            """,
                (tokens, round_id),
            )

            self.conn.commit()

        except Exception as e:
            logging.error(f"累加轮次token失败: {e}")
            raise

    def add_tokens_to_message(self, message_id: int, tokens: int, platform: str, model: str):
        """为消息设置token数量和平台模型信息

        Args:
            message_id: 消息ID
            tokens: token数量
            platform: 平台名称
            model: 模型名称
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                UPDATE messages 
                SET tokens = ?, platform = ?, model = ?
                WHERE message_id = ?
            """,
                (tokens, platform, model, message_id),
            )

            self.conn.commit()

        except Exception as e:
            logging.error(f"设置消息token失败: {e}")
            raise

    def update_round_execution_time(self, round_id: str, execution_time: float):
        """更新轮次执行时间

        Args:
            round_id: 轮次ID
            execution_time: 执行时间(秒)
        """
        try:
            cursor = self.conn.cursor()
            # 保留两位小数
            execution_time_rounded = round(execution_time, 2)
            cursor.execute(
                """
                UPDATE rounds 
                SET execution_time = ?
                WHERE round_id = ?
            """,
                (execution_time_rounded, round_id),
            )

            self.conn.commit()

        except Exception as e:
            logging.error(f"更新轮次执行时间失败: {e}")
            raise
