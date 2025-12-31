# VL (Vision-Language) 运行流程

> 版本: 1.0
> 更新时间: 2024-12-31
> 状态: 正式版

## 一、概述

VL (Vision-Language) 支持用户发送图片消息，由多模态 LLM 识别图片内容并回复。

### 1.1 功能特点

- 支持 OpenAI VL API 格式（GPT-4V、DeepSeek-VL、Moonshot-VL 等）
- 图片通过 EasyAccounts 文件服务中转，前端只发送 filename
- 后端自动下载图片并转换为 base64
- 向后兼容纯文本对话

### 1.2 关联文档

- [消息管理](./message_消息管理.md) - 消息模型和历史管理
- [WebSocket 运行流程](./websocket_运行流程.md) - WebSocket 消息格式
- [数据库架构](./database_数据库架构.md) - messages 表结构
- [VL 改动方案](../feature-guide/VL_改动方案.md) - 原始设计文档

---

## 二、数据流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              VL 消息数据流                                   │
└─────────────────────────────────────────────────────────────────────────────┘

前端                                                              EasyAccounts
  │                                                                    │
  │ 1. 上传图片 ───────────────────────────────────────────────────────>│
  │<─────────────────────────────────────────────── 返回 filename ─────│
  │                                                                    │
  │ 2. 发送消息 (content + attachments: [{filename}])                  │
  │                                                                    │
  ▼                                                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│  WebSocket 端点 (websocket.py)                                              │
│  ├─ 解析 attachments: [{filename: "xxx.png"}]                               │
│  └─ 调用 image_service.convert_attachments()                                │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 │ 3. 下载图片
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  ImageService (image_service.py)                                            │
│  ├─ GET {EASYACCOUNTS_URL}/image/{filename}                                 │
│  ├─ 转换为 base64                                                           │
│  └─ 返回 List[Attachment]                                                   │
│      Attachment: {filename, data(base64), media_type}                       │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  AgentExecutor / ChatProcessor                                              │
│  └─ 传递 attachments 参数                                                   │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  HistoryManager                                                             │
│  ├─ add_user_message(content, attachments)                                  │
│  │   └─ Message.create_user_message(content, round_id, attachments)         │
│  │                                                                          │
│  └─ get_history()                                                           │
│      └─ msg.to_llm_content()  ──────────────────────────────────────────────┤
│          ├─ 无附件: 返回 "string"                                           │
│          └─ 有附件: 返回 VL 格式数组                                         │
│              [                                                              │
│                {"type": "image_url", "image_url": {"url": "data:..."}},     │
│                {"type": "text", "text": "用户消息"}                          │
│              ]                                                              │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  EnhancedLLMClient (透传)                                                   │
│  └─ messages 直接发送给 OpenAI API，无需特殊处理                             │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  MessageRepository (数据库存储)                                              │
│  ├─ 存储: attachments 序列化为 JSON 字符串                                   │
│  └─ 读取: JSON 反序列化为 List[Attachment]                                  │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  ConversationManager (前端查询)                                              │
│  └─ FrontendMessage.attachments = [filename1, filename2, ...]               │
│      只返回文件名，不返回 base64 数据                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 三、Attachment 数据模型

### 3.1 Attachment 类

**文件**: `models/message.py`

```python
@dataclass
class Attachment:
    """VL 附件数据类（图片等）

    Attributes:
        filename: 文件名（用于前端展示和从文件服务获取）
        data: base64 编码的文件数据（用于 LLM 调用）
        media_type: MIME 类型，如 "image/png", "image/jpeg"
    """
    filename: str
    data: str  # base64 编码
    media_type: str = "image/png"

    def to_dict(self) -> Dict[str, str]:
        """转换为字典（用于数据库存储）"""
        return {
            "filename": self.filename,
            "data": self.data,
            "media_type": self.media_type
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "Attachment":
        """从字典创建（用于数据库读取）"""
        return cls(
            filename=data.get("filename", ""),
            data=data.get("data", ""),
            media_type=data.get("media_type", "image/png")
        )

    def to_llm_format(self) -> Dict[str, Any]:
        """转换为 LLM VL API 格式"""
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:{self.media_type};base64,{self.data}"
            }
        }
```

### 3.2 Message 扩展

```python
@dataclass
class Message:
    # ... 其他字段 ...

    # VL 附件（图片等）
    attachments: Optional[List[Attachment]] = None

    def to_llm_content(self):
        """转换为 LLM API 需要的 content 格式

        Returns:
            str: 纯文本消息
            List[Dict]: VL 格式（有附件时）
        """
        if not self.attachments:
            return self.content

        # VL 格式：content 是数组
        result = []

        # 先添加图片
        for att in self.attachments:
            result.append(att.to_llm_format())

        # 再添加文本
        if self.content:
            result.append({"type": "text", "text": self.content})

        return result
```

