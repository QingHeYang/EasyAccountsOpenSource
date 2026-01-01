# 数据库架构文档

> 版本: 1.2
> 更新时间: 2026-01-01
> 状态: 正式版

## 一、概述

KoalaQ Hub 采用 **Repository 模式** 的分层数据库架构，基于 SQLite3 实现。

### 设计理念

- **分层清晰**：7层架构，职责分离
- **兼容性强**：RepositoryAdapter 提供向后兼容接口
- **扩展性好**：Repository 模式易于添加新功能
- **可切换性**：底层可替换为其他数据库

---

## 二、分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                    业务逻辑层                                │
│          (AgentExecutor, ConversationManager 等)            │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                 RepositoryAdapter (适配层)                   │
│   - 完全兼容原 SqliteStorage 接口                            │
│   - 转换 TokenUsage 对象为 4 个字段                          │
│   - 委托给 RepositoryFactory                                │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                RepositoryFactory (工厂层)                    │
│   - 单例模式，管理所有 Repository 实例                        │
│   - 线程安全 (threading.Lock)                               │
│   - 延迟加载各 Repository                                    │
└──┬──────────┬──────────┬──────────┬──────────┬──────────────┘
   │          │          │          │          │
┌──▼───┐  ┌──▼────┐  ┌──▼───┐  ┌──▼────┐  ┌──▼────┐
│User  │  │Conver-│  │Msg   │  │Summary│  │Token  │
│Repo  │  │sation │  │Repo  │  │Repo   │  │Repo   │
│      │  │Repo   │  │      │  │       │  │       │
└──┬───┘  └──┬────┘  └──┬───┘  └──┬────┘  └──┬────┘
   └──────────┴──────────┴──────────┴──────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                 BaseRepository (基础层)                      │
│   - _execute_query / _execute_insert / _execute_update      │
│   - _fetch_one / _fetch_all                                 │
│   - _build_where_clause / _build_update_clause              │
│   - 批量操作 _execute_batch                                  │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│               DatabaseConnection (连接层)                    │
│   - 单例模式，线程安全                                        │
│   - 表结构初始化 (_init_tables)                              │
│   - 索引创建                                                 │
│   - PRAGMA 配置 (外键约束、日志模式)                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   SQLite3 数据库文件                         │
│              (resource/database/koalaq.db)                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、数据库表结构

### 3.1 users 表 (用户表)

**业务用途**: 存储用户信息和累计 Token 消费统计

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| user_id | TEXT | PRIMARY KEY | 用户唯一标识 |
| username | TEXT | | 用户名 |
| created_at | TEXT | NOT NULL | 创建时间 (ISO格式) |
| extra_data | TEXT | | 扩展数据 (JSON) |
| total_tokens | INTEGER | DEFAULT 0 | 累计总 Token |
| prompt_tokens | INTEGER | DEFAULT 0 | 累计提示 Token |
| completion_tokens | INTEGER | DEFAULT 0 | 累计完成 Token |
| reasoning_tokens | INTEGER | DEFAULT 0 | 累计推理 Token |

**索引**: `idx_users_username`, `idx_users_total_tokens`

---

### 3.2 conversations 表 (对话表)

**业务用途**: 存储对话元数据，支持主对话和子 Agent 对话

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| conversation_id | TEXT | PRIMARY KEY | 对话ID |
| user_id | TEXT | NOT NULL, FK→users | 用户ID |
| title | TEXT | | 对话标题 |
| summary | TEXT | | 对话总结 |
| created_at | TEXT | NOT NULL | 创建时间 |
| updated_at | TEXT | NOT NULL | 更新时间 |
| tags | TEXT | | 标签 (逗号分隔) |
| total_tokens | INTEGER | DEFAULT 0 | 对话总 Token |
| prompt_tokens | INTEGER | DEFAULT 0 | 提示 Token |
| completion_tokens | INTEGER | DEFAULT 0 | 完成 Token |
| reasoning_tokens | INTEGER | DEFAULT 0 | 推理 Token |
| application_name | TEXT | | 应用名称 |
| enabled | INTEGER | DEFAULT 1 | 是否启用 (软删除) |
| is_agent_call | INTEGER | DEFAULT 0 | 是否为子 Agent 调用 |
| parent_conversation_id | TEXT | FK→conversations | 父对话ID |

