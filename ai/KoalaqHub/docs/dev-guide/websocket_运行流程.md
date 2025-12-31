# WebSocket 运行流程

> 版本: 1.1
> 更新时间: 2025-12-31
> 状态: 正式版

本文档描述 KoalaQ Hub 中 WebSocket 通信系统的架构、消息格式和交互流程。

> 关联文档：
> - [Agent 运行流程](./agent_运行流程.md)
> - [LLM 运行流程](./llm_运行流程.md)
> - [VL 运行流程](./VL_运行流程.md) - 图片附件处理

## 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      客户端层                                    │
├─────────────────────────────────────────────────────────────────┤
│  WebSocket Client (前端)                                        │
│  ws://localhost:8001/ws/chat?user_id=xxx&agent_id=xxx          │
└─────────────────────────────────────────────────────────────────┘
                              ↑↓
┌─────────────────────────────────────────────────────────────────┐
│                      端点层                                      │
├─────────────────────────────────────────────────────────────────┤
│  websocket.py - WebSocket 端点                                  │
│  ├─ 验证参数 (user_id, agent_id)                               │
│  ├─ 创建 Agent 实例                                             │
│  ├─ 接收/解析消息                                               │
│  └─ 调用 AgentExecutor                                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      处理层                                      │
├─────────────────────────────────────────────────────────────────┤
│  WebSocketChatProcessor                                         │
│  ├─ 调用 LLM (流式)                                             │
│  ├─ 执行工具调用                                                │
│  └─ 通过 WebSocketHandler 发送消息                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      通信层                                      │
├─────────────────────────────────────────────────────────────────┤
│  WebSocketHandler                                               │
│  ├─ active_connections: Dict[conversation_id, WebSocket]       │
│  ├─ connect() / disconnect()                                    │
│  ├─ send_message()                                              │
│  └─ is_connected()                                              │
└─────────────────────────────────────────────────────────────────┘
```

## 一、消息格式定义

### 消息类型枚举 (MessageType)

| 类型 | 值 | 说明 | 方向 |
|------|-----|------|------|
| `CHUNK` | `chunk` | 流式文本块 | Server→Client |
| `SEGMENT` | `segment` | 完整响应片段 | Server→Client |
| `TOOL_CALL` | `tool_call` | 工具调用通知 | Server→Client |
| `TOOL_RESPONSE` | `tool_response` | 工具执行结果 | Server→Client |
| `START` | `start` | Agent 开始执行 | Server→Client |
| `COMPLETE` | `complete` | 处理完成 | Server→Client |
| `EXIT` | `exit` | 退出/轮次结束 | Server→Client |
| `ERROR` | `error` | 错误信息 | Server→Client |
| `TITLE` | `title` | 对话标题 | Server→Client |
| `QUESTION` | `question` | 问题建议 | Server→Client |

### 客户端发送消息格式

```json
{
  "conversation_id": "conv_123",      // 会话ID（可选，不传则自动生成）
  "content": "用户输入的消息",         // 必填
  "use_think_llm": true,              // 是否使用思考模式（可选）
  "attachments": [                    // VL 附件列表（可选）
    {
      "filename": "image.png",
      "data": "base64...",            // 或 URL
      "media_type": "image/png"
    }
  ]
}
```

> **VL 支持**: 详见 [VL 运行流程](./VL_运行流程.md)

心跳包格式：
```json
{
  "type": "ping"
}
```

### 服务端响应消息格式

```typescript
interface WebSocketMessage {
  conversation_id: string;    // 会话ID
  is_finish: boolean;         // 是否结束
  type: string;               // 消息类型
  text: string;               // 文本内容
  object: object;             // 附加数据
  status: boolean;            // 状态（成功/失败）
  agent: AgentMessage | null; // 子Agent信息（如有）
}

