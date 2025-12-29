# Token 管理模块文档

> 版本: 1.0
> 更新时间: 2025-12-08
> 状态: 正式版

## 一、概述

Token 管理模块负责统计和追踪 LLM 调用的 Token 消耗，支持**多层级累加**和**多维度统计**。

> **关联文档**：
> - [数据库架构](./database_数据库架构.md) - Token 相关表结构
> - [消息管理](./message_消息管理.md) - 消息级 Token 记录
> - [功能模块开发](./function_功能模块开发.md) - 总结功能的 Token 追踪

### 设计目标

1. **精确追踪**：记录每次 LLM 调用的 Token 消耗
2. **多层级累加**：从消息到用户的层级汇总
3. **多维度统计**：按用户、对话、模型等维度分析
4. **支持 4 种 Token 类型**：total / prompt / completion / reasoning

---

## 二、Token 数据结构

### 2.1 TokenUsage

**文件**: `core/llm/enhanced_llm_client.py`

```python
@dataclass
class TokenUsage:
    """Token使用情况"""
    total_tokens: int          # 总 Token 数
    prompt_tokens: int = 0     # 提示词 Token
    completion_tokens: int = 0 # 回复 Token
    reasoning_tokens: int = 0  # 推理 Token（思维链模型）
```

### 2.2 Token 类型说明

| 类型 | 说明 | 来源 |
|------|------|------|
| total_tokens | 总消耗 | = prompt + completion + reasoning |
| prompt_tokens | 输入消耗 | 系统提示词 + 历史消息 + 用户输入 |
| completion_tokens | 输出消耗 | LLM 生成的回复内容 |
| reasoning_tokens | 推理消耗 | 思维链模型的内部推理（如 DeepSeek R1） |

---

## 三、多层级统计架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                           LLM 调用                                   │
│                    EnhancedLLMClient.stream/block                   │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │ 返回 LLMResponse (含 TokenUsage)
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         TokenManager                                 │
│                      add_tokens(token_usage, ...)                   │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  models 表      │     │   users 表      │     │ conversations 表│
│  (模型维度)     │     │   (用户维度)    │     │   (对话维度)    │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                              ┌──────────┴──────────┐
                                              ▼                     ▼
                                    ┌─────────────────┐   ┌─────────────────┐
                                    │   rounds 表     │   │ summary_log 表  │
                                    │   (轮次维度)    │   │   (总结维度)    │
                                    └────────┬────────┘   └─────────────────┘
                                             │
                                             ▼
                                    ┌─────────────────┐
                                    │  messages 表    │
                                    │   (消息维度)    │
                                    └─────────────────┘
```

### 层级关系

```
用户 (users)
  └─→ 对话 (conversations)
        └─→ 轮次 (rounds)
              └─→ 消息 (messages)

模型 (models) ← 独立维度，按 platform + model 聚合
总结 (summary_log) ← 独立维度，记录总结操作的 Token
```

---

## 四、TokenManager 核心类

**文件**: `core/token_manager.py`

### 4.1 初始化

```python
class TokenManager:
    def __init__(self, repository_adapter: RepositoryAdapter):
        self.repository_adapter = repository_adapter
        self.logger = ManagerLogger("TokenManager")
```

### 4.2 核心方法

#### add_tokens - 多层级累加

```python
def add_tokens(self,
               token_usage: TokenUsage,
               llm: Optional[LLM] = None,
               operation_type: str = "chat",  # chat / summary / auto_question
               user_id: str = None,
               conversation_id: str = None,
               round_id: str = None,
               message_id: int = None,
               summary_id: int = None):
    """
    将 Token 添加到完整的层级结构中

    累加逻辑：
    1. models 表 - 所有调用都累加
    2. users 表 - 所有调用都累加
    3. conversations 表 - 有 conversation_id 时累加
    4. 根据 operation_type 分支：
       - chat: 累加到 rounds + messages
       - summary: 累加到 summary_log
       - auto_question: 不累加（只记录到 models 和 users）
    """
```

#### add_tokens_to_model - 模型维度

```python
def add_tokens_to_model(self, token_usage: TokenUsage, llm: LLM, operation_type: str):
    """
    记录 Token 到模型统计表

    流程：
    1. 从 LLM 对象获取 platform 和 model
    2. 调用 repository_adapter.add_tokens_to_model()
    3. 累加到 models 表的统计字段
    """
```

### 4.3 统计查询

```python
def get_model_statistics(self):
    """获取按模型分组的统计"""
    return self.repository_adapter.get_model_statistics()

def get_platform_statistics(self):
    """获取按平台分组的统计"""
    return self.repository_adapter.get_platform_statistics()