---

## 四、WebSocket 接收附件

### 4.1 消息格式

**文件**: `api/endpoints/websocket.py`

客户端发送：

```json
{
  "conversation_id": "conv_123",
  "content": "请识别这张图片",
  "attachments": [
    {"filename": "receipt_001.png"},
    {"filename": "receipt_002.jpg"}
  ]
}
```

### 4.2 处理流程

```python
# websocket.py
async def websocket_chat_handler(websocket: WebSocket):
    # ...

    # 解析消息
    data = json.loads(message)
    content = data.get("content")
    raw_attachments = data.get("attachments")  # [{filename: "xxx.png"}]

    # 转换附件：从 filename 下载图片并转为 base64
    attachments = None
    if raw_attachments:
        attachments = await convert_attachments(raw_attachments)
        logger.info("附件转换完成", {"count": len(attachments)})

    # 执行 Agent
    await agent_executor.execute(
        agent=agent,
        message=content,
        conversation_id=conversation_id,
        user_id=user_id,
        source='websocket',
        attachments=attachments  # List[Attachment]
    )
```

---

## 五、图片下载服务

### 5.1 ImageService

**文件**: `core/image_service.py`

```python
# 从环境变量获取 EasyAccounts URL
EASYACCOUNTS_URL = os.getenv("EASYACCOUNTS_URL", "http://localhost:8081")

async def fetch_image_as_base64(filename: str, token: str = None) -> Optional[Attachment]:
    """从 EasyAccounts 下载图片并转换为 base64

    Args:
        filename: 图片文件名
        token: 用户认证 token（可选）

    Returns:
        Attachment 对象，失败返回 None
    """
    url = f"{EASYACCOUNTS_URL}/image/{filename}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)

        if response.status_code != 200:
            return None

        # 获取 MIME 类型
        content_type = response.headers.get("content-type", "image/png")
        media_type = content_type.split(";")[0].strip()

        # 转换为 base64
        image_data = base64.b64encode(response.content).decode("utf-8")

        return Attachment(
            filename=filename,
            data=image_data,
            media_type=media_type
        )


async def convert_attachments(
    raw_attachments: List[dict],
    token: str = None
) -> List[Attachment]:
    """批量转换附件

    Args:
        raw_attachments: 原始附件列表，格式 [{filename: "xxx.png"}, ...]
        token: 用户认证 token（可选）

    Returns:
        Attachment 对象列表
    """
    result = []
    for raw in raw_attachments:
        filename = raw.get("filename")
        if filename:
            attachment = await fetch_image_as_base64(filename, token)
            if attachment:
                result.append(attachment)
    return result
```

---

## 六、历史管理

### 6.1 保存用户消息

**文件**: `core/history_manager.py`

```python
def add_user_message(self, agent: Agent, user_id: str,
                    conversation_id: str, round_id: str, content: str,
                    attachments: Optional[List[Attachment]] = None):
    """添加用户消息

    Args:
        attachments: VL 附件列表（Attachment 对象）
    """
    # 创建消息（包含附件）
    message = Message.create_user_message(content, round_id, attachments=attachments)

    # 存入内存缓存
    self.histories[user_id][conversation_id]["rounds"][round_id].append(message)

    # 存入数据库
    self.sqlite_storage.add_message(round_id, message)
```

### 6.2 构建 LLM 历史

```python
def get_history(self, agent: Agent, user_id: str, conversation_id: str) -> List[Dict]:
    """构建 LLM 历史"""
    result = []

    # ...

    for msg in messages:
        if msg.type == MessageType.CONTENT:
            # 对于用户消息，使用 to_llm_content() 处理 VL 附件
            if msg.role == "user":
                result.append({"role": msg.role, "content": msg.to_llm_content()})
            else:
                result.append({"role": msg.role, "content": msg.content})

    return result
```

---

## 七、数据库存储

### 7.1 表结构

**文件**: `database/base/database_connection.py`

messages 表新增字段：

```sql
CREATE TABLE IF NOT EXISTS messages (
    -- ... 其他字段 ...
    attachments TEXT DEFAULT ''  -- VL 附件 JSON 数组
)
```

### 7.2 数据库迁移

```python
# _init_tables() 中的迁移逻辑
migrations = [
    ("messages", "attachments", "TEXT DEFAULT ''"),
]
for table, column, definition in migrations:
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
    except sqlite3.OperationalError:
        pass  # 字段已存在，忽略
```

### 7.3 MessageRepository

**文件**: `database/repositories/message_repository.py`

