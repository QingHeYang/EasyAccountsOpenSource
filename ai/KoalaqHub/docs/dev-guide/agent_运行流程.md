# Agent 运行流程

本文档描述 KoalaQ Hub 中 Agent 系统的架构设计和运行流程。

## 类体系架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        配置层                                    │
├─────────────────────────────────────────────────────────────────┤
│  agent.ini ──→ AgentBuilder ──→ AgentConfig                     │
│  llm_config.ini ──→ LLMBuilder ──→ LLM                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      注册表层                                    │
├─────────────────────────────────────────────────────────────────┤
│  AgentRegistry                                                  │
│  ├─ _configs: Dict[str, AgentConfig]  # 配置缓存               │
│  ├─ create_agent_from_config()        # 创建 Agent 实例        │
│  ├─ build_sub_agent()                 # 创建子Agent            │
│  ├─ build_tools_list()                # 构建工具列表           │
│  └─ build_system_prompt()             # 构建系统提示词         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      实例层                                      │
├─────────────────────────────────────────────────────────────────┤
│  Agent (dataclass)                                              │
│  ├─ 基础信息: agent_id, name, description                       │
│  ├─ LLM对象: main_llm, think_llm, summary_llm                  │
│  ├─ 工具配置: tool_list, mcp_servers                           │
│  ├─ 系统提示词: system_prompt                                   │
│  └─ 运行时状态: is_active, usage_count                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      执行层                                      │
├─────────────────────────────────────────────────────────────────┤
│  AgentExecutor                                                  │
│  ├─ execute(agent, message, source)                             │
│  │     ├─ source="http"      → HttpChatProcessor               │
│  │     ├─ source="websocket" → WebSocketChatProcessor          │
│  │     └─ source="internal"  → InternalChatProcessor           │
│  └─ sub_agent_executor       → 子Agent调用                      │
└─────────────────────────────────────────────────────────────────┘
```

## 核心类说明

### 1. 配置层

#### AgentConfig (`config/agent_builder.py`)
- **职责**: 从 `agent.ini` 读取的静态配置
- **生命周期**: 应用启动时加载，运行期间不变
- **主要属性**:
  - `agent_id`: Agent 唯一标识
  - `name`, `description`: 基本信息
  - `llm_use`, `llm_think_use`, `summary_llm_use`: LLM 配置引用
  - `mcp_servers`: MCP 服务器列表
  - `role_file`: 角色配置文件
  - `agent_list`: 可调用的子 Agent 列表

#### LLM (`models/llm.py`)
- **职责**: LLM 模型配置对象
- **来源**: 由 `LLMBuilder` 从 `llm_config.ini` 加载
- **主要属性**: `api_key`, `url`, `model`, `temperature`, `max_tokens` 等

### 2. 注册表层

#### AgentRegistry (`core/agents/agent_registry.py`)
- **职责**: 管理 Agent 配置缓存，创建 Agent 实例
- **设计模式**: 工厂模式 + 注册表模式
- **核心方法**:

```python
# 初始化时缓存所有配置
async def initialize(self):
    all_agent_configs = agent_builder.get_all_agents()
    for agent_id, config in all_agent_configs.items():
        self._configs[agent_id] = config

# 创建 Agent 实例
def create_agent_from_config(self, agent_id: str) -> Optional[Agent]:
    config = self.get_agent_config(agent_id)
    main_llm = llm_builder.get_llm(config.llm_use)
    # ... 创建 Agent 实例

# 构建系统提示词和工具列表
def build_system_prompt(self, agent: Agent, user_id: str, conversation_id: str) -> str:
    self.build_tools_list(agent)  # 先构建工具列表
    return self.system_prompt_assembler.assemble(agent, user_id, conversation_id)
```

### 3. 实例层

#### Agent (`models/agent.py`)
- **职责**: 运行时 Agent 实例，包含完整的执行上下文
- **设计**: 使用 `@dataclass` 定义
- **主要属性分类**:

| 类别 | 属性 | 说明 |
|------|------|------|
| 基础信息 | `agent_id`, `name`, `description` | 标识和描述 |
| LLM 对象 | `main_llm`, `think_llm`, `summary_llm` | LLM 实例引用 |
| 配置值 | `llm_memory_window`, `tool_round` | 从 AgentConfig 复制 |
| 工具相关 | `tool_list`, `mcp_servers` | Function Calling 工具 |
| 提示词 | `system_prompt`, `role_context` | 运行时组装 |
| 运行状态 | `is_active`, `usage_count`, `last_used_at` | 统计信息 |

### 4. 执行层

#### AgentExecutor (`core/agents/agent_executor.py`)
- **职责**: 统一的 Agent 执行入口
- **依赖注入**: 接收所有必要的管理器实例
- **执行路由**: 根据 `source` 参数选择处理器

```python
async def execute(self, agent, message, conversation_id, user_id, source="internal"):
    if source == "http":
        return await self.http_processor.process_message(...)
    elif source == "websocket":
        return await self.websocket_processor.process_message(...)
    elif source == "internal":
        return await internal_processor.process_message(...)
```

## 运行流程

### 1. 应用启动

```
__main__.py
    │
    ├─→ llm_builder 加载 LLM 配置
    │
    ├─→ agent_builder 加载 Agent 配置
    │
    ├─→ ServerManager 初始化 MCP 服务器
    │
    ├─→ AgentRegistry 初始化
    │       └─→ 缓存所有 AgentConfig
    │
    └─→ AgentExecutor 初始化
            ├─→ 创建 ToolManager
            ├─→ 创建 HistoryManager
            ├─→ 创建 SubAgentExecutor
            └─→ 创建 ChatProcessor 实例
