# VL (Vision-Language) 多模态支持改动方案

> 版本: 1.1
> 创建时间: 2024-12-30
> 更新时间: 2024-12-31
> 状态: ✅ 已实现
>
> **运行流程文档**: [VL 运行流程](../dev-guide/VL_运行流程.md)

## 一、需求概述

支持用户上传图片（如票据、账单截图），由 VL 模型识别后自动记账。

### 1.1 目标场景

1. 用户拍照上传购物小票 → AI 识别金额、商品、日期 → 自动创建流水
2. 用户上传银行账单截图 → AI 批量识别 → 自动创建多条流水
3. 用户发送图片询问 → AI 看图回答问题

### 1.2 技术要求

- 支持 OpenAI VL API 格式（GPT-4V、DeepSeek-VL 等）
- 向后兼容现有纯文本对话
- 最小化代码改动

---

## 二、现有架构分析

### 2.1 VL 模型 API 格式（目标格式）

```json
{
    "model": "moonshot-v1-8k-vision-preview",
    "messages": [
        {
            "role": "system",
            "content": "你是一个智能助手..."
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
                    }
                },
                {
                    "type": "text",
                    "text": "请描述这个图片"
                }
            ]
        }
    ],
    "temperature": 0.3
}
```

**关键点**：
- `content` 从 `string` 变为 `array`
- 数组包含 `image_url` 和 `text` 两种类型
- 图片以 `data:image/png;base64,{base64_data}` 格式内嵌

### 2.2 消息流转路径

```
用户输入 (文本 + 图片)
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  API 层                                                      │
│  ├─ WebSocket: websocket.py                                  │
│  └─ HTTP: conversations.py                                   │
│      接收: {"content": "string", "round_id": "xxx"}          │
│      【需改造】支持 attachments 字段                          │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  执行层                                                      │
│  ├─ AgentExecutor.execute()                                  │
│  └─ ChatProcessor.process_message()                          │
│      message 参数: str                                       │
│      【需改造】新增 attachments 参数                          │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  历史管理层                                                   │
│  └─ HistoryManager                                           │
│      ├─ add_user_message(content: str)                       │
│      │   【需改造】新增 attachments 参数                      │
│      └─ get_history() → [{"role": "user", "content": str}]   │
│          【需改造】content 转为 array 格式                    │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  LLM 客户端层                                                 │
│  └─ EnhancedLLMClient                                        │
│      ├─ block(messages: List[Dict])                          │
│      └─ stream(messages: List[Dict])                         │
│      【无需改造】直接透传 messages                            │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  OpenAI API                                                  │
│  普通: {"role": "user", "content": "string"}                 │
│  VL:   {"role": "user", "content": [                         │
│           {"type": "image_url", "image_url": {"url": "..."}},│
│           {"type": "text", "text": "..."}                    │
│        ]}                                                    │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 关键代码现状

#### Message 模型 (`models/message.py`)

```python
@dataclass
class Message:
    role: str                    # user / assistant / tool
    content: str                 # 【关键】当前是纯字符串
    timestamp: str
    round_id: str
    type: MessageType
    # ... 其他字段
```

**问题**：`content` 是 `str` 类型，无法存储 VL 格式的数组内容。

#### HistoryManager (`core/history_manager.py`)

```python
def add_user_message(self, agent, user_id, conversation_id, round_id, content: str):
    """content 参数是 str 类型"""
    message = Message.create_user_message(content, round_id)
    # ...

def get_history(self, agent, user_id, conversation_id) -> List[Dict]:
    """返回的 content 是 str"""
    for msg in messages:
        if msg.type == MessageType.CONTENT:
            result.append({
                "role": msg.role,
                "content": msg.content  # str
            })
```

**问题**：整个链路都假设 `content` 是字符串。

#### EnhancedLLMClient (`core/llm/enhanced_llm_client.py`)

```python
async def _make_request(self, messages: List[Dict], ...):
    """直接透传 messages 给 OpenAI API"""
    response = await self.client.chat.completions.create(
        model=self.llm.model,
        messages=messages,  # 透传
        # ...
    )