**索引**: `idx_conversations_user_id`, `idx_conversations_updated_at`

**业务场景**:
- `is_agent_call=0`: 主对话（用户直接发起）
- `is_agent_call=1`: 子对话（call_agent 工具创建）
- `parent_conversation_id`: 关联父对话，用于追溯

---

### 3.3 rounds 表 (轮次表)

**业务用途**: 存储每轮用户-AI 交互

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| round_id | TEXT | PRIMARY KEY | 轮次ID |
| conversation_id | TEXT | NOT NULL, FK→conversations | 对话ID |
| summary | TEXT | | 轮次摘要 |
| created_at | TEXT | NOT NULL | 创建时间 |
| user_rating | INTEGER | | 用户评分 (1-5) |
| extra_data | TEXT | | 扩展数据 |
| total_tokens | INTEGER | DEFAULT 0 | 轮次总 Token |
| prompt_tokens | INTEGER | DEFAULT 0 | 提示 Token |
| completion_tokens | INTEGER | DEFAULT 0 | 完成 Token |
| reasoning_tokens | INTEGER | DEFAULT 0 | 推理 Token |
| execution_time | REAL | | 执行时间 (秒) |

**索引**: `idx_rounds_conversation_id`, `idx_rounds_created_at`

---

### 3.4 messages 表 (消息表)

**业务用途**: 存储所有消息（用户输入、AI回复、工具调用等）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| message_id | INTEGER | PRIMARY KEY AUTOINCREMENT | 消息ID |
| round_id | TEXT | NOT NULL, FK→rounds | 轮次ID |
| role | TEXT | NOT NULL | 角色 (user/assistant/tool/error) |
| content | TEXT | NOT NULL | 消息内容 |
| type | TEXT | NOT NULL | 消息类型 (见下表) |
| timestamp | TEXT | NOT NULL | 时间戳 |
| tool_success | INTEGER | | 工具执行成功 (1/0) |
| tool_call_ids | TEXT | | 工具调用ID列表 (\|分隔) |
| tool_call_raw | TEXT | | 工具调用原始 JSON |
| agent_id | TEXT | | 子 Agent ID |
| tool_name | TEXT | | 工具名称 |
| sub_conversation_id | TEXT | | 子会话ID |
| platform | TEXT | | LLM 平台 |
| model | TEXT | | LLM 模型 |
| total_tokens | INTEGER | DEFAULT 0 | Token 数 |
| prompt_tokens | INTEGER | DEFAULT 0 | 提示 Token |
| completion_tokens | INTEGER | DEFAULT 0 | 完成 Token |
| reasoning_tokens | INTEGER | DEFAULT 0 | 推理 Token |
| reasoning_content | TEXT | | 推理内容 (思维链) |
| attachments | TEXT | | VL 附件 (JSON数组) |

> **VL 支持**: `attachments` 存储 JSON 格式的附件列表，详见 [VL 运行流程](./VL_运行流程.md)

**消息类型 (MessageType)**:

| 类型 | 说明 | role | 典型内容 |
|------|------|------|----------|
| CONTENT | 普通内容 | user/assistant | 文本消息 |
| TOOL_CALL | 工具调用 | assistant | tool_call_raw JSON |
| TOOL_RESULT | 工具结果 | tool | 工具返回值 |
| ERROR | 错误 | error | 错误信息 |
| AGENT_START | 子Agent开始 | assistant | agent_id |
| AGENT_END | 子Agent结束 | assistant | 结果 + sub_conversation_id |

**索引**: `idx_messages_round_id`, `idx_messages_role`, `idx_messages_type`, `idx_messages_agent_id`, `idx_messages_tool_name`, `idx_messages_sub_conversation_id`

