# AI Plus 开发日志

## 项目概述

AI Plus 是 EasyAccounts 财务管理应用的 AI 助手功能，提供智能对话和财务数据查询能力。

### 技术栈
- **前端**: Vue 3 + Vant UI
- **通信**: WebSocket (实时) + HTTP API (历史)
- **AI服务**: 集成外部AI服务 (192.168.50.226:8001)
- **状态管理**: localStorage + Vuex

## 开发进度

### 阶段一：基础架构搭建 ✅
**时间**: 开发初期
**状态**: 已完成

#### 完成功能
1. **空界面创建**
   - 创建 `src/views/ai/AiPlus.vue` 基础组件
   - 添加路由配置 `/ai-plus`
   - 在 Dashboard 添加 AI+ 浮动按钮

2. **网络层集成**
   - 创建 `src/utils/ai-request.js` HTTP 工具类
   - 创建 `src/utils/websocket.js` WebSocket 管理器
   - 配置代理：`/ai-api` → `http://192.168.50.226:8001`

3. **基础UI设计**
   - 导航栏：标题 + 返回按钮
   - 内容区域：消息列表容器
   - 输入区域：输入框 + 发送按钮

### 阶段二：消息系统实现 ✅
**时间**: 中期开发
**状态**: 已完成

#### 历史消息加载
```javascript
// API格式解析
parseHistoryMessages(apiMessages) {
  // 处理 user、segment、tool 三种类型
  // 时间格式化：2025-07-12 17:56:50 → 17:56:50
  // 数据反转：API返回倒序 → UI正序显示
}
```

#### WebSocket实时通信
```javascript
// 消息类型处理
switch (data.type) {
  case 'chunk':    // 流式文本片段
  case 'segment':  // 完整回复段落  
  case 'tool_call': // 工具调用
  case 'tool_response': // 工具响应
  case 'exit':     // 对话结束
}
```

#### 统一消息格式
```javascript
{
  id: String,           // 唯一标识
  type: 'user|ai|tool', // 消息类型
  content: String,      // 显示内容
  timestamp: String,    // 时间戳
  // 工具消息扩展字段
  toolName: String,
  status: Boolean,
  toolCall: String,
  toolResponse: String
}
```

### 阶段三：UI/UX优化 ✅
**时间**: 中后期开发
**状态**: 已完成

#### 消息气泡设计
- **用户消息**: 右对齐，蓝色背景
- **AI消息**: 左对齐，灰色背景
- **工具消息**: 卡片式设计，状态指示

#### 工具消息优化
```css
.tool-message {
  background: 浅绿色(成功) | 浅红色(失败);
  border-radius: 8px;
  cursor: pointer; // 点击查看详情
}
```

#### 控制台风格详情弹窗
- **技术选择**: van-popup 替代 dialog
- **设计风格**: 黑色背景 + 绿色文本
- **内容分区**: 调用参数 | 返回结果
- **数据格式**: JSON 自动格式化

### 阶段四：输入框增强 ✅
**时间**: 后期优化
**状态**: 已完成

#### 圆角自适应输入框
```vue
<textarea
  class="message-textarea"
  rows="1"
  @input="adjustTextareaHeight"
  @keydown="handleKeydown"
/>
```

#### 功能特性
- **自动高度**: 1-3行自适应，超出显示滚动
- **快捷键**: Enter发送，Shift+Enter换行
- **圆角设计**: 20px圆角，聚焦时高亮边框
- **Loading状态**: 发送中按钮显示加载动画

### 阶段五：会话管理 ✅
**时间**: 最终优化
**状态**: 已完成

#### 动态conversation_id管理
```javascript
// localStorage缓存机制
initConversation() {
  this.conversationId = localStorage.getItem('ai_conversation_id') || '';
  if (this.conversationId) {
    this.loadMessages(); // 有ID才加载历史
  }
}

// 首次回复时自动缓存
handleWebSocketMessage(data) {
  if (data.conversation_id && data.conversation_id !== this.conversationId) {
    this.saveConversationId(data.conversation_id);
  }
}
```