```

**现状**：LLM 客户端本身已支持透传任意格式的 messages，无需改动。

#### 数据库 messages 表

```sql
CREATE TABLE messages (
    message_id INTEGER PRIMARY KEY,
    round_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT,           -- 【关键】TEXT 类型
    type TEXT NOT NULL,
    -- ...
);
```

**问题**：`content` 是 TEXT，存储 JSON 数组需要序列化。

---

## 三、改造难度评估

### 3.1 难度矩阵

| 模块 | 改动范围 | 难度 | 风险 |
|------|----------|------|------|
| Message 模型 | 新增字段 | ⭐ 低 | 低 |
| HistoryManager | 多处方法签名 | ⭐⭐⭐ 中高 | 中 |
| ChatProcessor | 参数传递 | ⭐⭐ 中 | 低 |
| LLM Client | 几乎无需改动 | ⭐ 低 | 低 |
| 数据库 | 新增字段 | ⭐ 低 | 低 |
| API 层 | 新增请求格式 | ⭐⭐ 中 | 低 |
| 前端 | 图片上传组件 | ⭐⭐⭐ 中高 | 低 |

### 3.2 主要挑战

1. **向后兼容**：历史消息都是纯文本，新代码需要兼容两种格式
2. **存储策略**：图片 Base64 很大（1MB 图片 ≈ 1.3MB Base64），是否单独存储
3. **历史构建**：`get_history()` 需要正确构建 VL 格式的消息
4. **Token 计算**：VL 模型的图片 Token 计算方式不同（按图片尺寸）

---

## 四、设计方案

### 4.1 方案对比

| 方案 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| A. 修改 content 类型 | `content: Union[str, List]` | 符合 OpenAI 格式 | 改动大，历史兼容复杂 |
| B. 新增 attachments 字段 | 保持 content: str，新增图片字段 | 改动小，向后兼容 | 构建历史时需转换 |
| C. 独立 VL 消息类型 | 新增 MessageType.VL_CONTENT | 类型清晰 | 代码分支多 |

**推荐方案**：**方案 B - 新增 attachments 字段**

### 4.2 详细设计

#### 4.2.1 数据模型改动

**新增 Attachment 模型** (`models/message.py`)

```python
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Attachment:
    """消息附件（图片等）"""
    type: str           # "image"
    media_type: str     # "image/jpeg", "image/png"
    data: str           # Base64 编码的图片数据
    # 可选：存储到文件系统后的路径
    file_path: Optional[str] = None
    # 原始文件名
    filename: Optional[str] = None
    # 图片尺寸（用于 Token 计算）
    width: Optional[int] = None
    height: Optional[int] = None


@dataclass
class Message:
    role: str
    content: str                 # 保持不变，存储文本部分
    timestamp: str
    round_id: str
    type: MessageType

    # 【新增】附件列表
    attachments: List[Attachment] = field(default_factory=list)

    # ... 其他字段保持不变

    def has_attachments(self) -> bool:
        """是否包含附件"""
        return len(self.attachments) > 0

    def to_llm_content(self) -> Union[str, List[Dict]]:
        """转换为 LLM API 需要的 content 格式"""
        if not self.attachments:
            return self.content

        # VL 格式
        result = []
        if self.content:
            result.append({"type": "text", "text": self.content})

        for att in self.attachments:
            if att.type == "image":
                result.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{att.media_type};base64,{att.data}"
                    }
                })

        return result
```

**工厂方法扩展**

```python
@staticmethod
def create_user_message(
    content: str,
    round_id: str,
    attachments: List[Attachment] = None
) -> "Message":
    """创建用户消息（支持附件）"""
    return Message(
        role="user",
        content=content,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        round_id=round_id,
        type=MessageType.CONTENT,
        attachments=attachments or []
    )
```

#### 4.2.2 数据库改动

**新增 attachments 字段**

```sql
-- 方案 A：在 messages 表新增字段
ALTER TABLE messages ADD COLUMN attachments TEXT DEFAULT '[]';

-- 方案 B（推荐）：新建附件表，支持大文件单独存储
CREATE TABLE message_attachments (
    attachment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    type TEXT NOT NULL,           -- "image"
    media_type TEXT NOT NULL,     -- "image/jpeg"
    data TEXT,                    -- Base64 数据（小图片）
    file_path TEXT,               -- 文件路径（大图片存文件系统）
    filename TEXT,
    width INTEGER,
    height INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (message_id) REFERENCES messages(message_id)
);
```

**存储策略**

| 图片大小 | 存储方式 |
|----------|----------|
| < 100KB | Base64 存入 `data` 字段 |
| >= 100KB | 存文件系统，`file_path` 存路径 |

#### 4.2.3 HistoryManager 改动

```python
def add_user_message(
    self,
    agent,
    user_id,
    conversation_id,
    round_id,
    content: str,
    attachments: List[Attachment] = None  # 【新增】
):
    """添加用户消息（支持附件）"""
    message = Message.create_user_message(
        content=content,
        round_id=round_id,
        attachments=attachments
    )

    # 存入内存
    self.histories[user_id][conversation_id]["rounds"][round_id].append(message)

    # 存入数据库
    self.sqlite_storage.add_message(round_id, message)

    # 【新增】存储附件
    if attachments:
        self.sqlite_storage.save_attachments(message.message_id, attachments)