---

### 3.5 summary_snapshots 表 (总结快照表)

**业务用途**: 存储对话的阶段性总结快照，用于长对话上下文压缩

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| snapshot_id | INTEGER | PRIMARY KEY AUTOINCREMENT | 快照ID |
| conversation_id | TEXT | NOT NULL, FK→conversations | 对话ID |
| based_on_round_id | TEXT | FK→rounds | 基于的轮次ID |
| context_summary | TEXT | NOT NULL | 总结内容 |
| created_at | TEXT | NOT NULL | 创建时间 |
| total_tokens | INTEGER | DEFAULT 0 | 生成消耗 Token |
| prompt_tokens | INTEGER | DEFAULT 0 | 提示 Token |
| completion_tokens | INTEGER | DEFAULT 0 | 完成 Token |
| reasoning_tokens | INTEGER | DEFAULT 0 | 推理 Token |
| summary_type | TEXT | DEFAULT 'context' | 快照类型 |

**索引**: `idx_snapshots_conversation_id`

---

### 3.6 summary_log 表 (总结日志表)

**业务用途**: 记录所有总结操作日志，用于审计和性能分析

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| log_id | INTEGER | PRIMARY KEY AUTOINCREMENT | 日志ID |
| summary_content | TEXT | NOT NULL | 输入内容 |
| summary_result | TEXT | | 总结结果 |
| status | TEXT | NOT NULL | 状态 (pending/success/failed) |
| conversation_id | TEXT | FK→conversations | 对话ID |
| round_id | TEXT | FK→rounds | 轮次ID |
| snapshot_id | INTEGER | FK→summary_snapshots | 快照ID |
| platform | TEXT | | LLM 平台 |
| model | TEXT | | LLM 模型 |
| created_at | TEXT | NOT NULL | 创建时间 |
| updated_at | TEXT | | 更新时间 |
| error_message | TEXT | | 错误信息 |
| execution_time | REAL | | 执行时间 (秒) |
| total_tokens | INTEGER | DEFAULT 0 | 消耗 Token |
| prompt_tokens | INTEGER | DEFAULT 0 | 提示 Token |
| completion_tokens | INTEGER | DEFAULT 0 | 完成 Token |
| reasoning_tokens | INTEGER | DEFAULT 0 | 推理 Token |

**索引**: `idx_summary_log_conversation_id`, `idx_summary_log_status`

---

### 3.7 models 表 (LLM 配置统计表)

**业务用途**: 存储 LLM 配置信息并统计各配置的使用情况

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| llm_id | TEXT | PRIMARY KEY | LLM 配置唯一标识 (UUID) |
| llm_config_name | TEXT | UNIQUE NOT NULL | LLM 配置名称 |
| platform | TEXT | NOT NULL | 平台名称 |
| model | TEXT | NOT NULL | 模型名称 |
| api_key | TEXT | | API 密钥 |
| url | TEXT | | API 地址 |
| temperature | REAL | DEFAULT 0.7 | 温度参数 |
| top_p | REAL | DEFAULT 1.0 | Top-P 参数 |
| max_tokens | INTEGER | DEFAULT 4096 | 最大 Token 数 |
| description | TEXT | DEFAULT '' | 描述信息 |
| total_tokens | INTEGER | DEFAULT 0 | 累计总 Token |
| prompt_tokens | INTEGER | DEFAULT 0 | 累计提示 Token |
| completion_tokens | INTEGER | DEFAULT 0 | 累计完成 Token |
| reasoning_tokens | INTEGER | DEFAULT 0 | 累计推理 Token |
| request_count | INTEGER | DEFAULT 0 | 请求次数 |
| success_count | INTEGER | DEFAULT 0 | 成功次数 |
| error_count | INTEGER | DEFAULT 0 | 失败次数 |
| avg_response_time | REAL | DEFAULT 0 | 平均响应时间 |
| created_at | TEXT | NOT NULL | 创建时间 |
| updated_at | TEXT | NOT NULL | 更新时间 |

