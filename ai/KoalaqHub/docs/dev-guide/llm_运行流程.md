# LLM 运行流程

本文档描述 KoalaQ Hub 中 LLM（大语言模型）系统的配置、构建和使用流程。

> 关联文档：[Agent 运行流程](./agent_运行流程.md)、[数据库架构](./database_数据库架构.md)、[Token 管理](./token_Token管理.md)

## 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         配置层（启动时）                              │
├─────────────────────────────────────────────────────────────────────┤
│  llm_config.ini ──→ LLMBuilder ──→ LLMManager ──→ 数据库            │
│                    (读取ini)      (save_to_database)                │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         数据层（持久化）                              │
├─────────────────────────────────────────────────────────────────────┤
│  models 表                                                          │
│  ├─ llm_id (UUID主键)                                               │
│  ├─ llm_config_name (唯一约束，ini section名)                        │
│  ├─ 连接信息: api_key, url, platform, model                         │
│  ├─ 参数配置: temperature, top_p, max_tokens, description           │
│  └─ Token统计: total_tokens, prompt_tokens, completion_tokens...    │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         运行时（实时读取）                            │
├─────────────────────────────────────────────────────────────────────┤
│  AgentRegistry ──→ LLMManager.get_llm() ──→ 数据库查询 ──→ LLM对象  │
│                   (无缓存，实时读取)                                  │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         客户端层                                     │
├─────────────────────────────────────────────────────────────────────┤
│  EnhancedLLMClient                                                  │
│  ├─ block()    → 阻塞式请求，返回完整结果                            │
│  ├─ stream()   → 流式请求（WebSocket / SSE）                        │
│  └─ 支持 Function Calling                                           │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         集成层                                       │
├─────────────────────────────────────────────────────────────────────┤
│  Agent.main_llm / Agent.think_llm / Agent.summary_llm               │
│                              ↓                                      │
│  ChatProcessor → EnhancedLLMClient → OpenAI API                     │
│                              ↓                                      │
│  TokenManager → repository_adapter → models表（Token累加）          │
└─────────────────────────────────────────────────────────────────────┘
```

## 一、配置文件 (llm_config.ini)

### 文件位置
```
koalaq_hub_python/resource/config/llm_config.ini
```

### 配置格式

每个 LLM 配置是一个独立的 section，section 名称即为 `llm_config_name`（数据库唯一标识）：

```ini
[deepseek-chat]
# 连接配置（入库字段）
api_key = sk-xxxxxxxxxxxxxxxx
url = https://api.deepseek.com
model = deepseek-chat
platform = deepseek

# 生成参数（入库字段）
temperature = 0.7
top_p = 0.9
max_tokens = 8192
description = DeepSeek AI 模型