```

### 2. 用户请求处理

```
API/WebSocket 请求到达
    │
    ├─→ 获取 user_id, agent_id, message
    │
    ├─→ AgentRegistry.get_or_create_user_agent(user_id, agent_id)
    │       │
    │       └─→ create_agent_from_config(agent_id)
    │               ├─→ 获取 AgentConfig
    │               ├─→ 从 llm_builder 获取 LLM 对象
    │               ├─→ 创建 Agent 实例
    │               └─→ 构建子 Agent 提示词
    │
    ├─→ AgentRegistry.build_system_prompt(agent, user_id, conversation_id)
    │       ├─→ build_tools_list(agent)  # 构建 Function Calling 工具
    │       └─→ system_prompt_assembler.assemble()  # 组装系统提示词
    │
    └─→ AgentExecutor.execute(agent, message, source)
            │
            └─→ ChatProcessor.process_message()
                    ├─→ 构建消息历史
                    ├─→ 调用 LLM
                    ├─→ 处理工具调用（如有）
                    └─→ 返回响应
```

### 3. 子 Agent 调用流程

```
主 Agent 执行中识别到需要调用子 Agent (call_agent 工具)
    │
    ├─→ SubAgentExecutor.execute_sub_agent(agent_id, task)
    │       │
    │       ├─→ 创建子会话 (parent_conversation_id 关联父会话)
    │       │
    │       └─→ AgentRegistry.build_sub_agent(agent_id)
    │               ├─→ 获取原始 AgentConfig
    │               ├─→ 创建简化的 Agent 实例
    │               │       ├─→ agent_id = "sub_{原始agent_id}"
    │               │       ├─→ agent_list = []  # 禁止递归调用
    │               │       ├─→ tool_round = min(原始值, 3)  # 限制轮次
    │               │       ├─→ enable_summary = False
    │               │       ├─→ enable_thinking = False
    │               │       ├─→ sub_agent_mode = True
    │               │       └─→ 复制: role_file, role_context, task_instructions_file, inner_tools
    │               │
    │               └─→ AgentToolBinder.build_tools_list(sub_agent)
    │                       └─→ 绑定 inner_tools (不绑定 call_agent)
    │
    ├─→ AgentRegistry.build_system_prompt(sub_agent, user_id, sub_conversation_id)
    │       │
    │       └─→ SystemPromptAssembler.assemble()  # 与主Agent相同的组装器
    │               ├─→ _load_task_layer()     # 加载相同的任务指导
    │               ├─→ _build_role_layer()    # 使用相同的角色定义
    │               └─→ _build_context_layer() # 从子会话获取上下文(通常为空)
    │
    └─→ AgentExecutor.execute(sub_agent, task, source="internal")
            │
            └─→ InternalChatProcessor.process_message()
                    ├─→ 使用子会话的历史记录
                    ├─→ 执行工具调用（受 tool_round 限制）
                    └─→ 返回结果给主 Agent
```

#### 子 Agent 关键特性

| 特性 | 主 Agent | 子 Agent | 说明 |
|------|----------|----------|------|
| agent_id | 原始ID | `sub_{原始ID}` | 区分实例 |
| agent_list | 配置的列表 | `[]` 空列表 | 防止递归调用 |
| tool_round | 配置值 | `min(配置值, 3)` | 限制工具轮次 |
| enable_summary | 配置值 | `False` | 禁用总结 |
| enable_thinking | 配置值 | `False` | 禁用思考 |
| inner_tools | 配置值 | 相同 | 保留内部工具 |
| mcp_servers | 配置值 | 相同 | 保留MCP工具 |
| task_instructions_file | 配置值 | 相同 | 使用相同任务指导 |
| role_file/role_context | 配置值 | 相同 | 使用相同角色定义 |
| system_prompt | 动态组装 | 动态组装 | 使用相同组装器 |

## 关键设计决策

### 1. 不缓存 Agent 实例
- **原因**: 每个请求的上下文不同，缓存实例会导致状态混乱
- **实现**: `get_or_create_user_agent()` 每次都创建新实例
- **好处**: 简化状态管理，避免并发问题

### 2. 配置与实例分离
- **AgentConfig**: 静态配置，可安全缓存
- **Agent**: 运行时实例，包含动态状态
- **好处**: 配置变更时只需重载 AgentConfig

### 3. 处理器复用
- **HttpChatProcessor**: 可复用，每次清空 `http_content`
- **WebSocketChatProcessor**: 可复用，状态在 `websocket_handler` 中
- **InternalChatProcessor**: 每次创建，因为需要特定的 `parent_conversation_id`

## 文件位置索引

| 文件 | 路径 | 说明 |
|------|------|------|
| Agent 模型 | `koalaq_hub/models/agent.py` | Agent 数据类定义 |
| Agent 注册表 | `koalaq_hub/core/agents/agent_registry.py` | 配置管理和实例创建 |
| Agent 执行器 | `koalaq_hub/core/agents/agent_executor.py` | 执行入口和处理器管理 |
| Agent 配置构建器 | `koalaq_hub/config/agent_builder.py` | 从 ini 加载配置 |
| LLM 构建器 | `koalaq_hub/config/llm_builder.py` | 从 ini 加载 LLM 配置 |
| 子 Agent 执行器 | `koalaq_hub/core/executor/sub_agent_executor.py` | 子 Agent 调用逻辑 |