**约束**: `llm_config_name UNIQUE`

**索引**: `idx_models_platform`, `idx_models_total_tokens`, `idx_models_llm_config_name`

> **v2.6.0 变更**: 表结构重构，详见 [版本迁移指南](./database_版本迁移指南.md)

---

## 四、表关系图

```
users
  │
  └──< conversations (user_id → users.user_id)
           │
           ├──< conversations (parent_conversation_id → conversations.conversation_id)
           │    [自引用：子Agent对话]
           │
           ├──< rounds (conversation_id → conversations.conversation_id)
           │       │
           │       └──< messages (round_id → rounds.round_id)
           │
           ├──< summary_snapshots (conversation_id → conversations.conversation_id)
           │       │
           │       └──< summary_log (snapshot_id → summary_snapshots.snapshot_id)
           │
           └──< summary_log (conversation_id → conversations.conversation_id)

models (独立表，无外键关联)
```

---

## 五、Repository 类及方法

### 5.1 UserRepository

**文件**: `database/repositories/user_repository.py`

```python
class UserRepository:
    # CRUD
    def add_user(user: User) -> None
    def get_user(user_id: str) -> Optional[User]
    def get_user_by_username(username: str) -> Optional[User]
    def update_user(user_id: str, updates: Dict) -> bool
    def delete_user(user_id: str) -> bool

    # Token 管理
    def add_tokens_to_user(user_id, total, prompt, completion, reasoning) -> None

    # 统计
    def get_user_token_stats(user_id: str) -> Dict
    def list_users(limit: int, offset: int) -> List[Dict]
    def get_user_count() -> int
```

---

### 5.2 ConversationRepository

**文件**: `database/repositories/conversation_repository.py`

```python
class ConversationRepository:
    # 对话操作
    def create_conversation(user_id, conversation_id, application_name,
                           is_agent_call=0, parent_conversation_id=None) -> None
    def get_conversation(conversation_id, user_id=None, application_name=None) -> Optional[Conversation]
    def get_user_conversations(user_id, application_names=None, limit=50, offset=0) -> List[Conversation]
    def update_conversation_title(conversation_id, title) -> None
    def update_conversation_summary(conversation_id, summary) -> None
    def delete_conversation(conversation_id) -> bool  # 软删除
    def restore_conversation(conversation_id) -> bool
    def permanently_delete_conversation(conversation_id) -> bool

    # 轮次操作
    def create_round(conversation_id, round_id) -> None
    def get_round(round_id, conversation_id=None) -> Optional[Round]
    def get_rounds_by_conversation(conversation_id, limit=None) -> List[Round]
    def get_rounds_by_memory_window(conversation_id, memory_window) -> List[Round]
    def update_round_summary(round_id, summary) -> None

    # Token 管理
    def add_tokens_to_conversation(conversation_id, total, prompt, completion, reasoning) -> None
    def add_tokens_to_round(round_id, total, prompt, completion, reasoning) -> None
```

---

### 5.3 MessageRepository

**文件**: `database/repositories/message_repository.py`

```python
class MessageRepository:
    # 消息操作
    def add_message(round_id: str, message: Message) -> int
    def get_message(message_id: int) -> Optional[Message]
    def get_messages_by_round(round_id: str) -> List[Message]
    def get_messages_by_conversation(conversation_id, limit=None) -> List[Message]
    def get_messages_by_type(round_id, message_type: MessageType) -> List[Message]

    # 系统消息 (特殊: round_id = conversation_id)
    def create_system_message(conversation_id, message: Message) -> int
    def get_system_message(conversation_id) -> Optional[Message]
    def update_system_message(conversation_id, message: Message) -> None

    # Token 管理
    def add_tokens_to_message(message_id, total, platform, model, prompt, completion, reasoning) -> None
```

---

### 5.4 SummaryRepository

**文件**: `database/repositories/summary_repository.py`

