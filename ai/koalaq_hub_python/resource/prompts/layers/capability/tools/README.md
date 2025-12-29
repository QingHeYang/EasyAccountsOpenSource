# 工具调用提示词说明

本目录包含两种工具调用模式的提示词：

## 1. MCP 文本格式 (tool_usage_guide.prompt)
适用于 `tool_mode = "mcp"` 配置。在这种模式下：
- 工具调用通过特定的文本格式实现
- 需要在系统提示词中包含详细的格式说明
- 工具描述会被包含在系统提示词中

## 2. Function Calling 格式 (tool_usage_guide_function_calling.prompt)
适用于 `tool_mode = "function_calling"` 配置。在这种模式下：
- 工具调用通过 OpenAI Function Calling API 实现
- 不需要格式说明，因为调用格式由 API 定义
- 工具描述通过 API 参数传递，不在系统提示词中
- 提示词更简洁，专注于使用原则和建议

## 选择指南
- 如果使用支持 Function Calling 的 LLM（如 GPT-4、Claude 等），推荐使用 Function Calling 模式
- 如果使用不支持 Function Calling 的 LLM，使用 MCP 文本格式模式

系统会根据 `config.tool_mode` 自动选择合适的提示词文件。