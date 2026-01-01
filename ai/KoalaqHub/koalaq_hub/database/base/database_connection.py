"""
数据库连接管理器
支持SQLite，为未来扩展PostgreSQL/MySQL预留接口
"""

import sqlite3
from pathlib import Path
from threading import Lock
from typing import List

from ...config.settings import Configuration
from ...core.logging_utils import ManagerLogger


class DatabaseConnection:
    """数据库连接管理器 - 单例模式，线程安全"""

    _instance = None
    _lock = Lock()

    def __new__(cls, db_path: str = None):
        """单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = None):
        """初始化数据库连接管理器

        Args:
            db_path: 数据库文件路径，如果为None则使用配置文件中的路径
        """
        self.logger = ManagerLogger("DatabaseConnection")
        
        if self._initialized:
            return

        if db_path:
            self.db_path = db_path
        else:
            # 动态获取配置，确保使用最新的环境变量
            current_config = Configuration()
            self.db_path = current_config.get_database_path()

        self.conn = None
        self._lock = Lock()
        self._initialized = True
        # 初始化数据库连接和表结构
        self._init_connection()
        self._init_tables()

        self.logger.info(f"数据库连接管理器初始化完成: {self.db_path}")

    def _init_connection(self):
        """初始化数据库连接"""
        try:
            # 确保数据库目录存在
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)

            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # 让查询结果返回字典格式

            # 启用外键约束
            self.conn.execute("PRAGMA foreign_keys = ON")

            # 启用WAL模式，支持并发读写
            self.conn.execute("PRAGMA journal_mode = DELETE")

            self.conn.commit()

        except Exception as e:
            self.logger.error(f"数据库连接初始化失败: {e}")
            raise

    def _init_tables(self):
        """初始化数据库表结构"""
        try:
            cursor = self.conn.cursor()

            # 创建所有表的DDL语句
            ddl_scripts = [
                # 用户表
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    created_at TEXT NOT NULL,
                    extra_data TEXT,
                    total_tokens INTEGER DEFAULT 0,
                    prompt_tokens INTEGER DEFAULT 0,
                    completion_tokens INTEGER DEFAULT 0,
                    reasoning_tokens INTEGER DEFAULT 0
                )
                """,
                # 对话表
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT,
                    summary TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    tags TEXT,
                    total_tokens INTEGER DEFAULT 0,
                    prompt_tokens INTEGER DEFAULT 0,
                    completion_tokens INTEGER DEFAULT 0,
                    reasoning_tokens INTEGER DEFAULT 0,
                    application_name TEXT,
                    enabled INTEGER DEFAULT 1,
                    is_agent_call INTEGER DEFAULT 0,  -- 是否为agent调用创建的对话
                    parent_conversation_id TEXT,       -- 父对话ID（如果是agent调用）
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (parent_conversation_id) REFERENCES conversations (conversation_id)
                )
                """,
                # 轮次表
                """
                CREATE TABLE IF NOT EXISTS rounds (
                    round_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    summary TEXT,
                    created_at TEXT NOT NULL,
                    user_rating INTEGER,
                    extra_data TEXT,
                    total_tokens INTEGER DEFAULT 0,
                    prompt_tokens INTEGER DEFAULT 0,
                    completion_tokens INTEGER DEFAULT 0,
                    reasoning_tokens INTEGER DEFAULT 0,
                    execution_time REAL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (conversation_id)
                )
                """,
                # 消息表
                """
                CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    round_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    tool_success INTEGER,
                    tool_call_ids TEXT,  -- 多个tool_call_id用|分割
                    tool_call_raw TEXT,  -- tool_calls的原始JSON字符串
                    agent_id TEXT,  -- 子Agent的ID（用于AGENT_START和AGENT_END类型的消息）
                    tool_name TEXT,  -- 工具名称（用于TOOL_RESULT类型的消息）
                    sub_conversation_id TEXT,  -- 子会话ID（用于AGENT_END类型的消息）
                    platform TEXT,
                    model TEXT,
                    total_tokens INTEGER DEFAULT 0,
                    prompt_tokens INTEGER DEFAULT 0,
                    completion_tokens INTEGER DEFAULT 0,
                    reasoning_tokens INTEGER DEFAULT 0,
                    reasoning_content TEXT,
                    attachments TEXT DEFAULT '',  -- VL附件JSON数组
                    FOREIGN KEY (round_id) REFERENCES rounds (round_id)
                )
                """,
                # 总结快照表
                """
                CREATE TABLE IF NOT EXISTS summary_snapshots (
                    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    based_on_round_id TEXT,
                    context_summary TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    total_tokens INTEGER DEFAULT 0,
                    prompt_tokens INTEGER DEFAULT 0,
                    completion_tokens INTEGER DEFAULT 0,
                    reasoning_tokens INTEGER DEFAULT 0,
                    summary_type TEXT DEFAULT 'context',
                    FOREIGN KEY (conversation_id) REFERENCES conversations (conversation_id),
                    FOREIGN KEY (based_on_round_id) REFERENCES rounds (round_id)
                )
                """,
                # 总结日志表
                """
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
                    total_tokens INTEGER DEFAULT 0,
                    prompt_tokens INTEGER DEFAULT 0,
                    completion_tokens INTEGER DEFAULT 0,
                    reasoning_tokens INTEGER DEFAULT 0,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (conversation_id),
                    FOREIGN KEY (round_id) REFERENCES rounds (round_id),
                    FOREIGN KEY (snapshot_id) REFERENCES summary_snapshots (snapshot_id)
                )
                """,
                # LLM配置表（含统计数据）
                """
                CREATE TABLE IF NOT EXISTS models (
                    llm_id TEXT PRIMARY KEY,
                    llm_config_name TEXT UNIQUE NOT NULL,
                    platform TEXT NOT NULL,
                    model TEXT NOT NULL,
                    api_key TEXT,
                    url TEXT,
                    temperature REAL DEFAULT 0.7,
                    top_p REAL DEFAULT 1.0,
                    max_tokens INTEGER DEFAULT 4096,
                    description TEXT DEFAULT '',
                    total_tokens INTEGER DEFAULT 0,
                    prompt_tokens INTEGER DEFAULT 0,
                    completion_tokens INTEGER DEFAULT 0,
                    reasoning_tokens INTEGER DEFAULT 0,
                    request_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    avg_response_time REAL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """,
            ]

            # 创建索引
            index_scripts = [
                "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
                "CREATE INDEX IF NOT EXISTS idx_users_total_tokens ON users(total_tokens)",
                "CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at)",
                "CREATE INDEX IF NOT EXISTS idx_rounds_conversation_id ON rounds(conversation_id)",
                "CREATE INDEX IF NOT EXISTS idx_rounds_created_at ON rounds(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_messages_round_id ON messages(round_id)",
                "CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role)",
                "CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(type)",
                "CREATE INDEX IF NOT EXISTS idx_messages_agent_id ON messages(agent_id)",
                "CREATE INDEX IF NOT EXISTS idx_messages_tool_name ON messages(tool_name)",
                "CREATE INDEX IF NOT EXISTS idx_messages_sub_conversation_id ON messages(sub_conversation_id)",
                "CREATE INDEX IF NOT EXISTS idx_snapshots_conversation_id ON summary_snapshots(conversation_id)",
                "CREATE INDEX IF NOT EXISTS idx_summary_log_conversation_id ON summary_log(conversation_id)",
                "CREATE INDEX IF NOT EXISTS idx_summary_log_status ON summary_log(status)",
                "CREATE INDEX IF NOT EXISTS idx_models_platform ON models(platform)",
                "CREATE INDEX IF NOT EXISTS idx_models_total_tokens ON models(total_tokens)",
                "CREATE INDEX IF NOT EXISTS idx_models_llm_config_name ON models(llm_config_name)",
            ]

            # 执行建表语句
            for script in ddl_scripts:
                cursor.execute(script)

            # 执行索引创建语句
            for index in index_scripts:
                cursor.execute(index)

            # 数据库迁移：为已有数据库添加新字段
            migrations = [
                # VL 附件支持
                ("messages", "attachments", "TEXT DEFAULT ''"),
                # models 表新字段
                ("models", "llm_config_name", "TEXT"),
            ]
            for table, column, definition in migrations:
                try:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
                    self.logger.info(f"数据库迁移：添加 {table}.{column} 字段")
                except sqlite3.OperationalError:
                    pass  # 字段已存在，忽略

            # 检查 models 表结构是否兼容，如果旧表结构不兼容则重建
            try:
                cursor.execute("SELECT llm_config_name FROM models LIMIT 1")
            except sqlite3.OperationalError:
                # 旧表结构不兼容，重建 models 表
                self.logger.warning("检测到旧版 models 表结构，正在重建...")
                cursor.execute("DROP TABLE IF EXISTS models")
                cursor.execute("""
                    CREATE TABLE models (
                        llm_id TEXT PRIMARY KEY,
                        llm_config_name TEXT UNIQUE NOT NULL,
                        platform TEXT NOT NULL,
                        model TEXT NOT NULL,
                        api_key TEXT,
                        url TEXT,
                        temperature REAL DEFAULT 0.7,
                        top_p REAL DEFAULT 1.0,
                        max_tokens INTEGER DEFAULT 4096,
                        description TEXT DEFAULT '',
                        total_tokens INTEGER DEFAULT 0,
                        prompt_tokens INTEGER DEFAULT 0,
                        completion_tokens INTEGER DEFAULT 0,
                        reasoning_tokens INTEGER DEFAULT 0,
                        request_count INTEGER DEFAULT 0,
                        success_count INTEGER DEFAULT 0,
                        error_count INTEGER DEFAULT 0,
                        avg_response_time REAL DEFAULT 0,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)

            self.conn.commit()
            self.logger.info("数据库表结构初始化完成")

        except Exception as e:
            self.logger.error(f"数据库表结构初始化失败: {e}")
            raise

    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接

        Returns:
            sqlite3.Connection: 数据库连接对象
        """
        with self._lock:
            if self.conn is None:
                self._init_connection()
                self._init_tables()
            return self.conn

    def close(self):
        """关闭数据库连接"""
        with self._lock:
            if self.conn:
                self.conn.close()
                self.conn = None
                self.logger.info("数据库连接已关闭")

    def execute_ddl(self, ddl_scripts: List[str]):
        """执行DDL语句（建表、索引等）

        Args:
            ddl_scripts: DDL语句列表
        """
        try:
            cursor = self.conn.cursor()
            for script in ddl_scripts:
                cursor.execute(script)
            self.conn.commit()
            self.logger.info(f"执行DDL语句完成，共{len(ddl_scripts)}条")
        except Exception as e:
            self.logger.error(f"执行DDL语句失败: {e}")
            raise

    def __del__(self):
        """析构函数，确保连接被关闭"""
        self.close()
