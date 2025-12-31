# 消息管理文档

> 版本: 1.1
> 更新时间: 2025-12-31
> 状态: 正式版

## 一、概述

消息管理是 Agent 运行的核心基础，负责：

1. **消息保存**：将用户输入、AI回复、工具调用等持久化到数据库
2. **历史构建**：为 LLM 构建符合 Function Calling 格式的对话历史
3. **实时推送**：通过 WebSocket 向前端推送流式响应
4. **前端查询**：提供 REST API 供前端分页查询历史消息

> **关联文档**：
> - [WebSocket 运行流程](./websocket_运行流程.md) - 实时消息推送
> - [Agent 运行流程](./agent_运行流程.md) - Agent 执行流程
> - [数据库架构](./database_数据库架构.md) - 消息表结构
> - [VL 运行流程](./VL_运行流程.md) - 图片附件处理

---

## 二、消息数据流

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           消息数据流                                      │
└──────────────────────────────────────────────────────────────────────────┘

用户输入
    │
    ▼
┌─────────────────┐    实时推送    ┌─────────────────┐
│  WebSocket 端点  │ ◄───────────► │   前端客户端     │
└────────┬────────┘                └─────────────────┘
         │                                   ▲
         ▼                                   │ REST API 查询
┌─────────────────┐                ┌─────────┴─────────┐
│ AgentExecutor   │                │ conversations.py  │
│ ChatProcessor   │                │ (分页查询端点)     │
└────────┬────────┘                └─────────┬─────────┘
         │                                   │
         ▼                                   │
┌─────────────────┐                ┌─────────▼─────────┐
│ HistoryManager  │                │ConversationManager│
├─────────────────┤                ├───────────────────┤
│ ① 内存缓存      │◄──────────────►│ 查询 + 格式转换   │
│ ② 持久化存储    │                └───────────────────┘
│ ③ 历史构建      │                          │
└────────┬────────┘                          │
         │                                   │
         ▼                                   ▼
┌─────────────────────────────────────────────────────┐
│              RepositoryAdapter (数据库)              │
│  ├─ messages 表：所有消息                            │
│  ├─ rounds 表：轮次信息                              │
│  └─ conversations 表：对话元数据                     │
└─────────────────────────────────────────────────────┘
```

---

## 三、Message 模型

### 3.1 消息类型 (MessageType)

**文件**: `models/message.py`

| 类型 | 值 | 说明 | role |
|------|-----|------|------|
| CONTENT | `content` | 普通文本消息 | user / assistant |
| TOOL_CALL | `tool_call` | 工具调用请求 | assistant |
| TOOL_RESULT | `tool_result` | 工具执行结果 | tool |
| ERROR | `error` | 错误消息 | error |
| AGENT_START | `agent_start` | 子Agent开始执行 | assistant |
| AGENT_END | `agent_end` | 子Agent执行结束 | tool |

### 3.2 Message 数据类

```python
@dataclass
class Message:
    # 基础字段
    role: str                    # user / assistant / tool / error
    content: str                 # 消息内容
    timestamp: str               # 时间戳 (YYYY-MM-DD HH:MM:SS)
    round_id: str                # 轮次ID
    type: MessageType            # 消息类型

    # 工具调用相关
    tool_success: bool = False   # 工具是否执行成功
    tool_call_ids: str = ""      # 工具调用ID (多个用 | 分隔)
    tool_call_raw: str = ""      # tool_calls 原始 JSON
    tool_name: str = None        # 工具名称 (TOOL_RESULT 用)

    # 思维链
    reasoning_content: str = ""  # 推理内容 (仅存数据库，不进历史)

    # 子Agent相关
    agent_id: str = None         # 子Agent ID
    sub_conversation_id: str = None  # 子会话ID (AGENT_END 用)

    # VL 附件 (图片等)
    attachments: List[Attachment] = None  # 附件列表 [{filename, data, media_type}]

    # 数据库相关
    message_id: int = None       # 数据库自增ID
    total_tokens: int = None     # Token数
    model: str = None            # 模型名称
