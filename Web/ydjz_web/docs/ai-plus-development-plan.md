# AI+ 功能开发计划与理解文档

## 功能理解总结

### 1. 界面设计
- **对话流界面**：类似聊天应用的对话界面
- **双方对话**：用户（蓝底白字）+ AI（浅灰底深灰字），圆角10px
- **输入区域**：底部固定输入框（限制100字）+ 发送按钮
- **发送逻辑**：点击发送后清空输入框，显示loading，禁用发送按钮直到收到结束信号
- **实时更新**：WebSocket流式接收，逐块显示AI回复

### 2. 消息类型与显示逻辑

#### Chunk类型（流式文本）
- 实时拼接显示AI回复
- 支持思维链模式（reasoning）和普通内容（content）

#### Segment类型（完整段落）
- 收到segment时，删除上一个segment之后的所有chunk
- 显示完整的处理过的segment内容
- 支持markdown解析和思维链折叠

#### Tool类型（工具调用）
- **tool_call**: 显示loading状态，显示工具名称
- **tool_response**: 结束loading，显示成功/失败状态
- **可点击弹窗**：显示tool_call和tool_response的详细信息

### 3. 数据管理
- **HTTP历史**：页面进入时获取对话历史（需要conversation_id）
- **WebSocket实时**：用户发送消息，实时接收AI回复
- **会话管理**：缓存conversation_id，首次对话传空值

### 4. 界面状态
- **标题动态**：初始"AI+"，连接后显示服务端返回的title
- **连接状态**：顶部显示WebSocket连接状态
- **时间戳**：每个对话框下方显示发送时间
- **滚动支持**：对话列表可向上滚动查看历史

## 开发计划

### Phase 1: 基础界面搭建（第1天）
1. **安装依赖**
   - markdown-it（markdown解析）
   - 可能需要的其他UI增强库

2. **重构AI.vue组件**
   - 创建对话界面布局
   - 实现输入框和发送按钮
   - 添加消息列表容器

3. **创建消息组件**
   - UserMessage.vue（用户消息）
   - AIMessage.vue（AI消息，支持markdown）
   - ToolMessage.vue（工具调用消息）

### Phase 2: 数据层实现（第2天）
1. **扩展WebSocket管理器**
   - 添加消息类型处理
   - 实现实时数据流解析
   - 添加conversation_id管理

2. **实现HTTP历史接口**
   - 扩展ai-request.js
   - 添加获取历史消息方法
   - 实现数据格式转换

3. **状态管理**
   - 消息列表状态
   - 连接状态管理
   - 缓存conversation_id

### Phase 3: 消息处理逻辑（第3天）
1. **Chunk处理**
   - 实时文本拼接
   - 思维链内容分离
   - 内容类型判断

2. **Segment处理**
   - 删除后续chunk逻辑
   - Markdown渲染
   - 思维链折叠功能

3. **Tool处理**
   - 配对tool_call和tool_response
   - Loading状态管理
   - 弹窗详情显示

### Phase 4: 用户交互（第4天）
1. **发送消息功能**
   - 输入验证（100字限制）
   - WebSocket消息发送
   - UI状态控制

2. **界面交互**
   - 滚动控制
   - Tool消息点击
   - 思维链展开/折叠

3. **错误处理**
   - 连接失败处理
   - 消息发送失败
   - 重连机制

### Phase 5: 优化与完善（第5天）
1. **性能优化**
   - 消息列表虚拟滚动（如果消息很多）
   - 内存管理
   - 渲染优化

2. **用户体验**
   - 动画效果
   - 加载指示器
   - 错误提示优化

3. **测试与调试**
   - 各种消息类型测试
   - 边界情况处理
   - 兼容性测试

## 技术实现要点

### 1. WebSocket消息处理
```javascript
// 消息类型分发
handleWebSocketMessage(data) {
  switch(data.type) {
    case 'chunk': this.handleChunk(data); break;
    case 'segment': this.handleSegment(data); break;
    case 'tool_call': this.handleToolCall(data); break;
    case 'tool_response': this.handleToolResponse(data); break;
  }
}
```

### 2. 思维链折叠
```vue
<template>
  <div v-if="message.object?.reasoning_content">
    <van-collapse v-model="activeNames">
      <van-collapse-item title="思维链" name="reasoning">
        <div v-html="renderedReasoning"></div>
      </van-collapse-item>
    </van-collapse>
  </div>
</template>
```

### 3. Tool配对逻辑
```javascript
// Tool消息配对
handleToolCall(data) {
  this.pendingTools[data.conversation_id] = data;
  this.showToolLoading(data);
}

handleToolResponse(data) {
  const toolCall = this.pendingTools[data.conversation_id];
  if (toolCall) {
    this.createToolMessage(toolCall, data);
    delete this.pendingTools[data.conversation_id];
  }
}
```

## 接口对接

### HTTP接口
- **URL**: `{aiApiUrl}/api/v1/conversations/{conversation_id}/messages`
- **Headers**: `user_id: user_67ce21d6-a11c-4340-851b-7a8949906aa3`
- **返回**: 历史消息列表 + conversation_id + title

### WebSocket接口
- **URL**: `{aiWebSocketUrl}/ws/chat?user_id=xxx&app_id=easy-accounts-assistant&use_think_llm=false`
- **发送**: `{conversation_id, content}`
- **接收**: chunk/segment/tool_call/tool_response

## 数据结构分析

