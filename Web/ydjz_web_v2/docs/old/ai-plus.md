# AI+ 智能助手页面

## 页面功能描述
AI 智能对话助手，支持与 AI 进行实时对话，查看思考过程，工具调用等功能。

## 调用的 API 接口列表

### HTTP 接口
1. **GET** `/api/v1/conversations/{conversationId}/messages`
   - 用途：加载历史对话消息
   - 参数：conversationId（对话ID）
   - 返回：对话历史记录列表

### WebSocket 接口
- 连接地址：由 aiWebSocketManager 管理
- 消息类型：
  - chunk: 流式文本片段
  - segment: 完整段落
  - tool_call: 工具调用
  - tool_response: 工具响应
  - title: 标题更新
  - exit: 对话结束

## 页面数据结构

### 会话数据
- userId: 用户ID
- conversationId: 对话ID（localStorage 存储）
- currentTitle: 当前对话标题

### 消息数据
- messages: 消息列表
  - type: 消息类型（user/ai/tool）
  - content: 消息内容
  - reasoning: 思维链内容
  - hasReasoning: 是否包含思维链
  - timestamp: 时间戳

### 状态数据
- wsConnected: WebSocket 连接状态
- loading: 加载状态
- sending: 发送状态
- thinkMode: 思考模式开关

## 主要交互逻辑

### 对话管理
- 自动保存对话ID到 localStorage
- 支持开启新对话（清空历史）
- 加载历史消息记录
- 动态更新对话标题

### 消息发送
- 通过 WebSocket 发送消息
- 实时显示 AI 回复
- 支持 Markdown 渲染
- 支持表格水平滚动

### 思考模式
- 开启后显示 AI 思考过程
- 思维链可展开/折叠
- 实时显示思考内容

### 工具调用
- 显示工具调用状态
- 点击查看工具调用详情
- 展示调用参数和返回结果

### 连接管理
- 显示连接状态指示器
- 支持手动重连
- 断线自动重连