```

> **VL 支持**: 详见 [VL 运行流程](./VL_运行流程.md)

### 3.3 消息创建工厂方法

| 方法 | 用途 | 返回类型 |
|------|------|----------|
| `create_user_message(content, round_id, attachments)` | 用户输入 | CONTENT |
| `create_assistant_message(content, round_id, tool_calls)` | AI回复/工具调用 | CONTENT / TOOL_CALL / AGENT_START |
| `create_tool_message(tool_call_id, result, round_id, success, tool_name)` | 工具结果 | TOOL_RESULT |
| `create_error_message(error_message, round_id)` | 错误信息 | ERROR |
| `create_sub_agent_message(content, round_id, agent_id, sub_conversation_id, tool_call_id)` | 子Agent结果 | AGENT_END |

---

## 四、HistoryManager - 核心消息管理器

**文件**: `core/history_manager.py`

### 4.1 职责

1. **内存缓存**：维护当前活跃对话的消息（按 memory_window 限制）
2. **持久化**：将消息写入数据库
3. **历史构建**：为 LLM 构建 Function Calling 格式的对话历史
4. **轮次管理**：创建轮次、滚动窗口、轮次结束处理

### 4.2 数据结构

```python
class HistoryManager:
    # 多用户多会话的内存缓存
    histories: Dict[str, Dict[str, Dict]] = {
        "user_id_1": {
            "conversation_id_1": {
                "rounds": {
                    "round_id_1": [Message, Message, ...],
                    "round_id_2": [Message, Message, ...],
                }
            },
            "conversation_id_2": {...}
        },
        "user_id_2": {...}
    }
```

### 4.3 核心方法

#### 加载历史

```python
def load_history(self, agent: Agent, user_id: str, conversation_id: str) -> bool:
    """
    加载对话历史到内存

    流程：
    1. 如果会话不存在于数据库 → 创建新会话
    2. 如果会话存在 → 从数据库加载最近 N 轮 (memory_window)
    3. 排除 ERROR 类型消息

    Returns:
        bool: 是否首次加载（新会话）
    """
```

#### 添加消息

```python
def add_user_message(agent, user_id, conversation_id, round_id, content):
    """添加用户消息"""
    # 1. 创建 Message 对象
    # 2. 存入内存缓存
    # 3. 持久化到数据库

def add_assistant_message(agent, user_id, conversation_id, round_id,
                         content, tool_calls=None, token_usage=None,
                         reasoning_content="", is_agent=False, agent_id=None):
    """添加助手消息

    特殊处理：
    - reasoning_content 只存数据库，不进内存历史（保持对话干净）
    - tool_calls 非空时，类型为 TOOL_CALL 或 AGENT_START
    - 自动调用 TokenManager 统计 Token
    """

def add_tool_result_message(agent, user_id, conversation_id, round_id,
                           tool_call_id, result, success=True, tool_name=None):
    """添加工具结果消息"""

def add_sub_agent_message(agent, user_id, conversation_id, round_id,
                         content, agent_id, tool_call_id=None, sub_conversation_id=None):
    """添加子Agent结果消息"""

def add_error_message(user_id, conversation_id, round_id, error_message):
    """添加错误消息（只存数据库，不进内存）"""
```

#### 构建 LLM 历史

```python
def get_history(self, agent: Agent, user_id: str, conversation_id: str) -> List[Dict]:
    """
    构建 Function Calling 格式的对话历史

    Returns:
        [
            {"role": "system", "content": "系统提示词..."},
            {"role": "user", "content": "用户问题"},
            {"role": "assistant", "content": "...", "tool_calls": [...]},
            {"role": "tool", "tool_call_id": "xxx", "name": "tool_name", "content": "结果"},
            {"role": "assistant", "content": "最终回答"},
            ...
        ]
    """
```

### 4.4 历史构建详细流程

```
get_history() 执行流程：

1. 添加 system message
   └─→ {"role": "system", "content": agent.system_prompt}