### HTTP历史消息结构
```javascript
{
  "success": true,
  "data": {
    "messages": [
      {
        "message_id": 50,
        "round_id": "247aa21e-47bd-423b-83e2-179df0b855e6",
        "type": "segment|tool|user",
        "content": "消息内容",
        "timestamp": "2025-07-12 17:56:50",
        "tool_name": "flows", // 仅tool类型
        "status": 1, // 仅tool类型，1=成功
        "object": { // 仅tool类型，包含详细信息
          "tool_call": "...",
          "tool_response": "..."
        }
      }
    ],
    "conversation_id": "conv_xxx",
    "title": "小易趣味账务助手"
  }
}
```

### WebSocket实时消息结构
```javascript
// 1. Chunk（流式文本片段）
{
  "conversation_id": "conv_xxx",
  "is_finish": false,
  "type": "chunk",
  "text": "文本片段",
  "object": {
    "content_type": "content|reasoning" // content=正文，reasoning=思维链
  },
  "status": true
}

// 2. Segment（完整段落）
{
  "conversation_id": "conv_xxx",
  "is_finish": true,
  "type": "segment", 
  "text": "完整的AI回复内容",
  "object": {
    "reasoning_content": "思维链内容" // 可选
  },
  "status": true
}

// 3. Tool Call（工具调用）
{
  "conversation_id": "conv_xxx",
  "is_finish": true,
  "type": "tool_call",
  "text": "工具名称",
  "object": {
    "tool": "工具名称",
    "arguments": {} // 工具参数
  },
  "status": true
}

// 4. Tool Response（工具响应）
{
  "conversation_id": "conv_xxx", 
  "is_finish": true,
  "type": "tool_response",
  "text": "工具名称",
  "object": {
    "tool_name": "工具名称",
    "result": "工具执行结果"
  },
  "status": true // true=成功，false=失败
}
```

## 关键技术细节

### 1. Conversation ID管理
- 初次进入：检查localStorage是否有conversation_id
- 无ID：发送消息时传空字符串，从WebSocket响应中获取新ID并缓存
- 有ID：发送消息时使用缓存的ID，并调用HTTP接口获取历史

### 2. 消息处理顺序
- Chunk → 实时拼接显示
- Segment → 替换之前的所有chunk，显示最终内容
- Tool Call → 显示loading
- Tool Response → 与Tool Call配对，显示结果

### 3. UI特殊要求
- 用户消息：蓝底白字，圆角10px
- AI消息：浅灰底深灰字，圆角10px，支持markdown
- Tool消息：可点击，显示loading状态
- 思维链：可折叠展开
- 输入框：100字限制，发送后禁用直到收到结束信号

## 文件结构规范

为了便于调试和维护，AI+功能将采用模块化文件结构：

```
src/views/ai/
├── AI.vue                    # 主容器组件，负责布局和状态管理
├── components/               # 子组件目录
│   ├── ChatContainer.vue     # 聊天消息容器
│   ├── MessageInput.vue      # 消息输入框组件
│   ├── MessageList.vue       # 消息列表组件
│   ├── messages/            # 消息类型组件
│   │   ├── UserMessage.vue   # 用户消息组件
│   │   ├── AIMessage.vue     # AI消息组件
│   │   ├── ToolMessage.vue   # 工具消息组件
│   │   └── ChunkMessage.vue  # 流式消息组件
│   └── ui/                  # UI组件
│       ├── MarkdownRenderer.vue  # Markdown渲染组件
│       ├── ThinkingChain.vue     # 思维链折叠组件
│       └── ToolDetailModal.vue   # 工具详情弹窗组件
├── composables/             # 组合式函数
│   ├── useConversation.js   # 对话管理逻辑
│   ├── useMessageHandler.js # 消息处理逻辑
│   ├── useWebSocketChat.js  # WebSocket聊天逻辑
│   └── useHistoryLoader.js  # 历史消息加载逻辑
└── types/                   # 类型定义
    └── message-types.js     # 消息类型定义
```

### 组件职责分工

#### 1. 主容器组件 (AI.vue)
- 整体布局管理
- 全局状态管理
- 组件协调

#### 2. 聊天组件
- **ChatContainer.vue**: 聊天区域容器，处理滚动
- **MessageInput.vue**: 输入框，处理用户输入和发送
- **MessageList.vue**: 消息列表，管理消息渲染

#### 3. 消息组件
- **UserMessage.vue**: 用户消息样式和逻辑
- **AIMessage.vue**: AI消息，集成markdown和思维链
- **ToolMessage.vue**: 工具消息，处理loading和状态
- **ChunkMessage.vue**: 流式消息实时更新

#### 4. UI组件
- **MarkdownRenderer.vue**: 独立的markdown渲染器
- **ThinkingChain.vue**: 思维链展开折叠
- **ToolDetailModal.vue**: 工具详情弹窗

#### 5. 组合式函数 (Composables)
- **useConversation.js**: conversation_id管理，缓存
- **useMessageHandler.js**: 消息类型处理，分发逻辑
- **useWebSocketChat.js**: WebSocket连接和消息收发
- **useHistoryLoader.js**: HTTP历史消息加载

### 开发优势
1. **模块化**: 每个文件职责明确，便于调试
2. **可复用**: 组件和组合式函数可以独立测试
3. **可维护**: 修改某个功能不会影响其他模块
4. **团队协作**: 不同开发者可以并行开发不同模块

这个开发计划预计需要5天完成，每天专注一个核心功能模块，确保功能的完整性和用户体验。