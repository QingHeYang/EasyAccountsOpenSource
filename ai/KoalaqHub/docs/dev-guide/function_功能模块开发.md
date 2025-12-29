# 功能模块开发文档

> 版本: 1.0
> 更新时间: 2025-12-08
> 状态: 正式版

## 一、概述

KoalaQ Hub 提供了一套**功能模块开发体系**，用于实现系统级的辅助功能。这些功能通过**独立的 LLM 调用**完成，与主对话流程解耦。

### 设计理念

```
功能模块 = 功能提示词(.prompt) + 功能管理器(Manager) + FunctionPromptAssembler
```

- **功能提示词**：定义功能的任务描述和输出格式
- **功能管理器**：封装业务逻辑、LLM 调用、数据处理
- **FunctionPromptAssembler**：加载和格式化提示词

### 现有功能模块

| 模块 | 管理器 | 提示词 | 功能 |
|------|--------|--------|------|
| 轮次总结 | SummaryManager | round_summary.prompt | 总结单轮对话 |
| 快照总结 | SummaryManager | snapshot_summary.prompt | 压缩多轮为快照 |
| 对话总结 | SummaryManager | conversation_summary.prompt | 总结整个对话 |
| 标题生成 | SummaryManager | title_summary.prompt | 生成对话标题 |
| 自动问题 | AutoQuestionManager | auto_question.prompt | 推荐后续问题 |

---

## 二、架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                         触发时机                                     │
│         on_round_end() / generate_auto_question()                   │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      功能管理器层                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────┐        ┌─────────────────────┐            │
│  │   SummaryManager    │        │ AutoQuestionManager │            │
│  ├─────────────────────┤        ├─────────────────────┤            │
│  │ - summarize_round() │        │ - generate_auto_    │            │
│  │ - summarize_snapshot│        │   question()        │            │
│  │ - summarize_conv()  │        │                     │            │
│  │ - generate_title()  │        │                     │            │
│  └──────────┬──────────┘        └──────────┬──────────┘            │
│             │                              │                        │
└─────────────┼──────────────────────────────┼────────────────────────┘
              │                              │
              ▼                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  FunctionPromptAssembler                            │