2. 遍历所有轮次（按时间排序）
   │
   ├─→ CONTENT 消息
   │     └─→ {"role": "user/assistant", "content": "..."}
   │
   ├─→ TOOL_CALL / AGENT_START 消息
   │     ├─→ 如果 content 为空，填充 "[思考被中断...]"
   │     └─→ {"role": "assistant", "content": "...", "tool_calls": [...]}
   │         记录待匹配的 tool_call_id
   │
   ├─→ TOOL_RESULT 消息
   │     └─→ {"role": "tool", "tool_call_id": "xxx", "name": "...", "content": "结果"}
   │         从待匹配列表中移除
   │
   └─→ AGENT_END 消息
         └─→ {"role": "tool", "tool_call_id": "xxx", "name": "call_agent", "content": "结果"}

3. 轮次结束检查
   └─→ 如果有未匹配的 tool_call_id，添加虚拟响应
       {"role": "tool", "tool_call_id": "xxx", "content": "[执行被中断]"}
```

### 4.5 轮次结束处理

```python
async def on_round_end(self, agent, conversation_id, round_id, websocket_handler):
    """
    轮次结束后的处理（按顺序执行）

    1. 计算并记录轮次执行时间
    2. 如果无标题 → 生成对话标题
    3. 如果启用自动问题 → 异步生成推荐问题
    4. Round 总结（必须等待完成）
    5. 检查是否需要 Snapshot 总结
    6. 检查是否需要 Conversation 总结
    """
```

---

## 五、消息保存流程

### 5.1 单轮对话消息保存

```
用户发送消息
    │
    ▼
┌─────────────────────────────────────────┐
│ 1. load_history()                        │
│    - 加载/创建会话                        │
│    - 加载最近 N 轮历史到内存              │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 2. load_round()                          │
│    - 如果 round_id 不存在 → 创建新轮次   │
│    - 滚动 memory_window                  │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 3. add_user_message()                    │
│    - 创建 Message(type=CONTENT)          │
│    - 存入内存 + 数据库                    │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 4. LLM 调用 (可能多轮工具调用)           │
│    │                                     │
│    ├─→ add_assistant_message()           │
│    │   - 普通回复 或 带 tool_calls       │
│    │   - 存入内存 + 数据库               │
│    │   - Token 统计                      │
│    │                                     │
│    ├─→ [如有工具调用] 执行工具           │
│    │                                     │
│    ├─→ add_tool_result_message()         │
│    │   - 工具结果                        │
│    │   - 存入内存 + 数据库               │
│    │                                     │
│    └─→ 继续调用 LLM...                   │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 5. on_round_end()                        │
│    - 标题生成                            │
│    - 总结处理                            │
└─────────────────────────────────────────┘
```

### 5.2 子 Agent 消息保存

```
主 Agent 调用 call_agent 工具
    │
    ▼
┌─────────────────────────────────────────┐
│ 主对话：add_assistant_message()          │
│   type=AGENT_START, is_agent=True        │
│   tool_calls=[{function: call_agent}]    │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 创建子对话 (sub_conversation_id)         │
│   - is_agent_call=1                      │
│   - parent_conversation_id=主对话ID      │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 子 Agent 执行                            │
│   - 独立的 HistoryManager 流程           │
│   - 消息保存到子对话                      │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 主对话：add_sub_agent_message()          │
│   type=AGENT_END                         │
│   role=tool                              │
│   tool_call_id=匹配的ID                  │
│   sub_conversation_id=子对话ID           │
└─────────────────────────────────────────┘
```

---

## 六、WebSocket 实时推送

> 详细内容见 [WebSocket 运行流程](./websocket_运行流程.md)

### 6.1 消息类型映射

| HistoryManager 保存 | WebSocket 推送 | 说明 |
|---------------------|----------------|------|
| add_user_message | - | 用户消息不推送 |
| add_assistant_message (无 tool_calls) | CHUNK → SEGMENT | 流式文本 |
| add_assistant_message (有 tool_calls) | TOOL_CALL | 工具调用通知 |
| add_tool_result_message | TOOL_RESPONSE | 工具结果 |
| add_sub_agent_message | - | 子Agent结果 |
| add_error_message | ERROR | 错误消息 |

### 6.2 推送时机

```python
# ChatProcessor 中的推送逻辑