interface AgentMessage {
  agent_id: string;           // 子Agent ID
  agent_conversation_id: string; // 子Agent会话ID
}
```

### 各类型消息示例

#### 1. chunk - 流式文本块
```json
{
  "conversation_id": "conv_123",
  "is_finish": false,
  "type": "chunk",
  "text": "你好",
  "object": {"content_type": "content"},
  "status": true,
  "agent": null
}
```

content_type 可选值：
- `content` - 普通内容
- `reasoning` - 思维链内容

#### 2. segment - 完整响应片段
```json
{
  "conversation_id": "conv_123",
  "is_finish": true,
  "type": "segment",
  "text": "完整的回复内容",
  "object": {"reasoning_content": "思考过程..."},
  "status": true,
  "agent": null
}
```

#### 3. tool_call - 工具调用通知
```json
{
  "conversation_id": "conv_123",
  "is_finish": true,
  "type": "tool_call",
  "text": "get_weather",
  "object": {
    "tool_call_id": "call_abc123",
    "tool_name": "get_weather",
    "tool_arguments": "{\"city\": \"北京\"}"
  },
  "status": true,
  "agent": null
}
```

#### 4. tool_response - 工具执行结果
```json
{
  "conversation_id": "conv_123",
  "is_finish": true,
  "type": "tool_response",
  "text": "get_weather",
  "object": {
    "tool_call_id": "call_abc123",
    "tool_name": "get_weather",
    "tool_response": {"temperature": 25, "weather": "晴"}
  },
  "status": true,
  "agent": null
}
```

#### 5. start - Agent 开始执行
```json
{
  "conversation_id": "conv_123",
  "is_finish": true,
  "type": "start",
  "text": "weather_agent",
  "object": {"agent_id": "weather_agent", "task": "查询天气"},
  "status": true,
  "agent": {"agent_id": "weather_agent", "agent_conversation_id": "sub_conv_456"}
}
```

#### 6. exit - 轮次结束
```json
{
  "conversation_id": "conv_123",
  "is_finish": true,
  "type": "exit",
  "text": "",
  "object": {"exit": true},
  "status": true,
  "agent": null
}
```

#### 7. error - 错误消息
```json
{
  "conversation_id": "conv_123",
  "is_finish": true,
  "type": "error",
  "text": "处理消息时出错",
  "object": {"error": true, "message": "处理消息时出错"},
  "status": false,
  "agent": null
}
```

#### 8. title - 对话标题
```json
{
  "conversation_id": "conv_123",
  "is_finish": true,
  "type": "title",
  "text": "关于天气查询的对话",
  "object": {"title": "关于天气查询的对话"},
  "status": true,
  "agent": null
}
```

#### 9. question - 问题建议
```json
{
  "conversation_id": "conv_123",
  "is_finish": true,
  "type": "question",
  "text": "",
  "object": {"questions": ["明天天气如何？", "北京气温多少？"]},
  "status": true,
  "agent": null
}
```

## 二、连接建立流程

### WebSocket URL 格式

```
ws://localhost:8001/ws/chat?user_id={user_id}&agent_id={agent_id}&tool_tokens={tokens}
```

参数说明：
| 参数 | 必填 | 说明 |
|------|------|------|
| `user_id` | 是 | 用户ID |
| `agent_id` | 是 | Agent ID |
| `tool_tokens` | 否 | 工具认证token，格式：`key1=value1\|key2=value2` |

### 连接建立流程

```
Client                                Server
   |                                    |
   |-------- WebSocket Connect -------->|
   |    ?user_id=xxx&agent_id=xxx       |
   |                                    |
   |                        1. 验证 user_id
   |                        2. 验证 agent_id
   |                        3. 创建 Agent 实例
   |                        4. 解析 tool_tokens
   |                                    |
   |<------- Connection Accept ---------|
   |                                    |
   |                        5. 进入消息循环
```

### 连接建立代码流程

```python
# websocket.py
async def websocket_chat_handler(websocket: WebSocket):
    # 1. 获取参数
    user_id = websocket.query_params.get("user_id")
    agent_id = websocket.query_params.get("agent_id")

    # 2. 验证用户
    user = user_manager.get_user(user_id)
    if not user:
        await websocket.close(code=4401, reason="用户不存在")
        return

    # 3. 创建 Agent 实例
    agent = await agent_registry.get_or_create_user_agent(user_id, agent_id)
    agent.websocket_mode = True

    # 4. 接受连接
    await websocket.accept()

    # 5. 消息循环
    while True:
        message = await websocket.receive_text()
        # ... 处理消息