├─────────────────────────────────────────────────────────────────────┤
│  load_and_format(function_name, **kwargs)                          │
│    │                                                                │
│    ├─→ _load_template()        从 functions/ 目录加载 .prompt      │
│    ├─→ _replace_placeholders() 替换 {{placeholder}} 占位符         │
│    └─→ 返回格式化后的提示词                                         │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│              resource/prompts/functions/*.prompt                    │
├─────────────────────────────────────────────────────────────────────┤
│  round_summary.prompt      - 轮次总结提示词                         │
│  snapshot_summary.prompt   - 快照总结提示词                         │
│  conversation_summary.prompt - 对话总结提示词                       │
│  title_summary.prompt      - 标题生成提示词                         │
│  auto_question.prompt      - 自动问题提示词                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 三、FunctionPromptAssembler

**文件**: `core/prompt/function_prompt_assembler.py`

### 3.1 核心功能

```python
class FunctionPromptAssembler:
    def __init__(self):
        self.functions_dir = config.prompts_dir / "functions"
        self._cache: Dict[str, str] = {}

    def load_and_format(self, function_name: str, **kwargs) -> str:
        """
        加载并格式化功能提示词

        Args:
            function_name: 功能名称（不带 .prompt 后缀）
            **kwargs: 用于替换的参数

        流程：
        1. 检查缓存
        2. 从 functions/{function_name}.prompt 加载模板
        3. 替换占位符
        4. 缓存结果
        """
```

### 3.2 占位符替换

支持两种格式：

| 格式 | 示例 | 说明 |
|------|------|------|
| `{{placeholder}}` | `{{max_length}}` | 双花括号格式 |
| `{placeholder}` | `{agent_system_prompt}` | 单花括号格式 |

```python
# 替换顺序
1. 先处理 {{placeholder}} 格式
2. 再处理 {placeholder} 格式（使用 str.format）
```

### 3.3 便捷方法

```python
# 预定义的加载方法
def load_round_summary_prompt(self) -> str:
    return self.load_and_format("round_summary", max_length=config.round_summary_max_length)

def load_snapshot_summary_prompt(self) -> str:
    return self.load_and_format("snapshot_summary", max_length=config.snapshot_summary_max_length)

def load_conversation_summary_prompt(self) -> str:
    return self.load_and_format("conversation_summary", max_length=config.conversation_summary_max_length)

def load_title_summary_prompt(self) -> str:
    return self.load_and_format("title_summary")

def load_auto_question_prompt(self, agent_system_prompt: str) -> str:
    return self.load_and_format("auto_question", agent_system_prompt=agent_system_prompt)
```

---

## 四、SummaryManager - 总结管理器

**文件**: `core/summary_manager.py`

### 4.1 职责

1. **轮次总结**：每轮对话结束后生成摘要
2. **快照总结**：每 N 轮生成一次压缩快照
3. **对话总结**：基于所有快照生成整体总结
4. **标题生成**：为新对话生成标题

### 4.2 总结层级关系

```
对话开始
    │
    ├─→ Round 1 ─→ Round总结 ─┐
    ├─→ Round 2 ─→ Round总结 ─┤
    ├─→ Round 3 ─→ Round总结 ─┤
    ├─→ Round 4 ─→ Round总结 ─┤
    ├─→ Round 5 ─→ Round总结 ─┴─→ Snapshot 1 ─┐
    │                                          │
    ├─→ Round 6 ─→ Round总结 ─┐               │
    ├─→ Round 7 ─→ Round总结 ─┤               │
    ├─→ Round 8 ─→ Round总结 ─┤               │
    ├─→ Round 9 ─→ Round总结 ─┤               │
    ├─→ Round 10 ─→ Round总结 ┴─→ Snapshot 2 ─┼─→ Conversation总结
    │                                          │
    └─→ ...                                    │
```

### 4.3 触发条件（配置）

```ini
# config.ini
round_summary_times = 5       # 每 5 轮生成一次快照
conversation_summary_snapshots = 2  # 每 2 个快照生成一次对话总结
```

### 4.4 核心方法

#### generate_conversation_title

```python
async def generate_conversation_title(self, agent, conversation_id, round_id, user_id):
    """
    生成对话标题

    流程：
    1. 构建当前轮次的对话内容
    2. 加载 title_summary.prompt
    3. 调用 LLM 生成标题
    4. 更新数据库
    5. 通过 WebSocket 推送给前端
    """
```

#### summarize_round

```python
async def summarize_round(self, agent, conversation_id, round_id, user_id):
    """
    总结单个轮次

    流程：
    1. 构建轮次消息内容
    2. 加载 round_summary.prompt（带 max_length 参数）
    3. 调用 LLM 生成总结
    4. 更新 rounds 表的 summary 字段
    """
```

#### summarize_snapshot

```python
async def summarize_snapshot(self, agent, conversation_id, user_id):
    """
    生成快照总结

    流程：
    1. 获取自上次快照后的所有轮次
    2. 检查轮次数量是否达到阈值
    3. 拼接轮次总结作为输入
    4. 加载 snapshot_summary.prompt
    5. 调用 LLM 生成快照总结
    6. 保存到 summary_snapshots 表
    """
```

#### summarize_conversation

```python
async def summarize_conversation(self, agent, conversation_id, user_id):
    """
    生成对话总结

    流程：
    1. 获取所有快照
    2. 拼接快照内容作为输入
    3. 加载 conversation_summary.prompt
    4. 调用 LLM 生成对话总结
    5. 更新 conversations 表的 summary 字段
    """
```

### 4.5 日志追踪

每次总结操作都会记录到 `summary_log` 表：

```python
def create_summary_log_with_token_tracking(self, agent, summary_content, ...):
    """
    创建总结日志，自动追踪：
    - 输入内容
    - 输出结果
    - Token 消耗
    - 执行时间
    - 成功/失败状态
    """
```

---

## 五、AutoQuestionManager - 自动问题管理器

**文件**: `core/auto_question_manager.py`

### 5.1 职责

根据对话内容，自动生成用户可能感兴趣的后续问题，通过 WebSocket 推送给前端。

### 5.2 核心方法

```python
async def generate_auto_question(self, agent, conversation_id, round_id, user_id):
    """
    生成自动问题建议

    流程：
    1. 构建对话内容（当前轮次）
    2. 加载 auto_question.prompt（注入 agent.system_prompt）
    3. 调用 LLM 生成问题
    4. 解析 JSON 响应
    5. 通过 WebSocket 推送给前端
    """
```

### 5.3 输出格式

```json
{
  "questions": [
    "第一个相关问题",
    "第二个相关问题",
    "第三个相关问题"
  ]
}
```

### 5.4 异步执行

自动问题生成是**异步执行**的，不阻塞主流程：

```python
# HistoryManager.on_round_end() 中
if agent.enable_auto_question:
    asyncio.create_task(
        self.auto_question_manager.generate_auto_question(...)
    )
```

---

## 六、功能提示词编写规范

### 6.1 目录结构

```
resource/prompts/functions/
├── round_summary.prompt        # 轮次总结
├── snapshot_summary.prompt     # 快照总结
├── conversation_summary.prompt # 对话总结
├── title_summary.prompt        # 标题生成
└── auto_question.prompt        # 自动问题
```

### 6.2 提示词模板

```markdown
# {功能名称}提示词

你是一个专业的{角色描述}，负责{任务描述}。

## 任务要求
- 要求1
- 要求2
- 字数限制：{{max_length}}字（如需）

## 输出格式
{描述期望的输出格式}

## 示例
**输入**：
```
{示例输入}
```

**输出**：
```
{示例输出}
```
```

### 6.3 占位符使用

| 占位符 | 来源 | 用途 |
|--------|------|------|
| `{{max_length}}` | config.xxx_max_length | 限制输出长度 |
| `{agent_system_prompt}` | agent.system_prompt | 注入 Agent 特性 |

### 6.4 现有提示词说明

| 提示词 | 占位符 | 输出要求 |
|--------|--------|----------|
| round_summary.prompt | `{{max_length}}` | 结构化总结（用户意图/解决方案/工具使用/关键信息） |
| snapshot_summary.prompt | `{{max_length}}` | 压缩多轮总结为一段 |
| conversation_summary.prompt | `{{max_length}}` | 压缩所有快照为整体总结 |
| title_summary.prompt | 无 | 8-15字中文标题 |
| auto_question.prompt | `{agent_system_prompt}` | JSON格式的3个问题 |

---

## 七、新增功能模块指南

### 7.1 步骤总览

```
1. 创建功能提示词文件
2. 在 FunctionPromptAssembler 添加便捷方法
3. 创建功能管理器类
4. 在适当位置调用
```

### 7.2 详细步骤

#### 步骤 1：创建提示词

**文件**: `resource/prompts/functions/my_function.prompt`

```markdown
你是一个专业的{功能描述}专家。

## 任务
{详细任务描述}

## 要求
- 要求1
- 要求2
- 字数限制：{{max_length}}字

## 输出格式
{期望格式}

## 示例
...
```

#### 步骤 2：添加加载方法

**文件**: `core/prompt/function_prompt_assembler.py`

```python
def load_my_function_prompt(self, custom_param: str = "") -> str:
    """加载我的功能提示词"""
    return self.load_and_format(
        "my_function",
        max_length=config.my_function_max_length,
        custom_param=custom_param
    )
```

#### 步骤 3：创建管理器

**文件**: `core/my_function_manager.py`

```python
class MyFunctionManager:
    def __init__(self, sqlite_storage: RepositoryAdapter,
                 function_prompt_assembler: FunctionPromptAssembler):
        self.sqlite_storage = sqlite_storage
        self.function_prompt_assembler = function_prompt_assembler
        self.token_manager = TokenManager(sqlite_storage)
        self.logger = ManagerLogger("MyFunctionManager")

    async def execute_my_function(self, agent: Agent, conversation_id: str, ...):
        """执行我的功能"""
        try:
            # 1. 构建输入内容
            input_content = await self._build_input(...)

            # 2. 加载提示词
            system_prompt = self.function_prompt_assembler.load_my_function_prompt()

            # 3. 调用 LLM
            llm_client = EnhancedLLMClient.create_from_llm(agent.summary_llm)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_content}
            ]
            response = await llm_client.block(messages=messages, ...)

            # 4. 处理结果
            result = self._parse_response(response.content)

            # 5. 记录 Token
            self.token_manager.add_tokens(
                token_usage=response.token_usage,
                llm=agent.summary_llm,
                operation_type="my_function",
                ...
            )

            return result

        except Exception as e:
            self.logger.error("执行失败", exception=e)
            raise
```

#### 步骤 4：集成调用

```python
# 在 __main__.py 初始化
my_function_manager = MyFunctionManager(db_storage, function_prompt_assembler)

# 在适当位置调用
await my_function_manager.execute_my_function(agent, conversation_id, ...)
```

---

## 八、配置项

**文件**: `config/config.ini`

```ini
[summary]
# 总结字数限制
round_summary_max_length = 200
snapshot_summary_max_length = 500
conversation_summary_max_length = 1000

# 触发条件
round_summary_times = 5              # 每 N 轮生成一次快照
conversation_summary_snapshots = 2   # 每 N 个快照生成一次对话总结
```

---

## 九、文件位置索引

| 类型 | 文件路径 |
|------|----------|
| 提示词组装器 | `koalaq_hub/core/prompt/function_prompt_assembler.py` |
| 总结管理器 | `koalaq_hub/core/summary_manager.py` |
| 自动问题管理器 | `koalaq_hub/core/auto_question_manager.py` |
| Token 管理器 | `koalaq_hub/core/token_manager.py` |
| 轮次总结提示词 | `resource/prompts/functions/round_summary.prompt` |
| 快照总结提示词 | `resource/prompts/functions/snapshot_summary.prompt` |
| 对话总结提示词 | `resource/prompts/functions/conversation_summary.prompt` |
| 标题生成提示词 | `resource/prompts/functions/title_summary.prompt` |
| 自动问题提示词 | `resource/prompts/functions/auto_question.prompt` |

---

## 十、关键设计决策

### 10.1 使用 summary_llm

功能模块使用 `agent.summary_llm` 而非 `agent.main_llm`：

- **原因**：功能调用通常不需要最强模型，可以使用更便宜的模型
- **配置**：`summary_llm_use` 在 agent.ini 中独立配置

### 10.2 异步非阻塞

自动问题生成使用 `asyncio.create_task()` 异步执行：

- **原因**：不影响主对话流程的响应速度
- **效果**：用户先看到回答，问题推荐稍后到达

### 10.3 日志追踪

所有总结操作都记录到 `summary_log` 表：

- **目的**：审计、调试、性能分析
- **内容**：输入、输出、Token、耗时、状态

### 10.4 缓存机制

`FunctionPromptAssembler` 缓存格式化后的提示词：

- **键**：`{function_name}_{hash(kwargs)}`
- **目的**：避免重复文件读取和格式化