# 1. 流式文本块
await websocket_handler.send_message(
    conversation_id,
    MessageBuilder.create_chunk_message(conversation_id, chunk_text)
)

# 2. 完整片段结束
await websocket_handler.send_message(
    conversation_id,
    MessageBuilder.create_segment_message(conversation_id, full_text, reasoning)
)

# 3. 工具调用
await websocket_handler.send_message(
    conversation_id,
    MessageBuilder.create_tool_call_message(conversation_id, name, id, args)
)

# 4. 工具结果
await websocket_handler.send_message(
    conversation_id,
    MessageBuilder.create_tool_response_message(conversation_id, result, name, id, success)
)
```

---

## 七、前端查询接口

### 7.1 ConversationManager

**文件**: `core/conversation_manager.py`

职责：
- 查询对话列表
- 查询对话消息（分页）
- 消息格式转换（给前端用）

### 7.2 REST API 端点

**文件**: `api/endpoints/conversations.py`

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/conversations/` | GET | 获取用户对话列表（分页） |
| `/api/v1/conversations/{id}` | GET | 获取对话详情 |
| `/api/v1/conversations/{id}/messages` | GET | 获取对话消息（分页） |
| `/api/v1/conversations/{id}` | DELETE | 软删除对话 |
| `/api/v1/conversations/{id}/title` | PUT | 更新对话标题 |
| `/api/v1/conversations/apply_id` | POST | 申请新对话ID |
| `/api/v1/conversations/stop/{id}` | POST | 停止对话生成 |

### 7.3 前端消息格式转换

```python
def _process_messages_for_frontend(self, raw_messages: List[Message]) -> List[FrontendMessage]:
    """
    将数据库消息转换为前端格式

    转换规则：
    - CONTENT (user) → FrontendMessage(role=USER)
    - CONTENT (assistant) → FrontendMessage(role=ASSISTANT)
    - TOOL_CALL → FrontendMessage(role=TOOL, tool=ToolInfo)
    - AGENT_START → FrontendMessage(role=AGENT, sub_agent=SubAgentInfo)
    - TOOL_RESULT → 更新对应 ToolInfo 的 result
    - AGENT_END → 更新对应 SubAgentInfo 的 output
    """
```

### 7.4 前端消息结构

```python
class FrontendMessage:
    round_id: str           # 轮次ID
    message_id: str         # 消息ID
    timestamp: str          # 时间戳
    role: FrontendMessageRole  # USER / ASSISTANT / TOOL / AGENT
    text: TextContent = None   # 文本内容
    attachments: List[str] = None  # VL 附件文件名列表
    tool: ToolInfo = None      # 工具调用信息
    sub_agent: SubAgentInfo = None  # 子Agent信息
    token: int = None          # Token数
    model: str = None          # 模型名称

class ToolInfo:
    tool_name: str          # 工具名称
    tool_arguments: str     # 参数
    tool_call_id: str       # 调用ID
    tool_result: str        # 结果
    tool_status: bool       # 是否成功
    execution_time: float   # 执行时间(秒)

class SubAgentInfo:
    agent_id: str           # Agent ID
    agent_call_id: str      # 调用ID
    agent_input: str        # 输入任务
    agent_output: str       # 输出结果
    agent_conversation_id: str  # 子会话ID
    agent_status: bool      # 是否成功
    execution_time: float   # 执行时间(秒)
```

---

## 八、Memory Window 滚动机制

### 8.1 配置

```ini
# agent.ini
[workorder-agent]
llm_memory_window = 10  # 保留最近 10 轮对话
```

### 8.2 滚动逻辑