```python
class MessageRepository:

    def _serialize_attachments(self, message: Message) -> str:
        """序列化 attachments 为 JSON 字符串"""
        if message.attachments:
            return json.dumps([att.to_dict() for att in message.attachments], ensure_ascii=False)
        return ""

    def _parse_message_row(self, row_dict: Dict) -> Dict:
        """解析消息行数据，处理 attachments JSON 反序列化"""
        if "attachments" in row_dict:
            attachments_str = row_dict.get("attachments")
            if attachments_str:
                try:
                    row_dict["attachments"] = json.loads(attachments_str)
                except (json.JSONDecodeError, TypeError):
                    row_dict["attachments"] = None
            else:
                row_dict["attachments"] = None
        return row_dict

    def add_message(self, round_id: str, message: Message) -> int:
        """添加消息（包含 attachments 序列化）"""
        sql = """
            INSERT INTO messages (..., attachments)
            VALUES (..., ?)
        """
        params = (
            # ... 其他参数 ...
            self._serialize_attachments(message),
        )
        return self._execute_insert(sql, params)
```

---

## 八、前端返回格式

### 8.1 FrontendMessage

**文件**: `api/models/frontend_message.py`

```python
class FrontendMessage(BaseModel):
    round_id: str
    message_id: str
    timestamp: str
    role: FrontendMessageRole
    text: Optional[TextContent] = None

    # VL 附件（只返回文件名列表，不返回 base64）
    attachments: Optional[List[str]] = None

    token: Optional[int] = None
    model: Optional[str] = None
    tool: Optional[ToolInfo] = None
    sub_agent: Optional[SubAgentInfo] = None
```

### 8.2 格式转换

**文件**: `core/conversation_manager.py`

```python
def _process_messages_for_frontend(self, raw_messages: List[Message]) -> List[FrontendMessage]:
    """转换为前端格式"""
    for msg in raw_messages:
        if msg.role == "user" and msg.type == MessageType.CONTENT:
            # 提取附件文件名列表（只返回 filename，不返回 base64）
            attachment_filenames = None
            if msg.attachments:
                attachment_filenames = [att.filename for att in msg.attachments]

            fmsg = FrontendMessage(
                # ... 其他字段 ...
                attachments=attachment_filenames,
            )
```

### 8.3 返回示例

```json
{
  "round_id": "round_123",
  "message_id": "456",
  "timestamp": "2024-12-31 10:00:00",
  "role": "user",
  "text": {
    "content": "请识别这张图片",
    "reasoning_content": ""
  },
  "attachments": ["receipt_001.png", "receipt_002.jpg"],
  "token": 150,
  "model": "gpt-4o"
}
```

前端根据 `attachments` 中的文件名，通过 `{EASYACCOUNTS_URL}/image/{filename}` 获取图片显示。

---

## 九、文件位置索引

| 组件 | 文件路径 |
|------|----------|
| Attachment 模型 | `koalaq_hub/models/message.py` |
| ImageService | `koalaq_hub/core/image_service.py` |
| WebSocket 端点 | `koalaq_hub/api/endpoints/websocket.py` |
| HistoryManager | `koalaq_hub/core/history_manager.py` |
| BaseChatProcessor | `koalaq_hub/core/chat/base_chat_processor.py` |
| DatabaseConnection | `koalaq_hub/database/base/database_connection.py` |
| MessageRepository | `koalaq_hub/database/repositories/message_repository.py` |
| FrontendMessage | `koalaq_hub/api/models/frontend_message.py` |
| ConversationManager | `koalaq_hub/core/conversation_manager.py` |

---

## 十、关键设计决策

### 10.1 图片通过 EasyAccounts 中转

- **问题**: 前端直接发送 base64 会导致 WebSocket 消息过大
- **方案**: 前端先上传图片到 EasyAccounts，获取 filename，只发送 filename
- **好处**:
  - WebSocket 消息轻量
  - 图片可复用（不同消息引用同一图片）
  - 前端显示时可直接通过 URL 获取

### 10.2 Attachment 简化结构

- **文档设计**: 7 个字段（含 width/height/file_path 等）
- **实际实现**: 3 个字段（filename, data, media_type）
- **原因**: 当前不需要图片尺寸信息，Token 计算暂未实现

### 10.3 JSON 存储而非独立表

- **文档设计**: 独立的 message_attachments 表
- **实际实现**: JSON 存储在 messages.attachments 字段
- **原因**: 简化实现，附件数量通常较少（1-3 张）

### 10.4 前端只返回 filename

- **问题**: base64 数据量大，返回给前端浪费带宽
- **方案**: FrontendMessage.attachments 只包含 filename 列表
- **前端处理**: 通过 `{EASYACCOUNTS_URL}/image/{filename}` 获取图片

---

## 十一、Prompt Caching 说明

OpenAI 和其他 VL 模型支持 Prompt Caching，自动缓存重复的 prefix 内容（包括图片）：

- 相同图片在多轮对话中会被缓存
- 缓存命中时可节省约 75% 的 Token 费用
- 无需特殊处理，模型自动识别

参考: [OpenAI Prompt Caching](https://platform.openai.com/docs/guides/prompt-caching)
