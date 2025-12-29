# Parser包使用指南

## 一、快速开始

### 1.1 基本使用（最简单的方式）

```python
from koalaq_hub.core.parser import UnifiedParser

# 创建解析器
parser = UnifiedParser()

# 解析LLM响应
llm_response = '''
我来帮你查询工单信息。

\`\`\`tool
{
  "tool": "search_workorders",
  "arguments": {
    "status": "open"
  }
}
\`\`\`

同时让 @easy-accounts-agent 分析一下相关的财务影响。
'''

# 解析响应
cleaned_content, results, stats = parser.parse_response(llm_response)

# cleaned_content: "我来帮你查询工单信息。\n\n同时让 分析一下相关的财务影响。"
# results: [ToolCall对象, AgentCall对象]
# stats: {"tool": 1, "agent": 1, "parallel": 0, "pipeline": 0}
```

## 二、核心概念

### 2.1 输入输出流程

```
输入（LLM响应文本）
     ↓
UnifiedParser.parse_response()
     ↓
 ┌───┴───┐
 ↓       ↓
工具解析  Agent解析
 ↓       ↓
 └───┬───┘
     ↓
输出：(清理后文本, 解析结果列表, 统计信息)
```

### 2.2 数据结构关系

```
ParseResult (基类)
    ├── ToolCall (工具调用)
    ├── AgentCall (单个Agent调用)
    ├── ParallelAgentCall (并行Agent调用)
    └── PipelineAgentCall (串行Agent调用)
```

## 三、详细使用示例

### 3.1 解析工具调用

```python
from koalaq_hub.core.parser import ToolParser

tool_parser = ToolParser()

# 支持的格式1: 代码块
content1 = '''
\`\`\`tool
{
  "tool": "get_weather",
  "arguments": {"city": "北京"}
}
\`\`\`
'''

# 支持的格式2: 内联JSON
content2 = '调用工具 {"tool": "translate", "arguments": {"text": "hello"}}'

# 解析
cleaned, tools, has_tools = tool_parser.parse(content1)
# tools[0].tool_name == "get_weather"
# tools[0].arguments == {"city": "北京"}
```

### 3.2 解析Agent调用

```python
from koalaq_hub.core.parser import AgentParser

agent_parser = AgentParser()

# 格式1: 单个Agent
content1 = '''
\`\`\`agent
{
  "agent": "workorder-agent",
  "task": "查询所有未完成的工单",
  "context": {"priority": "high"}
}
\`\`\`
'''

# 格式2: @mention格式
content2 = "@easy-accounts-agent 请分析本月支出情况"

# 格式3: 并行调用
content3 = '''
\`\`\`parallel
[
  {"agent": "agent1", "task": "任务1"},
  {"agent": "agent2", "task": "任务2"}
]
\`\`\`
'''

# 格式4: 串行调用
content4 = '''
\`\`\`pipeline
[
  {"agent": "data-agent", "task": "收集数据"},
  {"agent": "analysis-agent", "task": "分析数据"},
  {"agent": "report-agent", "task": "生成报告"}
]
\`\`\`
'''
```

### 3.3 统一解析器高级功能

```python
from koalaq_hub.core.parser import UnifiedParser

parser = UnifiedParser()

# 1. 快速检查
if parser.has_any_calls(content):
    print("包含调用指令")

# 2. 解析并分组
cleaned, results, stats = parser.parse_response(content)
grouped = parser.group_by_type(results)
# grouped[CallType.TOOL] = [所有工具调用]
# grouped[CallType.AGENT] = [所有Agent调用]

# 3. 提取特定类型
tool_calls = parser.extract_tool_calls(results)
agent_calls = parser.extract_agent_calls(results)

# 4. 验证调用有效性
available_tools = ["search_workorders", "get_weather"]
available_agents = ["workorder-agent", "easy-accounts-agent"]
valid_calls, errors = parser.validate_calls(
    results, 
    available_tools=available_tools,
    available_agents=available_agents
)

# 5. 格式化显示
display_text = parser.format_for_display(results)
print(display_text)
```

## 四、方法流程图

### 4.1 UnifiedParser.parse_response() 流程

