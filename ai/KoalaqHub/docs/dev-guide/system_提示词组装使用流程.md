# 系统提示词组装流程文档

> 版本: 2.1
> 更新时间: 2025-12-08
> 状态: 正式版

## 一、概述

系统提示词采用**简化的分层架构**，只保留核心层次：

- **任务层 (Task)** - 每个Agent的详细任务指导（含工具使用指南）
- **角色层 (Role)** - 身份定位
- **上下文层 (Context)** - 历史信息（动态生成）

### 设计理念

Agent必须有详细的、手写的工具指南，说明什么情况用什么工具。这无法通过模块化拼接简单做到，因此简化为任务层为核心的设计。

---

## 二、目录结构

```
resource/
├── config/
│   └── agent.ini              # Agent配置文件
├── role/                       # 角色定义文件 (.role)
│   ├── 智能助手.role
│   └── 恒银科技.role
├── agents/                     # Agent能力定义 (.yaml) - 给其他Agent调用时参考
│   └── workorder-agent.yaml
└── prompts/
    ├── layers/
    │   ├── task/              # 任务层：Agent专属指导（核心）
    │   │   ├── workorder_instructions.prompt
    │   │   └── device_instructions.prompt
    │   └── role/              # 角色层：身份定位模板
    │       └── default.prompt
    └── functions/             # 功能型提示词（独立使用）
        ├── round_summary.prompt
        ├── snapshot_summary.prompt
        └── conversation_summary.prompt

注：上下文层（context）从数据库动态获取，无对应目录
```

---

## 三、提示词分层架构

```
┌─────────────────────────────────────────────┐
│  <task>      任务层 - 核心指导             │
├─────────────────────────────────────────────┤
│  <role>      角色层 - 身份定位             │
├─────────────────────────────────────────────┤
│  <context>   上下文层 - 历史信息           │
└─────────────────────────────────────────────┘
```

### 3.1 任务层 (Task Layer) - 核心

**目录**: `prompts/layers/task/`
**配置项**: `task_instructions_file`

任务层是每个Agent的**核心指导**，必须包含：
- 具体业务规则
- **工具使用指南**（什么情况用什么工具）
- 回复规范
- 注意事项

**示例文件**: `workorder_instructions.prompt`
```markdown
# 智能运维专家指导

## 核心职责
分析用户需求，专业查询IOMS工单、设备台账数据

## 工具联动
1. get_system_time → 获取当前时间
2. query_device → 查询设备数据
3. query_history_workorder → 查询工单
4. create_excel_report → 导出报表

## 时间查询规则
统一查询字段：end_time
维修工单特指：process_method = '现场维修'

## 回复规范
### 查询前
第一步：简洁确认需求
第二步：分析用户需求

### 结果呈现
- 单条：突出关键信息
- 多条：给出全部条目，不能省略
- 统计：关键指标+趋势

## 记住
- 先调用 `get_system_time` 获取当前时间
- 遇到银行简称，调用 `get_bank_info` 获取全称

## 禁止内容
- 禁止使用LIMIT
```

**组装结果**:
```xml
<task>
[任务层内容]
</task>
```

### 3.2 角色层 (Role Layer)

**目录**: `prompts/layers/role/`
**关联文件**: `resource/role/*.role`
**配置项**: `role` (在agent.ini中)

#### 角色定义文件 (.role)

**路径**: `resource/role/恒银科技.role`
```
role: 恒银科技制造的专业的sqlite数据库数据查询员
cos_role: 高效率的数据查询员
name: 小U
character: 专业、理性、高效，语言精准简洁
user_role: 需要查询数据库的管理人员、工程师
user_role_description: 恒银科技的总部管理人员
user_scene: 工作场景
location: 天津市东丽区
```

#### 角色模板文件 (.prompt)

**default.prompt**:
```
# 身份定义
## 基本信息
你是{name}，一位{role}。

## 角色特征
- **特殊身份**：{cos_role}
- **性格特点**：{character}
- **服务对象**：{user_role}

## 工作环境
- **对话场景**：{user_scene}
- **所在位置**：{location}
```

**组装流程**:
1. 从 `.role` 文件读取角色属性 → 解析为JSON
2. 加载 default.prompt 模板
3. 替换模板中的 `{占位符}`

### 3.3 上下文层 (Context Layer)

**数据源**: 数据库（通过 `RepositoryAdapter`）

上下文层提供历史会话信息：
- 当前会话总结
- 最近快照（最多2个）

**组装结果**:
```xml
<context>
【当前会话总结】
用户询问了工单查询相关问题...

【快照1】
之前讨论了设备台账分析...
</context>
```

---

## 四、配置系统

### 4.1 Agent配置 (agent.ini)

```ini
[workorder-agent]
# 基础信息
id = 1
enable = true
name = 小U智能体
description = 工单查询分析

# 角色配置
role = 恒银科技.role

# 任务指导文件（核心配置）
task_instructions_file = workorder_instructions.prompt

# 其他配置...
llm_use = moonshot-k2
tool_round = 10
mcp_servers = []
```

### 4.2 Agent模型属性

提示词相关的核心属性：

```python
@dataclass
class Agent:
    # 角色配置
    role_file: str = ""           # 角色文件名
    role_context: str = ""        # 角色文件内容（JSON格式）

    # 任务指导（核心）
    task_instructions_file: str = ""

    # 运行时组装结果
    system_prompt: str = ""
```

---

## 五、调用流程

```
WebSocket/HTTP
      │
      ▼
AgentRegistry.build_system_prompt()
      │
      ├→ build_tools_list() [异步]
      │
      └→ SystemPromptAssembler.assemble() [同步]
              │
              ├→ _load_task_layer()     # 加载任务指导
              ├→ _build_role_layer()    # 构建角色定位
              └→ _build_context_layer() # 构建历史上下文
```