def get_current_platform_and_model_info(self, llm: LLM, operation_type: str):
    """获取当前使用的平台和模型详细信息"""
```

---

## 五、调用场景

### 5.1 对话消息 (chat)

**调用位置**: `HistoryManager.add_assistant_message()`

```python
# history_manager.py
def add_assistant_message(self, ..., token_usage: TokenUsage = None):
    # 保存消息
    message_id = self.sqlite_storage.add_message(round_id, db_message)

    # Token 统计
    if token_usage and token_usage.total_tokens > 0:
        self.token_manager.add_tokens(
            token_usage=token_usage,
            llm=agent.get_llm_for_mode(),
            operation_type="chat",
            conversation_id=conversation_id,
            round_id=round_id,
            message_id=message_id,
            user_id=user_id
        )
```

**累加目标**：
- ✅ models 表
- ✅ users 表
- ✅ conversations 表
- ✅ rounds 表
- ✅ messages 表

### 5.2 总结功能 (summary)

**调用位置**: `SummaryManager.update_summary_log_with_token_tracking()`

```python
# summary_manager.py
def update_summary_log_with_token_tracking(self, agent, log_id, summary_result,
                                           token_usage, execution_time, user_id,
                                           conversation_id):
    # 更新日志状态
    self.sqlite_storage.update_summary_log(log_id, summary_result, "success", ...)

    # Token 统计
    self.token_manager.add_tokens(
        token_usage=token_usage,
        llm=agent.summary_llm,
        operation_type="summary",
        conversation_id=conversation_id,
        summary_id=log_id,
        user_id=user_id
    )
```

**累加目标**：
- ✅ models 表
- ✅ users 表
- ✅ conversations 表
- ✅ summary_log 表
- ❌ rounds 表（总结不属于轮次）
- ❌ messages 表（总结不产生消息）

### 5.3 自动问题 (auto_question)

**调用位置**: `AutoQuestionManager.generate_auto_question()`

```python
# auto_question_manager.py
async def generate_auto_question(self, ...):
    # Token 统计
    if self.token_manager and user_id:
        self.token_manager.add_tokens(
            token_usage=token_usage,
            llm=agent.summary_llm,
            operation_type="auto_question",
            conversation_id=conversation_id,
            user_id=user_id
        )
```

**累加目标**：
- ✅ models 表
- ✅ users 表
- ❌ conversations 表（自动问题是辅助功能）
- ❌ 其他表

---

## 六、数据库表 Token 字段

> 详见 [数据库架构](./database_数据库架构.md)

### 6.1 涉及的表

| 表名 | Token 字段 | 说明 |
|------|------------|------|
| users | total/prompt/completion/reasoning_tokens | 用户累计消耗 |
| conversations | total/prompt/completion/reasoning_tokens | 对话累计消耗 |
| rounds | total/prompt/completion/reasoning_tokens | 轮次累计消耗 |
| messages | total/prompt/completion/reasoning_tokens | 单条消息消耗 |
| summary_log | total/prompt/completion/reasoning_tokens | 总结操作消耗 |
| models | total/prompt/completion/reasoning_tokens | 模型累计消耗 |

### 6.2 RepositoryAdapter 方法

```python
# 用户级
add_tokens_to_user(user_id, token_usage)

# 对话级
add_tokens_to_conversation(conversation_id, token_usage)

# 轮次级
add_tokens_to_round(round_id, token_usage)

# 消息级
add_tokens_to_message(message_id, token_usage, platform, model)

# 总结级
add_tokens_to_summary(summary_id, token_usage)

# 模型级
add_tokens_to_model(platform, model, token_usage)
```

---

## 七、Token 流转流程

### 7.1 对话消息流程

```
用户发送消息
    │
    ▼
LLM 调用 (EnhancedLLMClient.stream)
    │
    ├─→ 流式返回 chunk
    │
    └─→ 最终返回 LLMResponse
            │
            └─→ token_usage: TokenUsage(
                    total_tokens=1500,
                    prompt_tokens=1200,
                    completion_tokens=300,
                    reasoning_tokens=0
                )
    │
    ▼
HistoryManager.add_assistant_message()
    │
    └─→ TokenManager.add_tokens(
            token_usage=token_usage,
            operation_type="chat",
            user_id="user_123",
            conversation_id="conv_456",
            round_id="round_789",
            message_id=42
        )
    │
    ▼
┌─────────────────────────────────────────┐
│ 并行累加到各层级                         │
├─────────────────────────────────────────┤
│ models: platform=deepseek, model=v3     │
│ users: user_id=user_123                 │
│ conversations: conversation_id=conv_456│
│ rounds: round_id=round_789              │
│ messages: message_id=42                 │
└─────────────────────────────────────────┘
```

### 7.2 总结功能流程

```
轮次结束 (on_round_end)
    │
    ▼