def get_history(self, agent, user_id, conversation_id) -> List[Dict]:
    """构建 LLM 历史（支持 VL 格式）"""
    result = []

    # 添加 system message
    result.append({
        "role": "system",
        "content": agent.system_prompt
    })

    # 遍历消息
    for msg in messages:
        if msg.type == MessageType.CONTENT:
            result.append({
                "role": msg.role,
                "content": msg.to_llm_content()  # 【改动】使用转换方法
            })
        # ... 其他类型保持不变

    return result
```

#### 4.2.4 ChatProcessor 改动

```python
async def process_message(
    self,
    agent: Agent,
    message: str,
    conversation_id: str,
    user_id: str,
    round_id: str,
    attachments: List[Attachment] = None  # 【新增】
):
    """处理用户消息（支持附件）"""

    # 添加用户消息
    self.history_manager.add_user_message(
        agent, user_id, conversation_id, round_id,
        content=message,
        attachments=attachments  # 【新增】
    )

    # ... 后续流程不变
```

#### 4.2.5 API 层改动

**WebSocket 消息格式扩展**

```python
# 现有格式
{
    "type": "chat",
    "data": {
        "content": "帮我记一笔账",
        "round_id": "round_xxx"
    }
}

# VL 格式（新增）
{
    "type": "chat",
    "data": {
        "content": "识别这张小票",
        "round_id": "round_xxx",
        "attachments": [
            {
                "type": "image",
                "media_type": "image/jpeg",
                "data": "/9j/4AAQSkZJRg..."  # Base64
            }
        ]
    }
}
```

**HTTP 端点扩展**

```python
# api/endpoints/chat.py

class ChatRequest(BaseModel):
    content: str
    conversation_id: str
    round_id: Optional[str] = None
    # 【新增】
    attachments: Optional[List[AttachmentInput]] = None

class AttachmentInput(BaseModel):
    type: str = "image"
    media_type: str
    data: str  # Base64
```

#### 4.2.6 前端改动

**图片上传组件**

```vue
<template>
  <div class="chat-input">
    <!-- 图片预览 -->
    <div v-if="attachments.length" class="attachments-preview">
      <div v-for="(att, idx) in attachments" :key="idx" class="attachment-item">
        <img :src="`data:${att.media_type};base64,${att.data}`" />
        <button @click="removeAttachment(idx)">×</button>
      </div>
    </div>

    <!-- 输入区 -->
    <input type="text" v-model="message" />
    <button @click="selectImage">📷</button>
    <button @click="send">发送</button>

    <input type="file" ref="fileInput" accept="image/*" @change="onFileSelect" hidden />
  </div>
</template>

<script>
export default {
  data() {
    return {
      message: '',
      attachments: []
    }
  },
  methods: {
    selectImage() {
      this.$refs.fileInput.click()
    },
    async onFileSelect(e) {
      const file = e.target.files[0]
      if (!file) return

      // 转 Base64
      const base64 = await this.fileToBase64(file)

      this.attachments.push({
        type: 'image',
        media_type: file.type,
        data: base64.split(',')[1]  // 去掉 data:xxx;base64, 前缀
      })
    },
    fileToBase64(file) {
      return new Promise((resolve) => {
        const reader = new FileReader()
        reader.onload = () => resolve(reader.result)
        reader.readAsDataURL(file)
      })
    },
    send() {
      this.$emit('send', {
        content: this.message,
        attachments: this.attachments
      })
      this.message = ''
      this.attachments = []
    }
  }
}
</script>
```

---

## 五、实施计划

### 5.1 分阶段实施

| 阶段 | 任务 | 预估改动量 |
|------|------|------------|
| Phase 1 | 数据模型 + 数据库 | 2 个文件 |
| Phase 2 | HistoryManager 改造 | 1 个文件，~50 行 |
| Phase 3 | ChatProcessor 改造 | 3 个文件，~30 行 |
| Phase 4 | API 层改造 | 2 个文件，~50 行 |
| Phase 5 | 前端改造 | 2-3 个组件 |
| Phase 6 | 测试 + 调试 | - |

### 5.2 文件改动清单

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `models/message.py` | 修改 | 新增 Attachment 类，扩展 Message |
| `database/base/database_connection.py` | 修改 | 新增 attachments 表 |
| `database/repositories/message_repository.py` | 修改 | 附件存取方法 |
| `core/history_manager.py` | 修改 | add_user_message、get_history |
| `core/chat/base_chat_processor.py` | 修改 | process_message 参数 |
| `core/chat/http_chat_processor.py` | 修改 | 参数透传 |
| `core/chat/websocket_chat_processor.py` | 修改 | 参数透传 |
| `core/websocket_handler.py` | 修改 | 解析附件 |
| `api/endpoints/chat.py` | 修改 | 请求模型 |
| `api/models/frontend_message.py` | 修改 | 前端消息格式 |

---

## 六、兼容性考虑

### 6.1 向后兼容

| 场景 | 处理方式 |
|------|----------|
| 旧消息（无附件） | `attachments = []`，`to_llm_content()` 返回 str |
| 新消息（有附件） | `attachments` 有值，`to_llm_content()` 返回 List |
| 旧客户端 | 不发送 attachments 字段，正常工作 |
| 新客户端 | 可选发送 attachments |

### 6.2 数据库迁移

```python
# database/migrations/add_attachments.py

