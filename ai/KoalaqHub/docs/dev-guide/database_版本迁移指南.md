# 数据库版本迁移指南

本文档记录 KoalaqHub 数据库表结构的版本变更和迁移策略。

---

## 版本变更记录

### v2.6.0 (当前版本)

#### 1. `models` 表重构（破坏性变更）

**旧版结构：**
```sql
CREATE TABLE models (
    model_id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    model TEXT NOT NULL,
    total_tokens INTEGER DEFAULT 0,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    reasoning_tokens INTEGER DEFAULT 0,
    request_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    avg_response_time REAL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(platform, model)
)
```

**新版结构：**
```sql
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
```

**变更说明：**

| 变更类型 | 字段 | 说明 |
|----------|------|------|
| 主键变更 | `model_id` → `llm_id` | INTEGER 自增 → TEXT UUID |
| 新增字段 | `llm_config_name` | LLM 配置名称，唯一约束 |
| 新增字段 | `api_key` | API 密钥 |
| 新增字段 | `url` | API 地址 |
| 新增字段 | `temperature` | 温度参数 |
| 新增字段 | `top_p` | Top-P 参数 |
| 新增字段 | `max_tokens` | 最大 Token 数 |
| 新增字段 | `description` | 描述信息 |
| 唯一约束 | `UNIQUE(platform, model)` → `llm_config_name UNIQUE` | 约束条件变更 |

**迁移策略：** 自动 DROP 并重建（统计数据会丢失）

---

#### 2. `messages` 表新增字段

**新增字段：**
```sql
ALTER TABLE messages ADD COLUMN attachments TEXT DEFAULT ''
```

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `attachments` | TEXT | `''` | VL 附件 JSON 数组 |

**迁移策略：** ALTER TABLE 添加字段（兼容迁移）

---

## 表结构完整对照

### 不变的表

以下表在 v2.6.0 中保持不变：

| 表名 | 说明 |
|------|------|
| `users` | 用户表 |
| `conversations` | 对话表 |
| `rounds` | 轮次表 |
| `summary_snapshots` | 总结快照表 |
| `summary_log` | 总结日志表 |

### 变更的表

| 表名 | 变更类型 | 说明 |
|------|----------|------|
| `models` | 重构 | 主键、字段、约束全部变更 |
| `messages` | 新增字段 | 添加 `attachments` 字段 |

---

## 自动迁移逻辑

代码位置：`koalaq_hub/database/base/database_connection.py` 的 `_init_tables()` 方法

### 迁移执行流程

```
1. 执行 CREATE TABLE IF NOT EXISTS（不影响已存在的表）
2. 执行 CREATE INDEX IF NOT EXISTS（不影响已存在的索引）
3. 执行 ALTER TABLE 迁移（添加缺失字段）
4. 检查 models 表兼容性
   └── 如果缺少 llm_config_name 列 → DROP 并重建
5. COMMIT
```

### 迁移代码

```python
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
    cursor.execute("""CREATE TABLE models (...)""")
```

---

## 手动迁移指南

### 场景 1：全新部署

无需任何操作，系统自动创建正确的表结构。

### 场景 2：从旧版升级

**方式 A：自动迁移（推荐）**

直接启动新版本，系统会自动：
1. 为 `messages` 表添加 `attachments` 字段
2. 重建 `models` 表（旧统计数据会丢失）

**方式 B：手动清理数据库**

如果自动迁移失败，可以手动清理：

```bash
# 进入容器
docker exec -it easy_accounts_ai bash

# 删除数据库文件
rm /app/koalaq_hub_python/resource/database/koalaq.db

# 重启容器
exit
docker restart easy_accounts_ai
```

或者在宿主机删除挂载的数据库目录：

```bash
# 停止容器
docker-compose stop ai

# 清理数据库目录
rm -rf ./AI/database/*

# 重启容器
docker-compose up -d ai
```

---

## 数据影响说明

### 会丢失的数据

| 数据类型 | 影响 | 说明 |
|----------|------|------|
| LLM 统计数据 | `models` 表重建 | Token 使用统计、请求计数归零 |

### 会保留的数据

| 数据类型 | 说明 |
|----------|------|
| 用户数据 | `users` 表保持不变 |
| 对话历史 | `conversations`、`rounds`、`messages` 保持不变 |
| 总结数据 | `summary_snapshots`、`summary_log` 保持不变 |

---

## 版本兼容性矩阵

| 数据库版本 | v2.5.x 代码 | v2.6.0 代码 |
|------------|-------------|-------------|
| v2.5.x 数据库 | ✓ 兼容 | ⚠️ 自动迁移 |
| v2.6.0 数据库 | ✗ 不兼容 | ✓ 兼容 |

---

## 故障排查

### 错误：`no such column: llm_config_name`

**原因**：旧版数据库 `models` 表缺少新字段

**解决**：
1. 重启服务，自动迁移会重建 `models` 表
2. 如果仍失败，手动删除数据库文件后重启

### 错误：`database is locked`

**原因**：多个进程同时访问数据库

**解决**：
1. 确保只有一个服务实例在运行
2. 重启 Docker 容器

### 错误：`UNIQUE constraint failed`

**原因**：迁移过程中数据冲突

**解决**：
1. 备份现有数据库
2. 删除数据库文件
3. 重启服务创建新数据库