### 核心代码

```python
def assemble(self, agent: Agent, user_id: str, conversation_id: str) -> str:
    sections = []

    # 1. 任务层 - Agent专属指导
    if agent.task_instructions_file:
        task_content = self._load_task_layer(agent)
        if task_content:
            sections.append(f"<task>\n{task_content}\n</task>")

    # 2. 角色层 - 身份定位
    role_content = self._build_role_layer(agent)
    if role_content:
        sections.append(f"<role>\n{role_content}\n</role>")

    # 3. 上下文层 - 历史信息
    context_content = self._build_context_layer(user_id, conversation_id)
    if context_content:
        sections.append(f"<context>\n{context_content}\n</context>")

    return "\n\n".join(sections)
```

---

## 六、子 Agent (Sub-Agent) 提示词组装

### 6.1 概述

子 Agent 使用**与主 Agent 完全相同**的 `SystemPromptAssembler` 进行提示词组装。这意味着：

- 任务层：使用相同的 `task_instructions_file`
- 角色层：使用相同的 `role_file` 和 `role_context`
- 上下文层：从**子会话**获取历史信息

### 6.2 调用流程

```
SubAgentExecutor.execute_sub_agent()
      │
      ├─→ 创建子会话 (sub_conversation_id)
      │       └─→ parent_conversation_id 关联父会话
      │
      ├─→ AgentRegistry.build_sub_agent(agent_id)
      │       └─→ 创建简化的 Agent 实例
      │               ├─→ 复制 role_file, role_context
      │               ├─→ 复制 task_instructions_file
      │               └─→ 设置 sub_agent_mode = True
      │
      └─→ AgentRegistry.build_system_prompt(sub_agent, user_id, sub_conversation_id)
              │
              └─→ SystemPromptAssembler.assemble()  # 同一个组装器
                      ├─→ _load_task_layer()     # 加载相同的任务指导
                      ├─→ _build_role_layer()    # 使用相同的角色定义
                      └─→ _build_context_layer(user_id, sub_conversation_id)
                              └─→ 从子会话获取上下文（首次调用通常为空）
```

### 6.3 子 Agent 与主 Agent 的提示词差异

| 层次 | 主 Agent | 子 Agent | 说明 |
|------|----------|----------|------|
| 任务层 | 完整任务指导 | 相同 | 使用同一份 `.prompt` 文件 |
| 角色层 | 角色定义 | 相同 | 使用同一份 `.role` 文件 |
| 上下文层 | 主会话历史 | 子会话历史 | 独立的会话上下文 |

### 6.4 设计原因

1. **一致性**：子 Agent 继承主 Agent 的专业能力和角色设定
2. **简化**：无需为子 Agent 单独维护提示词配置
3. **隔离**：子会话的上下文独立，不污染主会话

### 6.5 代码位置

```python
# AgentExecutor.execute() - 子Agent提示词组装入口
if not agent.system_prompt:
    system_prompt = await self.agent_registry.build_system_prompt(
        agent, user_id, conversation_id  # conversation_id 是子会话ID
    )
    agent.system_prompt = system_prompt
```

---

## 七、创建新Agent指南

### 步骤

1. **创建角色文件** `resource/role/my_agent.role`
   ```
   role: 专业的XX助手
   name: 小助手
   character: 专业、高效
   user_role: 用户
   user_scene: 工作场景
   ```

2. **创建任务指导文件** `resource/prompts/layers/task/my_instructions.prompt`
   ```markdown
   # XX专家指导

   ## 核心职责
   [描述Agent的主要职责]

   ## 工具使用指南
   1. tool_a → 什么情况下使用
   2. tool_b → 什么情况下使用

   ## 回复规范
   [描述如何回复用户]

   ## 注意事项
   [列出需要注意的点]
   ```

3. **添加Agent配置** `resource/config/agent.ini`
   ```ini
   [my-agent]
   enable = true
   name = 我的智能体
   role = my_agent.role
   task_instructions_file = my_instructions.prompt
   # ...其他配置
   ```

---

## 八、组装结果示例

```xml
<task>
# 智能运维专家指导

## 核心职责
分析用户需求，专业查询IOMS工单、设备台账数据

## 工具联动
1. get_system_time → 获取当前时间
2. query_history_workorder → 查询工单
...
</task>

<role>
# 角色定位
你是小U，恒银科技制造的专业的sqlite数据库数据查询员。性格专业、理性、高效，为需要查询数据库的管理人员、工程师在工作场景提供服务。
</role>

<context>
【当前会话总结】
用户询问了本月工单统计相关问题
</context>
```

---

## 九、相关文件清单

| 文件 | 说明 |
|------|------|
| `koalaq_hub/core/prompt/system_prompt_assembler.py` | 核心组装器 |
| `koalaq_hub/core/agents/agent_registry.py` | Agent注册表 |
| `koalaq_hub/config/agent_builder.py` | Agent配置加载器 |
| `koalaq_hub/models/agent.py` | Agent模型 |
| `resource/config/agent.ini` | Agent配置文件 |
| `resource/role/*.role` | 角色定义文件 |
| `resource/prompts/layers/task/*.prompt` | 任务指导文件 |
| `resource/prompts/layers/role/*.prompt` | 角色模板文件 |

---

## 十、已删除内容（历史记录）

以下模块已在v2.0中删除：

- **基础层 (Base Layer)** - 包括 format_rules, communication_style, safety_rules, react_mode 等
- **能力层 (Capability Layer)** - 包括 tool_usage_guide, agent_collaboration 等

**删除原因**：Agent必须有详细的、手写的工具使用指南，通用的模块化拼接无法满足实际需求。