# 运行时参数（不入库，使用全局配置或默认值）
timeout = 120
think = true
think_max_tokens = 1024
```

### 配置项说明

| 配置项 | 类型 | 必填 | 入库 | 默认值 | 说明 |
|--------|------|------|------|--------|------|
| `api_key` | str | 是 | 是 | - | API 密钥 |
| `url` | str | 是 | 是 | - | API 基础 URL |
| `model` | str | 是 | 是 | - | 模型名称 |
| `platform` | str | 是 | 是 | - | 平台标识（用于特殊处理） |
| `temperature` | float | 否 | 是 | 0.7 | 温度参数，控制随机性 |
| `top_p` | float | 否 | 是 | 1.0 | 核采样参数 |
| `max_tokens` | int | 否 | 是 | 4096 | 最大生成 token 数 |
| `description` | str | 否 | 是 | "" | 模型描述 |
| `timeout` | float | 否 | 否 | .env配置 | 请求超时（使用全局LLM_TIMEOUT） |
| `think` | bool | 否 | 否 | false | 是否支持思维链（运行时配置） |
| `think_max_tokens` | int | 否 | 否 | 0 | 思维链最大 token 数 |

### 支持的平台

| 平台 | platform 值 | 特殊处理 |
|------|-------------|----------|
| DeepSeek | `deepseek` | 支持 reasoning_content |
| 通义千问 | `tongyi` | 需要 stream_options.include_usage |
| SiliconFlow | `siliconflow` | 标准 OpenAI 格式 |
| Moonshot (Kimi) | `moonshot` | usage 在 choice 中 |

## 二、数据库表结构 (models)

### 表定义

```sql
CREATE TABLE IF NOT EXISTS models (
    -- 主键和标识
    llm_id TEXT PRIMARY KEY,              -- UUID (取后8位)
    llm_config_name TEXT UNIQUE NOT NULL, -- ini section 名，唯一约束

    -- 连接配置
    platform TEXT NOT NULL,               -- 平台标识
    model TEXT NOT NULL,                  -- 模型名称
    api_key TEXT,                         -- API 密钥
    url TEXT,                             -- API URL

    -- 生成参数
    temperature REAL DEFAULT 0.7,
    top_p REAL DEFAULT 1.0,
    max_tokens INTEGER DEFAULT 4096,
    description TEXT DEFAULT '',

    -- Token 统计
    total_tokens INTEGER DEFAULT 0,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    reasoning_tokens INTEGER DEFAULT 0,

    -- 请求统计
    request_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    avg_response_time REAL DEFAULT 0,

    -- 时间戳
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
```

### 字段说明

| 字段 | 类型 | 来源 | 说明 |
|------|------|------|------|
| `llm_id` | TEXT | 自动生成 | UUID 后8位，主键 |
| `llm_config_name` | TEXT | ini section | 配置名，唯一标识，用于查询 |
| `platform` | TEXT | ini | 平台标识 |
| `model` | TEXT | ini | 模型名称 |
| `api_key` | TEXT | ini | API 密钥 |
| `url` | TEXT | ini | API URL |
| `temperature` | REAL | ini | 温度参数 |
| `top_p` | REAL | ini | 核采样参数 |
| `max_tokens` | INTEGER | ini | 最大 token 数 |
| `description` | TEXT | ini | 描述信息 |
| `total_tokens` | INTEGER | 运行时累加 | 累计总 token |
| `prompt_tokens` | INTEGER | 运行时累加 | 累计输入 token |
| `completion_tokens` | INTEGER | 运行时累加 | 累计输出 token |
| `reasoning_tokens` | INTEGER | 运行时累加 | 累计推理 token |

## 三、LLM 数据模型

### 文件位置
```
koalaq_hub/models/llm.py
```

### 类定义

```python
@dataclass
class LLM:
    """LLM 模型配置实例"""

    # 数据库字段
    llm_id: str              # UUID 唯一标识
    llm_config_name: str     # ini section 名（数据库查询键）
    api_key: str             # API 密钥
    url: str                 # API URL
    model: str               # 模型名称
    platform: str            # 平台名称
    temperature: float = 0.7
    top_p: float = 1.0
    max_tokens: int = 4096
    description: str = ""

    # 运行时字段（不入库）
    timeout: float = field(default_factory=lambda: config.llm_timeout)
    think: bool = False
    think_max_tokens: int = 0
```

### 核心方法

```python
def to_llm_config(self) -> Dict[str, Any]:
    """转换为 LLMClient 需要的配置格式"""
    return {
        "api_key": self.api_key,
        "url": self.url,
        "model": self.model,
        "platform": self.platform,
        "temperature": self.temperature,
        "timeout": self.timeout,
        # ...
    }
```

## 四、LLMBuilder 构建器

### 文件位置
```
koalaq_hub/config/llm_builder.py
```

### 职责
- 从 `llm_config.ini` 读取配置到内存
- 调用 `LLMManager.create_if_not_exists()` 保存到数据库
- **不再提供运行时 LLM 获取功能**（由 LLMManager 负责）

### 类定义

```python
class LLMBuilder:
    """LLM 构建器 - 读取 ini 配置并保存到数据库"""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = project_root / "resource" / "config" / "llm_config.ini"
        self._ini_configs: Dict[str, Dict[str, Any]] = {}  # 原始 ini 数据
        self._load_ini_configs()

    def _load_ini_configs(self):
        """从配置文件加载所有配置到内存（仅原始数据）"""
        config_parser = configparser.ConfigParser()
        config_parser.read(self.config_path, encoding="utf-8")

        for section_name in config_parser.sections():
            self._ini_configs[section_name] = {
                "llm_config_name": section_name,
                "platform": section.get("platform", section_name),
                "model": section.get("model", ""),
                "api_key": section.get("api_key", ""),
                "url": section.get("url", ""),
                "temperature": section.getfloat("temperature", 0.7),
                "top_p": section.getfloat("top_p", 1.0),
                "max_tokens": section.getint("max_tokens", 4096),
                "description": section.get("description", ""),
            }

    def save_to_database(self, llm_manager: LLMManager) -> int:
        """将 ini 配置保存到数据库（如果不存在）"""
        saved_count = 0
        for config_name, config_data in self._ini_configs.items():
            llm_manager.create_if_not_exists(**config_data)
            saved_count += 1
        return saved_count

    def get_ini_config(self, config_name: str) -> Optional[Dict]:
        """获取原始 ini 配置（仅用于启动验证）"""
        return self._ini_configs.get(config_name)

    def get_ini_configs(self) -> Dict[str, Dict]:
        """获取所有 ini 配置"""
        return self._ini_configs.copy()

# 全局单例
llm_builder = LLMBuilder()
```

## 五、LLMManager 管理器

### 文件位置
```
koalaq_hub/core/llm_manager.py
```

### 职责
- 从数据库实时读取 LLM 配置（**无缓存**）
- 创建、更新、删除 LLM 配置
- 运行时 LLM 获取的唯一入口

### 类定义

```python
class LLMManager:
    """LLM 管理器 - 无缓存，实时从数据库读取"""

    def __init__(self, repository_adapter: RepositoryAdapter):
        self.repository = repository_adapter

    # ==================== 查询方法（实时读库） ====================

    def get_llm_by_name(self, llm_config_name: str) -> Optional[LLM]:
        """根据配置名称获取 LLM（从数据库实时读取）"""
        model_data = self.repository.get_llm_config_by_name(llm_config_name)
        return self._model_to_llm(model_data)

    def get_llm_by_id(self, llm_id: str) -> Optional[LLM]:
        """根据 ID 获取 LLM"""
        model_data = self.repository.get_llm_config_by_id(llm_id)
        return self._model_to_llm(model_data)

    def list_all(self) -> List[LLM]:
        """获取所有 LLM 配置"""
        model_list = self.repository.list_llm_configs()
        return [self._model_to_llm(m) for m in model_list if m]

    # ==================== 创建方法 ====================

    def create_if_not_exists(self, llm_config_name: str, **kwargs) -> str:
        """创建 LLM 配置（如果不存在）"""
        return self.repository.create_llm_config_if_not_exists(
            llm_config_name=llm_config_name, **kwargs
        )

    # ==================== 兼容方法 ====================

    def get_llm(self, llm_config_name: str) -> Optional[LLM]:
        """获取 LLM（兼容旧 API）"""
        return self.get_llm_by_name(llm_config_name)
```

### 为什么无缓存？

1. **配置可能被外部修改**：通过 API 或数据库直接修改
2. **实时性要求**：确保获取的是最新配置
3. **简化架构**：避免缓存失效问题
4. **性能影响小**：LLM 获取不是高频操作

## 六、LLMRepository 仓库

### 文件位置
```
koalaq_hub/database/repositories/llm_repository.py
```

### 职责
- LLM 配置的 CRUD 操作
- UUID 生成（取后8位）
- 数据库访问封装

### 核心方法

```python
class LLMRepository(BaseRepository):
    """LLM 配置仓库"""

    def create_llm(self, llm_config_name: str, platform: str, model: str,
                   api_key: str = None, url: str = None, ...) -> str:
        """创建 LLM 配置，返回 llm_id"""
        llm_id = uuid.uuid4().hex[-8:]  # UUID 后8位
        sql = """
            INSERT INTO models (llm_id, llm_config_name, platform, model,
                               api_key, url, temperature, top_p, max_tokens,
                               description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        # ...
        return llm_id

    def create_if_not_exists(self, llm_config_name: str, ...) -> str:
        """创建或获取已存在的 LLM 配置"""
        existing = self.get_by_config_name(llm_config_name)
        if existing:
            return existing.llm_id
        return self.create_llm(llm_config_name, ...)

    def get_by_config_name(self, llm_config_name: str) -> Optional[Model]:
        """根据配置名查询"""
        sql = "SELECT * FROM models WHERE llm_config_name = ?"
        # ...

    def get_by_id(self, llm_id: str) -> Optional[Model]:
        """根据 ID 查询"""
        sql = "SELECT * FROM models WHERE llm_id = ?"
        # ...
```

## 七、启动初始化流程

### __main__.py 中的初始化

```python
async def initialize_services():
    # 1. 创建数据库存储
    db_storage = RepositoryAdapter(str(db_path))

    # 2. 创建 LLM 管理器
    llm_manager = LLMManager(db_storage)

    # 3. 将 ini 配置保存到数据库
    saved_count = llm_builder.save_to_database(llm_manager)
    # 输出: "LLM 配置保存完成，共 5 个"

    # 4. 创建 Agent 注册表（注入 llm_manager）
    agent_registry = AgentRegistry(
        tool_manager=tool_manager,
        repository_adapter=db_storage,
        llm_manager=llm_manager,  # 关键：注入 LLMManager
        cache_timeout_minutes=config.agent_cache_timeout_minutes
    )

    # ...
```

### 完整初始化流程图

```
应用启动 (__main__.py)
    │
    ├─→ LLMBuilder 单例初始化（模块加载时）
    │   └─→ _load_ini_configs() 从 llm_config.ini 加载
    │   └─→ self._ini_configs: Dict[str, Dict] (原始数据)
    │
    ├─→ validate_and_print_config()
    │   └─→ llm_builder.get_ini_config(app.llm_use) 验证配置存在
    │   └─→ 检查 api_key 是否有效
    │
    ├─→ initialize_services()
    │   ├─→ RepositoryAdapter 初始化
    │   │   └─→ DatabaseConnection 创建表结构
    │   │
    │   ├─→ LLMManager(db_storage) 创建
    │   │
    │   ├─→ llm_builder.save_to_database(llm_manager)
    │   │   └─→ 遍历 _ini_configs:
    │   │       └─→ llm_manager.create_if_not_exists(...)
    │   │           └─→ LLMRepository.create_if_not_exists(...)
    │   │               └─→ INSERT OR 获取已存在记录
    │   │
    │   └─→ AgentRegistry(llm_manager=llm_manager)
    │
    └─→ FastAPI 服务器启动
```

## 八、运行时 Agent 创建流程

### AgentRegistry 中获取 LLM

```python
class AgentRegistry:
    def __init__(self, ..., llm_manager: Optional[LLMManager] = None, ...):
        self.llm_manager = llm_manager

    def _create_agent(self, agent_id: str, config: AgentConfig) -> Optional[Agent]:
        # 从数据库获取主 LLM
        main_llm = None
        if config.llm_use:
            main_llm = self.llm_manager.get_llm(config.llm_use)
            # ↑ 调用 LLMManager.get_llm_by_name()
            # ↑ 从数据库实时读取
            if not main_llm:
                self.logger.error(f"找不到 LLM 配置: {config.llm_use}")
                return None

        # 从数据库获取思考 LLM
        think_llm = None
        if config.enable_thinking and config.llm_think_use:
            think_llm = self.llm_manager.get_llm(config.llm_think_use)

        # 从数据库获取总结 LLM
        summary_llm = None
        if config.enable_summary and config.summary_llm_use:
            summary_llm = self.llm_manager.get_llm(config.summary_llm_use)

        # 创建 Agent 实例
        agent = Agent(
            agent_id=agent_id,
            main_llm=main_llm,
            think_llm=think_llm,
            summary_llm=summary_llm,
            # ...
        )
        return agent
```

### 数据流图

```
agent.ini                      数据库 models 表
    │                                │
    │ llm_use = deepseek-chat        │ llm_config_name = deepseek-chat
    │                                │ api_key = sk-xxx
    ↓                                │ url = https://...
AgentConfig.llm_use ─────────────────┼─────────────────────────────────→
                                     │
                     LLMManager.get_llm("deepseek-chat")
                                     │
                                     ↓
                              LLMRepository.get_by_config_name()
                                     │
                                     ↓
                              SELECT * FROM models
                              WHERE llm_config_name = ?
                                     │
                                     ↓
                              Model → LLM dataclass
                                     │
                                     ↓
                              Agent.main_llm = LLM(...)
```

## 九、Token 统计流程

### 调用链

```
ChatProcessor 处理完成
    │
    ↓
HistoryManager.add_assistant_message(agent, token_usage)
    │
    ↓
TokenManager.add_tokens(llm=agent.get_llm_for_mode(), token_usage=...)
    │
    ↓
TokenManager.add_tokens_to_model()
    │
    │  llm_config_name = llm.llm_config_name  ← 从 LLM 对象获取
    │
    ↓
repository_adapter.add_tokens_to_model(llm_config_name, token_usage)
    │
    ↓
TokenRepository.add_tokens_by_config_name(llm_config_name, ...)
    │
    ↓
UPDATE models SET
    total_tokens = total_tokens + ?,
    prompt_tokens = prompt_tokens + ?,
    ...
WHERE llm_config_name = ?
```

### 关键代码

```python
# token_manager.py
def add_tokens_to_model(self, token_usage: TokenUsage, llm: Optional[LLM] = None, ...):
    if llm:
        llm_config_name = llm.llm_config_name  # 使用配置名作为索引
        platform = llm.platform
        model = llm.model
    else:
        llm_config_name = "unknown"

    # 累加到模型统计（使用 llm_config_name 作为索引）
    self.repository_adapter.add_tokens_to_model(llm_config_name, token_usage)
```

## 十、EnhancedLLMClient 客户端

### 文件位置
```
koalaq_hub/core/llm/enhanced_llm_client.py
```

### 职责
- 封装 OpenAI API 调用
- 支持多种输出模式（阻塞/WebSocket/SSE）
- 处理 Function Calling
- 处理思维链内容
- Token 统计

### 创建方式

```python
# 从 Agent 创建（推荐）
client = EnhancedLLMClient.create_from_agent(agent)
# 自动根据 agent.use_think_llm 选择 main_llm 或 think_llm

# 直接从 LLM 对象创建
client = EnhancedLLMClient(llm=llm)
```

### 请求方式

```python
# 阻塞式请求
response = await client.block(
    messages=messages,
    conversation_id="conv_123",
    tools=tool_list
)

# WebSocket 流式请求
response = await client.stream(
    messages=messages,
    conversation_id="conv_123",
    output_type=OutputType.WEBSOCKET,
    websocket_handler=websocket_handler
)
```

### 响应数据结构

```python
@dataclass
class LLMResponse:
    content: str                    # 生成的文本内容
    reasoning_content: str = ""     # 思维链内容
    token_usage: TokenUsage = None  # Token 使用统计
    is_interrupted: bool = False    # 是否被中断
    tool_calls: List[ToolCall] = [] # Function Calling 工具调用

@dataclass
class TokenUsage:
    total_tokens: int
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
```

## 十一、完整调用流程

```
1. 应用启动
   ├─→ LLMBuilder._load_ini_configs()
   │   └─→ 从 llm_config.ini 加载原始配置
   │
   ├─→ LLMManager 创建
   │
   ├─→ llm_builder.save_to_database(llm_manager)
   │   └─→ 遍历 ini 配置
   │   └─→ create_if_not_exists() 保存到数据库
   │
   └─→ AgentRegistry(llm_manager=llm_manager)

2. 创建 Agent 时
   └─→ AgentRegistry._create_agent()
       └─→ llm_manager.get_llm(config.llm_use)
           └─→ 从数据库实时读取
       └─→ Agent.main_llm = llm

3. 处理用户消息时
   └─→ ChatProcessor.process_message()
       └─→ EnhancedLLMClient.create_from_agent(agent)
           └─→ agent.get_llm_for_mode()
       └─→ client.stream() / client.block()
           └─→ OpenAI API 调用
       └─→ 返回 LLMResponse

4. Token 统计
   └─→ TokenManager.add_tokens(llm=agent.get_llm_for_mode(), ...)
       └─→ llm_config_name = llm.llm_config_name
       └─→ repository_adapter.add_tokens_to_model(llm_config_name, token_usage)
           └─→ UPDATE models ... WHERE llm_config_name = ?
```

## 十二、文件位置索引

| 文件 | 路径 | 说明 |
|------|------|------|
| LLM 配置 | `resource/config/llm_config.ini` | INI 格式配置文件 |
| LLM 模型 | `koalaq_hub/models/llm.py` | LLM dataclass 定义 |
| LLM 构建器 | `koalaq_hub/config/llm_builder.py` | ini 读取和初始化保存 |
| LLM 管理器 | `koalaq_hub/core/llm_manager.py` | 运行时 LLM 获取（从数据库） |
| LLM 仓库 | `koalaq_hub/database/repositories/llm_repository.py` | LLM 配置 CRUD |
| Token 仓库 | `koalaq_hub/database/repositories/token_repository.py` | Token 统计累加 |
| LLM 客户端 | `koalaq_hub/core/llm/enhanced_llm_client.py` | API 调用封装 |
| Token 管理器 | `koalaq_hub/core/token_manager.py` | Token 统计入口 |
| 启动入口 | `koalaq_hub/__main__.py` | 初始化流程 |
| 数据库表定义 | `koalaq_hub/database/base/database_connection.py` | models 表 DDL |

## 十三、常见问题

### Q: 如何切换不同的 LLM？

修改 `agent.ini` 中的 `llm_use` 配置即可：

```ini
[my-agent]
llm_use = tongyi-max  # 改为其他已配置的 LLM
```

### Q: 如何添加新的 LLM 配置？

1. 在 `llm_config.ini` 添加配置
2. 重启应用，配置会自动保存到数据库
3. 如果平台有特殊 API 格式，在 `EnhancedLLMClient._build_api_params()` 中添加处理逻辑

### Q: 修改数据库中的 LLM 配置会生效吗？

会。因为 LLMManager 是无缓存设计，每次 `get_llm()` 都从数据库实时读取。

### Q: ini 配置和数据库配置冲突怎么办？

启动时使用 `INSERT OR IGNORE`，**数据库已存在的配置不会被覆盖**。如需更新，请直接修改数据库或删除记录后重启。

### Q: timeout 配置在哪里？

timeout 不入库，使用全局配置：
- `.env` 文件：`LLM_TIMEOUT=120.0`
- `settings.py`：`self.llm_timeout = float(os.getenv("LLM_TIMEOUT", "120.0"))`

### Q: 如何通过 API 修改 LLM 配置？

通过 `LLMManager` 提供的方法：

```python
# 更新配置
llm_manager.update_llm(llm_id, temperature=0.8, max_tokens=8192)

# 删除配置
llm_manager.delete_llm(llm_id)

# 创建新配置
llm_manager.create_llm(
    llm_config_name="new-llm",
    platform="openai",
    model="gpt-4",
    api_key="sk-xxx",
    url="https://api.openai.com/v1"
)
```