```python
class SummaryRepository:
    # 总结日志
    def create_summary_log(summary_log: SummaryLog) -> int
    def update_summary_log(log_id, summary_result=None, status=None, error_message=None) -> bool
    def get_summary_logs_by_conversation(conversation_id, limit=50) -> List[SummaryLog]
    def get_summary_log_statistics() -> Dict

    # 快照
    def create_snapshot(conversation_id, based_on_round_id, context_summary) -> int
    def get_latest_snapshot(conversation_id) -> Optional[Dict]
    def get_recent_snapshots(conversation_id, limit=2) -> List[Dict]
    def get_rounds_since_last_snapshot(conversation_id) -> List[Dict]
```

---

### 5.5 TokenRepository

**文件**: `database/repositories/token_repository.py`

```python
class TokenRepository:
    def create_or_update_model(platform: str, model: str) -> int
    def get_model_by_platform_and_name(platform, model) -> Optional[Model]
    def add_tokens_to_model(platform, model, total, prompt, completion, reasoning) -> None
    def get_model_statistics() -> List[Dict]
    def get_platform_statistics() -> List[Dict]
```

---

## 六、初始化流程

### 6.1 启动时序

```
__main__.py
    │
    ├─→ config.get_database_path()
    │       └─→ 返回 resource/database/koalaq.db
    │
    └─→ RepositoryAdapter(db_path)
            │
            └─→ RepositoryFactory(db_path)
                    │
                    └─→ DatabaseConnection(db_path)
                            │
                            ├─→ _init_connection()
                            │       ├─→ 创建目录 (如不存在)
                            │       ├─→ sqlite3.connect()
                            │       ├─→ PRAGMA foreign_keys = ON
                            │       └─→ PRAGMA journal_mode = DELETE
                            │
                            └─→ _init_tables()
                                    ├─→ CREATE TABLE IF NOT EXISTS users...
                                    ├─→ CREATE TABLE IF NOT EXISTS conversations...
                                    ├─→ CREATE TABLE IF NOT EXISTS rounds...
                                    ├─→ CREATE TABLE IF NOT EXISTS messages...
                                    ├─→ CREATE TABLE IF NOT EXISTS summary_snapshots...
                                    ├─→ CREATE TABLE IF NOT EXISTS summary_log...
                                    ├─→ CREATE TABLE IF NOT EXISTS models...
                                    └─→ CREATE INDEX IF NOT EXISTS idx_*...
```

### 6.2 关键代码位置

| 步骤 | 文件 | 方法 |
|------|------|------|
| 入口 | `__main__.py:213` | `RepositoryAdapter(str(db_path))` |
| 工厂 | `factory/repository_factory.py` | `RepositoryFactory.__init__()` |
| 连接 | `base/database_connection.py` | `DatabaseConnection.__init__()` |
| 建表 | `base/database_connection.py` | `_init_tables()` |

---

## 七、新增字段规范

### 7.1 添加新字段步骤

**步骤 1**: 修改 DDL (database_connection.py)

```python
# base/database_connection.py → _init_tables()
# 在对应表的 CREATE TABLE 语句中添加字段

CREATE TABLE IF NOT EXISTS users (
    ...
    new_field TEXT DEFAULT '',  # 新增字段，必须有默认值
    ...
)
```

**步骤 2**: 修改数据模型 (data_models.py)

```python
# models/data_models.py
@dataclass
class User:
    ...
    new_field: str = ""  # 与 DDL 默认值一致
```

**步骤 3**: 修改 Repository 方法

```python
# repositories/user_repository.py

# 1. 如果是插入时需要的字段，修改 add_user()
def add_user(self, user: User) -> None:
    self._execute_insert(
        "users",
        {
            ...
            "new_field": user.new_field,  # 添加
        }
    )

# 2. 如果需要更新，添加 update 方法或修改现有方法
def update_user_new_field(self, user_id: str, value: str) -> bool:
    return self._execute_update("users", {"new_field": value}, {"user_id": user_id})

# 3. 如果需要查询，确保 _row_to_user() 正确映射
def _row_to_user(self, row: sqlite3.Row) -> User:
    return User(
        ...
        new_field=row["new_field"],
    )
```