```

## 三、消息处理流程

### 完整交互时序图

```
Client          Endpoint         AgentExecutor      ChatProcessor       LLMClient        WebSocketHandler
   |               |                   |                  |                 |                   |
   |-- message --->|                   |                  |                 |                   |
   |               |                   |                  |                 |                   |
   |               |-- connect() -------------------------------------------->|                  |
   |               |                   |                  |                 |                   |
   |               |-- build_system_prompt() ------------>|                 |                   |
   |               |                   |                  |                 |                   |
   |               |-- execute() ----->|                  |                 |                   |
   |               |                   |                  |                 |                   |
   |               |                   |-- process_message() -->|           |                   |
   |               |                   |                  |                 |                   |
   |               |                   |                  |-- stream() ---->|                   |
   |               |                   |                  |                 |                   |
   |<-- chunk --------------------------------------------------|-----------|-- send_message() |
   |<-- chunk --------------------------------------------------|-----------|-- send_message() |
   |<-- chunk --------------------------------------------------|-----------|-- send_message() |
   |               |                   |                  |                 |                   |
   |               |                   |                  |<-- LLMResponse -|                   |
   |               |                   |                  |                 |                   |
   |<-- segment --------------------------------|---------|-----------------|-- send_message() |
   |               |                   |                  |                 |                   |
   |               |                   |        [如果有工具调用]             |                   |
   |<-- tool_call -------------------------------|---------|-----------------|-- send_message() |
   |               |                   |                  |                 |                   |
   |               |                   |        [执行工具]                   |                   |
   |               |                   |                  |                 |                   |
   |<-- tool_response --------------------------|---------|-----------------|-- send_message() |
   |               |                   |                  |                 |                   |
   |               |                   |        [递归调用 LLM]              |                   |
   |               |                   |                  |                 |                   |
   |<-- chunk --------------------------------------------------|-----------|-- send_message() |
   |               |                   |                  |                 |                   |
   |<-- segment --------------------------------|---------|-----------------|-- send_message() |
   |               |                   |                  |                 |                   |
   |<-- exit -----------------------------------|---------|-----------------|-- send_message() |
   |               |                   |                  |                 |                   |
```

### 消息发送点汇总

| 发送位置 | 消息类型 | 触发条件 |
|----------|----------|----------|
| `EnhancedLLMClient._stream_websocket()` | `chunk` | LLM 流式输出每个 token |
| `BaseChatProcessor.process_message()` | `segment` | LLM 响应完成 |
| `BaseChatProcessor.process_message()` | `exit` | 轮次结束，无工具调用 |
| `BaseChatProcessor.process_message()` | `error` | 处理异常 |
| `BaseChatProcessor._execute_tool_calls()` | `tool_call` | 检测到工具调用 |
| `BaseChatProcessor._execute_tool_calls()` | `tool_response` | 工具执行完成 |
| `BaseChatProcessor._handle_tool_and_agent_calls()` | `exit` | 工具调用后无需继续 |
| `HistoryManager.on_round_end()` | `title` | 首轮结束生成标题 |
| `HistoryManager.on_round_end()` | `question` | 启用自动问题时 |
| `SubAgentExecutor` | `start` | 子 Agent 开始执行 |
| `SubAgentExecutor` | `complete` | 子 Agent 执行完成 |

## 四、Agent 集成

### Agent 创建流程

```python
# 1. WebSocket 端点获取 Agent
agent = await agent_registry.get_or_create_user_agent(user_id, agent_id)
agent.websocket_mode = True  # 标记为 WebSocket 模式

# 2. 设置动态参数
agent.current_conversation_id = conversation_id
if data.get("use_think_llm"):
    agent.use_think_llm = True

# 3. 组装系统提示词
system_prompt = agent_registry.build_system_prompt(agent, user_id, conversation_id)
agent.system_prompt = system_prompt

# 4. 执行
await agent_executor.execute(
    agent=agent,
    message=content,
    conversation_id=conversation_id,
    user_id=user_id,
    source='websocket'  # 指定来源
)
```

### Agent 与 WebSocket 的关系

```
┌────────────────────────────────────────────────────────────────┐
│                    WebSocket 连接                               │
│  conversation_id ←→ WebSocket 连接 (1:1)                       │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│                    Agent 实例                                   │
│  ├─ agent.websocket_mode = True                                │
│  ├─ agent.current_conversation_id = conversation_id            │
│  └─ 每次请求创建新实例，不缓存                                   │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│                WebSocketChatProcessor                           │
│  ├─ call_llm() → 流式调用，实时推送 chunk                       │
│  ├─ send_message() → 通过 WebSocketHandler 发送                │
│  └─ websocket_handler 引用                                      │
└────────────────────────────────────────────────────────────────┘
```

### 子 Agent 调用流程

当主 Agent 调用子 Agent 时：

```
主 Agent 检测到 call_agent 工具调用
         ↓