```python
def _roll_memory_window(self, agent, user_id, conversation_id):
    """
    当内存中的轮次数超过 memory_window 时，移除最旧的轮次

    注意：只影响内存缓存，不影响数据库存储
    """
    rounds = self.histories[user_id][conversation_id]["rounds"]
    if len(rounds) <= agent.llm_memory_window:
        return

    # 按时间排序，保留最新的 N 轮
    sorted_rounds = sorted(rounds.items(), key=lambda x: x[1][0].timestamp)
    keep_rounds = dict(sorted_rounds[-agent.llm_memory_window:])
    self.histories[user_id][conversation_id]["rounds"] = keep_rounds
```

### 8.3 加载时的处理

```python
# 从数据库加载时，只加载最近 N 轮
rounds = self.sqlite_storage.get_rounds_recorder_by_memory_window(
    conversation_id,
    agent.llm_memory_window
)
```

---

## 九、数据一致性保证

### 9.1 双写策略

每条消息同时写入：
1. **内存缓存** - 供 `get_history()` 快速访问
2. **数据库** - 持久化存储

### 9.2 异常处理

```python
def add_user_message(...):
    try:
        # 1. 验证会话和轮次存在
        if user_id not in self.histories:
            raise ValueError(...)

        # 2. 创建消息
        message = Message.create_user_message(content, round_id)

        # 3. 存入内存
        self.histories[user_id][conversation_id]["rounds"][round_id].append(message)

        # 4. 存入数据库
        self.sqlite_storage.add_message(round_id, message)

    except Exception as e:
        self.logger.error("添加用户消息失败", exception=e)
        raise  # 重新抛出，让上层处理
```

### 9.3 tool_call 匹配验证

```python
# get_history() 中的验证逻辑
round_tool_calls = {}  # 记录待匹配的 tool_call_id

# 遇到 TOOL_CALL 消息时
for tc in msg.tool_calls:
    round_tool_calls[tc["id"]] = tc["function"]["name"]

# 遇到 TOOL_RESULT 消息时
if tool_id in round_tool_calls:
    del round_tool_calls[tool_id]  # 匹配成功

# 轮次结束时，检查未匹配的
if round_tool_calls:
    # 添加虚拟响应，防止 LLM 格式错误
    for tool_id, tool_name in round_tool_calls.items():
        result.append({
            "role": "tool",
            "tool_call_id": tool_id,
            "name": tool_name,
            "content": "[执行被中断]"
        })
```

---

## 十、文件位置索引

| 组件 | 文件路径 |
|------|----------|
| Message 模型 | `koalaq_hub/models/message.py` |
| HistoryManager | `koalaq_hub/core/history_manager.py` |
| ConversationManager | `koalaq_hub/core/conversation_manager.py` |
| WebSocketHandler | `koalaq_hub/core/websocket_handler.py` |
| Conversations 端点 | `koalaq_hub/api/endpoints/conversations.py` |
| 前端消息模型 | `koalaq_hub/api/models/frontend_message.py` |
| TokenManager | `koalaq_hub/core/token_manager.py` |
| SummaryManager | `koalaq_hub/core/summary_manager.py` |

---

## 十一、关键设计决策

### 11.1 reasoning_content 分离

- **问题**：思维链内容会污染对话历史，影响 LLM 理解
- **方案**：`reasoning_content` 只存数据库，不进内存历史
- **实现**：`add_assistant_message` 创建两个 Message 对象

### 11.2 内存 + 数据库双存储

- **问题**：每次构建历史都查数据库太慢
- **方案**：内存缓存 + memory_window 限制
- **实现**：`histories` 字典 + 滚动清理

### 11.3 tool_call_id 匹配验证

- **问题**：LLM 要求每个 tool_call 必须有对应的 tool 响应
- **方案**：`get_history()` 中检测未匹配的 tool_call，补充虚拟响应
- **效果**：防止因中断导致的格式错误

### 11.4 子 Agent 作为 tool 响应

- **问题**：子 Agent 是 Function Calling 调用的，需要返回 tool 消息
- **方案**：`AGENT_END` 消息的 role 设为 `tool`，name 设为 `call_agent`
- **效果**：LLM 能正确解析子 Agent 的响应