**步骤 4**: 如需要，更新 RepositoryAdapter

```python
# repository_adapter.py
# 如果新字段需要在适配层暴露，添加对应方法
def update_user_new_field(self, user_id: str, value: str) -> bool:
    return self.factory.get_user_repository().update_user_new_field(user_id, value)
```

### 7.2 规范要点

| 项目 | 要求 |
|------|------|
| 默认值 | DDL 中必须有 DEFAULT，保证旧数据兼容 |
| 类型一致 | DDL 类型、Python 类型、默认值三者一致 |
| 索引 | 如需按该字段查询，添加索引 |
| 非空约束 | 谨慎使用 NOT NULL，可能导致旧数据问题 |
| 外键 | 如需外键，确保引用表已存在 |

### 7.3 迁移已有数据库

如果数据库已存在，需要执行 ALTER TABLE：

```python
# 可在 _init_tables() 末尾添加迁移逻辑
try:
    self.conn.execute("ALTER TABLE users ADD COLUMN new_field TEXT DEFAULT ''")
except sqlite3.OperationalError:
    pass  # 字段已存在
```

---

## 八、切换数据库源

### 8.1 架构支持

当前架构为切换数据库预留了扩展点：

```
                    RepositoryAdapter
                          │
                          ▼
                   RepositoryFactory
                          │
                          ▼
                   BaseRepository  ← 抽象此层
                          │
                          ▼
               DatabaseConnection  ← 替换此层
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
           SQLite      MySQL      PostgreSQL
```

### 8.2 切换到 MySQL/PostgreSQL 步骤

**步骤 1**: 创建新的数据库连接类

```python
# base/mysql_connection.py
class MySQLConnection:
    def __init__(self, host, port, user, password, database):
        import pymysql
        self.conn = pymysql.connect(
            host=host, port=port, user=user,
            password=password, database=database,
            cursorclass=pymysql.cursors.DictCursor
        )

    def _init_tables(self):
        # MySQL 语法的建表语句
        pass
```

**步骤 2**: 抽象 BaseRepository

```python
# base/base_repository.py
class BaseRepository:
    def __init__(self, connection):  # 接收连接实例
        self.conn = connection

    # 抽象 SQL 方言差异
    def _get_placeholder(self) -> str:
        return "?"  # SQLite
        # return "%s"  # MySQL/PostgreSQL
```

**步骤 3**: 修改 RepositoryFactory

```python
# factory/repository_factory.py
class RepositoryFactory:
    def __init__(self, db_type: str = "sqlite", **kwargs):
        if db_type == "sqlite":
            self._db = DatabaseConnection(kwargs.get("db_path"))
        elif db_type == "mysql":
            self._db = MySQLConnection(**kwargs)
        elif db_type == "postgresql":
            self._db = PostgreSQLConnection(**kwargs)
```

**步骤 4**: 修改配置

```ini
# config/config.ini
[database]
type = mysql
host = localhost
port = 3306
user = root
password = xxx
database = koalaq
```

### 8.3 SQL 方言差异处理

| 特性 | SQLite | MySQL | PostgreSQL |
|------|--------|-------|------------|
| 占位符 | `?` | `%s` | `%s` |
| 自增 | `INTEGER PRIMARY KEY` | `INT AUTO_INCREMENT` | `SERIAL` |
| 布尔 | INTEGER (0/1) | TINYINT / BOOLEAN | BOOLEAN |
| 时间 | TEXT | DATETIME | TIMESTAMP |
| 获取插入ID | `cursor.lastrowid` | `cursor.lastrowid` | `RETURNING id` |

### 8.4 建议的抽象接口