SubAgentExecutor.execute()
         ↓
发送 start 消息（通知前端子 Agent 开始）
         ↓
创建子 Agent 实例（build_sub_agent）
         ↓
子 Agent 执行（InternalChatProcessor）
         ↓
发送 complete 消息（通知前端子 Agent 完成）
         ↓
返回结果给主 Agent
```

子 Agent 消息特点：
- 消息中包含 `agent` 字段，标识来源
- 使用 `InternalChatProcessor`，不直接推送 chunk
- 结果汇总后通过 `tool_response` 返回

## 五、连接管理

### WebSocketHandler 核心方法

```python
class WebSocketHandler:
    active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, conversation_id: str):
        """建立连接"""
        self.active_connections[conversation_id] = websocket

    async def disconnect(self, conversation_id: str):
        """断开连接"""
        del self.active_connections[conversation_id]

    async def send_message(self, conversation_id: str, message: WebSocketMessage):
        """发送消息"""
        if conversation_id in self.active_connections:
            await self.active_connections[conversation_id].send_text(message.to_json())

    def is_connected(self, conversation_id: str) -> bool:
        """检查连接状态"""
        if conversation_id not in self.active_connections:
            return False
        websocket = self.active_connections[conversation_id]
        return websocket.client_state == WebSocketState.CONNECTED
```

### 连接断开处理

```python
# LLM 流式调用中检查连接状态
async for chunk in stream:
    # 检查连接是否断开
    if not websocket_handler.is_connected(conversation_id):
        is_interrupted = True
        await stream.aclose()  # 主动关闭流，节省 token
        break

    # 正常处理 chunk
    await websocket_handler.send_message(conversation_id, message)
```

### 资源清理

```python
# websocket.py finally 块
finally:
    # 1. 清理 WebSocket 连接
    if agent_executor.websocket_handler.is_connected(conversation_id):
        await agent_executor.websocket_handler.disconnect(conversation_id)

    # 2. 标记 Agent 断开
    await agent_registry.mark_agent_disconnected(user_id, agent_id)

    # 3. 释放 Agent 引用
    agent = None
```

## 六、心跳机制

### 心跳包处理

```python
# 检查是否为心跳包
if data.get("type") == "ping":
    await websocket.send_text(json.dumps({"type": "pong"}))
    continue  # 不进入消息处理流程
```

### 心跳格式

请求：
```json
{"type": "ping"}
```

响应：
```json
{"type": "pong"}
```

## 七、错误码

| 错误码 | 说明 |
|--------|------|
| 4400 | 缺少必要参数 (user_id/agent_id) |
| 4401 | 用户不存在 |
| 4402 | Agent 不存在或未启用 |
| 5000 | 服务器内部错误 |

## 八、停止机制

### 问题背景

WebSocket 高速 chunk 数据流会阻塞停止信号的传递。当 LLM 高速输出时，WebSocket 通道被大量 chunk 数据占用，用户发送的停止消息可能无法及时到达服务端。

### 解决方案：HTTP 独立通道

使用独立的 HTTP 接口发送停止信号，绕过 WebSocket 数据流：

```
POST /api/v1/conversations/stop/{conversation_id}?cascade=true
```

参数说明：
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `conversation_id` | path | - | 要停止的会话 ID |
| `cascade` | query | `true` | 是否级联停止子 Agent |

### 停止流程时序图

```
Client (HTTP)          AgentExecutor       ChatProcessor       LLMClient          Stream
      |                      |                   |                  |                |
      |--- POST /stop ------>|                   |                  |                |
      |                      |                   |                  |                |
      |                      |-- stop() -------->|                  |                |
      |                      |                   |                  |                |
      |                      |                   |-- stop() ------->|                |
      |                      |                   |                  |                |
      |                      |                   |                  |-- aclose() --->|
      |                      |                   |                  |                |
      |                      |  [级联停止子对话]                      |                |
      |                      |                   |                  |                |
      |<-- 200 OK -----------|                   |                  |                |