#### 新对话功能
- **UI入口**: 导航栏右上角"新对话"按钮
- **清理逻辑**: 清空conversation_id + 消息列表 + 状态重置
- **用户反馈**: Toast提示"已开启新对话"

### 阶段六：路由和部署修复 ✅
**时间**: 部署阶段
**状态**: 已完成

#### 问题修复
1. **路由简化**: `/ai/plus` → `/ai-plus`
2. **资源路径**: `config.js` → `/config.js`
3. **History模式**: 添加 `historyApiFallback: true`
4. **刷新问题**: 解决直接访问URL时的404错误

## 技术细节

### WebSocket消息流
```
用户输入 → 发送消息 → AI处理
          ↓
chunk消息(实时) → segment消息(完整) → exit消息(结束)
          ↓              ↓              ↓
    实时显示文本    保存完整消息    重置发送状态
```

### 工具调用流程
```
tool_call消息 → 显示工具执行中 → tool_response消息 → 显示执行结果
     ↓                             ↓
  保存调用参数                   保存响应结果
     ↓                             ↓
         点击查看 → 控制台风格弹窗展示详情
```

### 自动滚动策略
- **历史加载后**: 滚动到底部查看最新消息
- **发送消息后**: 滚动到底部查看自己的消息
- **接收chunk时**: 实时滚动跟随AI输入
- **接收完整消息**: 滚动到底部查看完整内容

## 项目文件结构

```
src/views/ai/
├── AiPlus.vue          # 主界面组件

src/utils/
├── ai-request.js       # HTTP API工具类
└── websocket.js        # WebSocket管理器

src/router/
└── index.js            # 路由配置 (/ai-plus)

public/
├── config.js           # 配置文件 (aiApiUrl, aiWebSocketUrl)
└── index.html          # HTML模板 (修复资源路径)

vue.config.js           # 代理配置 (/ai-api)
```

## 配置说明

### 代理配置
```javascript
// vue.config.js
proxy: {
  "/ai-api": {
    target: "http://192.168.50.226:8001",
    pathRewrite: { "^/ai-api": "" }
  }
}
```

### 环境配置
```javascript
// public/config.js
window.config = {
  aiApiUrl: 'http://192.168.50.226:8001',
  aiWebSocketUrl: 'ws://192.168.50.226:8001'
};
```

## API接口

### HTTP API
- **历史消息**: `GET /api/v1/conversations/{conversation_id}/messages`
- **请求头**: `user_id: user_67ce21d6-a11c-4340-851b-7a8949906aa3`

### WebSocket API
- **连接地址**: `ws://host:port/ws/chat`
- **查询参数**: `user_id`, `app_id=easy-accounts-assistant`, `use_think_llm=false`
- **消息格式**: `{conversation_id, content}`

## 未来优化方向

### 功能增强
- [ ] 消息搜索功能
- [ ] 对话记录导出
- [ ] 语音输入支持
- [ ] 图片上传功能
- [ ] 多轮对话上下文优化

### 性能优化
- [ ] 消息虚拟滚动（大量历史消息）
- [ ] WebSocket断线重连机制
- [ ] 消息本地缓存策略
- [ ] 网络状态监控

### 体验优化
- [ ] 深色模式支持
- [ ] 字体大小调节
- [ ] 消息复制功能
- [ ] 快捷回复模板

## 开发总结

AI Plus功能从零开始，历经6个开发阶段，成功实现了：

1. **完整的AI对话体验** - 支持实时流式回复和历史记录
2. **智能工具调用** - 财务数据查询和分析功能
3. **现代化UI设计** - 移动优先，符合Material Design
4. **健壮的会话管理** - 自动缓存，支持多轮对话
5. **优秀的开发体验** - 组件化架构，易于维护和扩展

整个项目代码结构清晰，功能模块化，为后续的功能扩展打下了坚实基础。