def upgrade(connection):
    """添加附件支持"""
    connection.execute("""
        CREATE TABLE IF NOT EXISTS message_attachments (
            attachment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            media_type TEXT NOT NULL,
            data TEXT,
            file_path TEXT,
            filename TEXT,
            width INTEGER,
            height INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (message_id) REFERENCES messages(message_id)
        )
    """)
    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_attachments_message
        ON message_attachments(message_id)
    """)

def downgrade(connection):
    """回滚"""
    connection.execute("DROP TABLE IF EXISTS message_attachments")
```

---

## 七、Token 计算

### 7.1 VL 模型图片 Token 估算

不同模型的图片 Token 计算方式不同：

| 模型 | 计算方式 |
|------|----------|
| GPT-4V | 低分辨率: 85 tokens，高分辨率: 按 512x512 块计算 |
| Claude 3 | 图片大小 / 750 bytes ≈ tokens |
| DeepSeek-VL | 与 GPT-4V 类似 |

### 7.2 实现建议

```python
def estimate_image_tokens(width: int, height: int, detail: str = "auto") -> int:
    """估算图片 Token 数"""
    if detail == "low":
        return 85

    # 高分辨率模式
    # 1. 缩放到 2048x2048 以内
    max_dim = max(width, height)
    if max_dim > 2048:
        scale = 2048 / max_dim
        width = int(width * scale)
        height = int(height * scale)

    # 2. 缩放短边到 768
    min_dim = min(width, height)
    if min_dim > 768:
        scale = 768 / min_dim
        width = int(width * scale)
        height = int(height * scale)

    # 3. 计算 512x512 块数
    tiles = (width // 512 + 1) * (height // 512 + 1)

    return 85 + 170 * tiles
```

---

## 八、安全考虑

### 8.1 图片验证

```python
def validate_image(data: str, media_type: str) -> bool:
    """验证图片安全性"""
    # 1. 检查 media_type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if media_type not in allowed_types:
        return False

    # 2. 检查 Base64 大小（限制 10MB）
    max_size = 10 * 1024 * 1024
    if len(data) * 3 / 4 > max_size:
        return False

    # 3. 验证是真实图片（解码测试）
    try:
        import base64
        from PIL import Image
        from io import BytesIO

        img_data = base64.b64decode(data)
        img = Image.open(BytesIO(img_data))
        img.verify()
        return True
    except:
        return False
```

### 8.2 存储安全

- 图片文件存储在独立目录，不可直接 URL 访问
- 通过 API 中转访问，验证用户权限
- 定期清理孤立附件（消息已删除的附件）

---

## 九、测试计划

### 9.1 单元测试

```python
# tests/test_vl_message.py

def test_message_without_attachments():
    """测试无附件消息"""
    msg = Message.create_user_message("hello", "round_1")
    assert msg.to_llm_content() == "hello"

def test_message_with_image():
    """测试带图片消息"""
    att = Attachment(type="image", media_type="image/jpeg", data="abc123")
    msg = Message.create_user_message("识别这张图", "round_1", attachments=[att])

    content = msg.to_llm_content()
    assert isinstance(content, list)
    assert content[0] == {"type": "text", "text": "识别这张图"}
    assert content[1]["type"] == "image_url"

def test_history_with_vl():
    """测试 VL 历史构建"""
    # ...
```

### 9.2 集成测试

1. 上传图片 → 存储 → 读取 → 验证一致性
2. 发送 VL 消息 → LLM 调用 → 验证响应
3. 混合对话（文本 + 图片）→ 历史正确构建

---

## 十、总结

### 10.1 推荐方案

采用 **方案 B：新增 attachments 字段**

- **优点**：改动最小，向后兼容，风险低
- **核心思路**：`Message.content` 保持 str，新增 `attachments` 存储图片，`to_llm_content()` 负责格式转换

### 10.2 预估工作量

| 项目 | 预估 |
|------|------|
| 后端改动 | 10 个文件，~300 行代码 |
| 前端改动 | 2-3 个组件，~200 行代码 |
| 测试 | ~100 行测试代码 |
| 总计 | 约 2-3 天开发时间 |

### 10.3 后续扩展

- 支持多图上传
- 支持视频（未来 VL 模型可能支持）
- 支持文件（PDF 等）
- OCR 预处理优化（降低 Token 消耗）