SummaryManager.summarize_round()
    │
    ├─→ 创建 summary_log 记录 (status=pending)
    │
    ├─→ LLM 调用 (使用 summary_llm)
    │       └─→ 返回 token_usage
    │
    └─→ update_summary_log_with_token_tracking()
            │
            └─→ TokenManager.add_tokens(
                    token_usage=token_usage,
                    operation_type="summary",
                    summary_id=log_id
                )
    │
    ▼
┌─────────────────────────────────────────┐
│ 累加到：                                 │
│ - models 表                             │
│ - users 表                              │
│ - conversations 表                      │
│ - summary_log 表                        │
└─────────────────────────────────────────┘
```

---

## 八、统计查询示例

### 8.1 模型统计

```python
# 按模型分组统计
stats = token_manager.get_model_statistics()

# 返回示例：
[
    {
        "platform": "deepseek",
        "model": "deepseek-chat-v3",
        "total_tokens": 1500000,
        "prompt_tokens": 1000000,
        "completion_tokens": 450000,
        "reasoning_tokens": 50000,
        "request_count": 1000,
        "success_count": 990,
        "error_count": 10
    },
    ...
]
```

### 8.2 平台统计

```python
# 按平台分组统计
stats = token_manager.get_platform_statistics()

# 返回示例：
[
    {
        "platform": "deepseek",
        "total_tokens": 2000000,
        "request_count": 1500
    },
    {
        "platform": "tongyi",
        "total_tokens": 500000,
        "request_count": 300
    }
]
```

### 8.3 用户统计

```python
# 从 UserRepository 获取
user_stats = repository_adapter.get_user_token_stats(user_id)

# 返回示例：
{
    "user_id": "user_123",
    "total_tokens": 50000,
    "prompt_tokens": 35000,
    "completion_tokens": 14000,
    "reasoning_tokens": 1000,
    "conversation_count": 20,
    "message_count": 150
}
```

---

## 九、配置与扩展

### 9.1 LLM 配置

Token 统计依赖 LLM 配置来确定 platform 和 model：

```ini
# llm_config.ini
[deepseek-v3]
platform = deepseek
model = deepseek-chat-v3
api_key = xxx
url = https://api.deepseek.com/v1
```

### 9.2 扩展新的 operation_type

如需添加新的操作类型：

```python
# token_manager.py
def add_tokens(self, ..., operation_type: str = "chat"):
    ...
    elif operation_type == "my_new_operation":
        # 自定义累加逻辑
        if my_id:
            self.repository_adapter.add_tokens_to_my_table(my_id, token_usage)
    ...
```

---

## 十、文件位置索引

| 组件 | 文件路径 |
|------|----------|
| TokenManager | `koalaq_hub/core/token_manager.py` |
| TokenUsage | `koalaq_hub/core/llm/enhanced_llm_client.py` |
| RepositoryAdapter | `koalaq_hub/database/repository_adapter.py` |
| UserRepository | `koalaq_hub/database/repositories/user_repository.py` |
| ConversationRepository | `koalaq_hub/database/repositories/conversation_repository.py` |
| MessageRepository | `koalaq_hub/database/repositories/message_repository.py` |
| SummaryRepository | `koalaq_hub/database/repositories/summary_repository.py` |
| TokenRepository | `koalaq_hub/database/repositories/token_repository.py` |

---

## 十一、关键设计决策

### 11.1 累加而非覆盖

所有 Token 操作都是**累加**：

```sql
UPDATE users SET total_tokens = total_tokens + ? WHERE user_id = ?
```

### 11.2 4 种 Token 类型

完整支持现代 LLM 的 Token 分类：
- `prompt_tokens`：输入消耗
- `completion_tokens`：输出消耗
- `reasoning_tokens`：思维链消耗（新增）
- `total_tokens`：总和

### 11.3 operation_type 分支

不同操作类型有不同的累加目标：
- `chat`：完整层级（消息→轮次→对话→用户→模型）
- `summary`：总结层级（summary_log→对话→用户→模型）
- `auto_question`：简化层级（用户→模型）

### 11.4 LLM 动态传入

TokenManager 不持有 LLM 配置，而是每次调用时动态传入：

```python
# 支持不同场景使用不同的 LLM
token_manager.add_tokens(token_usage, llm=agent.main_llm, ...)    # 对话用主模型
token_manager.add_tokens(token_usage, llm=agent.summary_llm, ...) # 总结用总结模型
```