```

### 对象持有链

停止机制依赖以下对象持有关系：

```
AgentExecutor
    └── active_processors: Dict[conversation_id, ChatProcessor]
            └── ChatProcessor.current_llm_client: EnhancedLLMClient
                    └── EnhancedLLMClient.current_stream: AsyncGenerator
                            └── should_stop: bool
```

### 级联停止

当主对话调用子 Agent 时，子对话 ID 格式为：`{conversation_id}_sub_{uuid}`

停止主对话时会自动查找并停止所有匹配的子对话：

```python
# AgentExecutor.stop() 内部逻辑
sub_prefix = f"{conversation_id}_sub_"
sub_conversation_ids = [
    cid for cid in self.active_processors.keys()
    if cid.startswith(sub_prefix)
]
for sub_cid in sub_conversation_ids:
    await self.active_processors[sub_cid].stop()
```

### 响应格式

成功停止：
```json
{
  "success": true,
  "data": {
    "conversation_id": "conv_123",
    "stopped": true,
    "cascade": true
  },
  "message": "已发送停止信号（含子对话）"
}
```

未找到活跃任务：
```json
{
  "success": true,
  "data": {
    "conversation_id": "conv_123",
    "stopped": false
  },
  "message": "未找到正在执行的任务"
}
```

### 前端集成示例

```javascript
// 停止当前对话
async function stopConversation(conversationId) {
  try {
    const response = await fetch(
      `/api/v1/conversations/stop/${conversationId}?cascade=true`,
      { method: 'POST' }
    );
    const result = await response.json();

    if (result.data.stopped) {
      console.log('已停止对话');
    } else {
      console.log('未找到正在执行的任务');
    }
  } catch (error) {
    console.error('停止失败:', error);
  }
}
```

### 相关代码位置

| 文件 | 说明 |
|------|------|
| `koalaq_hub/api/endpoints/conversations.py` | HTTP 停止端点 |
| `koalaq_hub/core/agents/agent_executor.py` | 停止逻辑、级联停止 |
| `koalaq_hub/core/chat/base_chat_processor.py` | Processor 停止方法 |
| `koalaq_hub/core/llm/enhanced_llm_client.py` | LLM 流停止实现 |

## 九、文件位置索引

| 文件 | 路径 | 说明 |
|------|------|------|
| WebSocket 处理器 | `koalaq_hub/core/websocket_handler.py` | 连接管理、消息构建 |
| WebSocket 端点 | `koalaq_hub/api/endpoints/websocket.py` | 路由、参数验证 |
| WebSocket 聊天处理器 | `koalaq_hub/core/chat/websocket_chat_processor.py` | 消息处理逻辑 |
| 基础聊天处理器 | `koalaq_hub/core/chat/base_chat_processor.py` | 公共处理逻辑 |
| LLM 客户端 | `koalaq_hub/core/llm/enhanced_llm_client.py` | 流式输出实现 |

## 十、前端集成示例

```javascript
// 建立连接
const ws = new WebSocket('ws://localhost:8001/ws/chat?user_id=user1&agent_id=assistant');

// 发送消息
ws.send(JSON.stringify({
  conversation_id: 'conv_123',
  content: '你好',
  use_think_llm: false
}));

// 接收消息
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch(data.type) {
    case 'chunk':
      // 流式文本，追加显示
      if (data.object.content_type === 'content') {
        appendContent(data.text);
      } else if (data.object.content_type === 'reasoning') {
        appendReasoning(data.text);
      }
      break;

    case 'segment':
      // 完整响应，可用于确认
      break;

    case 'tool_call':
      // 显示工具调用中
      showToolCalling(data.object.tool_name);
      break;

    case 'tool_response':
      // 显示工具结果
      showToolResult(data.object);
      break;

    case 'exit':
      // 轮次结束
      enableInput();
      break;

    case 'error':
      // 显示错误
      showError(data.text);
      break;

    case 'title':
      // 更新对话标题
      updateTitle(data.object.title);
      break;

    case 'question':
      // 显示推荐问题
      showSuggestions(data.object.questions);
      break;
  }
};

// 心跳
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({type: 'ping'}));
  }
}, 30000);
```