```
parse_response(content)
    │
    ├─► 初始化结果列表和统计
    │
    ├─► 遍历所有解析器（tool_parser, agent_parser）
    │   │
    │   ├─► parser.can_parse(content) 快速检查
    │   │
    │   └─► parser.parse(content) 执行解析
    │       │
    │       ├─► 提取匹配内容
    │       ├─► 创建对应的Result对象
    │       └─► 清理已解析内容
    │
    ├─► 合并所有结果
    │
    └─► 返回 (清理后内容, 结果列表, 统计)
```

### 4.2 ToolParser.parse() 流程

```
parse(content)
    │
    ├─► 尝试解析代码块格式 \`\`\`tool
    │   └─► 正则匹配 → JSON解析 → 创建ToolCall
    │
    ├─► 尝试解析JSON格式 {"tool": ...}
    │   └─► 正则匹配 → JSON解析 → 创建ToolCall
    │
    ├─► 尝试解析嵌套JSON（手工匹配括号）
    │   └─► 括号匹配 → JSON解析 → 创建ToolCall
    │
    └─► 返回 (清理后内容, ToolCall列表, 是否有结果)
```

### 4.3 AgentParser.parse() 流程

```
parse(content)
    │
    ├─► 解析 \`\`\`agent 代码块
    │   └─► 创建 AgentCall
    │
    ├─► 解析 \`\`\`parallel 代码块
    │   └─► 创建 ParallelAgentCall
    │
    ├─► 解析 \`\`\`pipeline 代码块
    │   └─► 创建 PipelineAgentCall
    │
    ├─► 解析 @agent-name 格式
    │   └─► 创建 AgentCall
    │
    └─► 返回 (清理后内容, 各类Call列表, 是否有结果)
```

## 五、在ChatProcessor中的集成

```python
class WebSocketChatProcessor:
    def __init__(self):
        self.parser = UnifiedParser()
    
    async def process_llm_response(self, response: str, context: dict):
        # 1. 解析响应
        cleaned_content, calls, stats = self.parser.parse_response(response)
        
        # 2. 如果没有调用，直接返回
        if not calls:
            return cleaned_content
        
        # 3. 处理各类调用
        for call in calls:
            if isinstance(call, ToolCall):
                # 调用工具
                result = await self.tool_manager.handle_tool_call(
                    call.tool_name, 
                    call.arguments
                )
            
            elif isinstance(call, AgentCall):
                # 调用Agent
                result = await self.agent_coordinator.handle_agent_call(call)
            
            elif isinstance(call, ParallelAgentCall):
                # 并行调用多个Agent
                results = await self.agent_coordinator.handle_parallel(call.agents)
            
            elif isinstance(call, PipelineAgentCall):
                # 串行调用
                result = await self.agent_coordinator.handle_pipeline(call.steps)
        
        # 4. 继续对话流程...
```

## 六、最佳实践

1. **始终使用UnifiedParser作为入口**
   - 它会自动协调所有子解析器
   - 提供统一的接口和错误处理

2. **利用验证功能**
   - 在执行调用前验证工具/Agent是否可用
   - 避免执行无效调用

3. **保留原始内容**
   - ParseResult包含原始内容和位置信息
   - 便于调试和错误追踪

4. **处理清理后的内容**
   - 解析器会移除已识别的调用指令
   - 剩余内容可能需要进一步处理或显示

## 七、扩展性

如需支持新的调用格式：

1. 创建新的解析器类，继承BaseParser
2. 实现parse()和can_parse()方法
3. 在UnifiedParser中注册新解析器

```python
class CustomParser(BaseParser):
    def parse(self, content: str):
        # 实现自定义解析逻辑
        pass
    
    def can_parse(self, content: str):
        # 快速检查逻辑
        pass

# 注册到统一解析器
unified_parser.parsers.append(CustomParser())
```

## 八、常见问题

### Q1: 为什么要清理已解析的内容？
A: 避免调用指令显示在最终回复中，让用户看到的是纯净的对话内容。

### Q2: 如何处理解析失败的情况？
A: 解析器会跳过无法解析的内容，不会抛出异常。可以通过日志查看解析失败的详情。

### Q3: 支持的代码块标记为什么要转义？
A: 在Python字符串中，需要使用 `\`\`\`` 来表示实际的三个反引号。