```python
# base/db_interface.py
from abc import ABC, abstractmethod

class DatabaseInterface(ABC):
    @abstractmethod
    def connect(self) -> None: pass

    @abstractmethod
    def execute(self, sql: str, params: tuple) -> Any: pass

    @abstractmethod
    def fetch_one(self, sql: str, params: tuple) -> Optional[Dict]: pass

    @abstractmethod
    def fetch_all(self, sql: str, params: tuple) -> List[Dict]: pass

    @abstractmethod
    def get_last_insert_id(self) -> int: pass

    @abstractmethod
    def close(self) -> None: pass
```

---

## 九、文件位置索引

| 类型 | 文件路径 |
|------|----------|
| 数据模型 | `koalaq_hub/models/data_models.py` |
| 消息模型 | `koalaq_hub/models/message.py` |
| 数据库连接 | `koalaq_hub/database/base/database_connection.py` |
| 基础 Repository | `koalaq_hub/database/base/base_repository.py` |
| Repository 工厂 | `koalaq_hub/database/factory/repository_factory.py` |
| Repository 适配器 | `koalaq_hub/database/repository_adapter.py` |
| UserRepository | `koalaq_hub/database/repositories/user_repository.py` |
| ConversationRepository | `koalaq_hub/database/repositories/conversation_repository.py` |
| MessageRepository | `koalaq_hub/database/repositories/message_repository.py` |
| SummaryRepository | `koalaq_hub/database/repositories/summary_repository.py` |
| TokenRepository | `koalaq_hub/database/repositories/token_repository.py` |

---

## 十、业务场景示例

### 10.1 用户发起对话

```
1. 创建对话
   → ConversationRepository.create_conversation(user_id, conv_id, app_name)

2. 创建轮次
   → ConversationRepository.create_round(conv_id, round_id)

3. 保存用户消息
   → MessageRepository.add_message(round_id, Message(role="user", type="CONTENT"))

4. 保存 AI 回复
   → MessageRepository.add_message(round_id, Message(role="assistant", type="CONTENT"))

5. 更新 Token 统计
   → MessageRepository.add_tokens_to_message(...)
   → ConversationRepository.add_tokens_to_round(...)
   → ConversationRepository.add_tokens_to_conversation(...)
   → UserRepository.add_tokens_to_user(...)
   → TokenRepository.add_tokens_to_model(...)
```

### 10.2 子 Agent 调用

```
1. 主对话中触发 call_agent

2. 创建子对话
   → ConversationRepository.create_conversation(
       user_id, sub_conv_id, app_name,
       is_agent_call=1,
       parent_conversation_id=main_conv_id
     )

3. 子对话执行（同普通对话流程）

4. 子对话结果保存到主对话
   → MessageRepository.add_message(
       main_round_id,
       Message(type="AGENT_END", sub_conversation_id=sub_conv_id)
     )
```

### 10.3 长对话总结

```
1. 检查轮次数量
   → ConversationRepository.get_rounds_count(conv_id)

2. 如超过阈值，创建快照
   → SummaryRepository.create_snapshot(conv_id, last_round_id, summary)

3. 查询时获取最近快照
   → SummaryRepository.get_recent_snapshots(conv_id, limit=2)

4. 获取快照后的轮次
   → SummaryRepository.get_rounds_since_last_snapshot(conv_id)
```

---

## 十一、性能优化建议

### 11.1 索引优化

当前已有 15 个索引，覆盖主要查询场景。如有新的高频查询：

```python
# 在 _init_tables() 中添加
self.conn.execute("CREATE INDEX IF NOT EXISTS idx_xxx ON table(column)")
```

### 11.2 批量操作

使用 `_execute_batch()` 进行批量插入：

```python
messages_data = [msg.to_dict() for msg in messages]
self._execute_batch("INSERT INTO messages (...) VALUES (...)", messages_data)
```

### 11.3 连接复用

`DatabaseConnection` 是单例，自动复用连接。避免在循环中创建新的 Repository 实例。

### 11.4 查询限制

所有列表查询都支持 `limit` 和 `offset` 参数，避免全表扫描。
