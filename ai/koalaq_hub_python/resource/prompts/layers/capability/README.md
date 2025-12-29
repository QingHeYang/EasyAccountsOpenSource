# 能力层（Capability Layer）

能力层描述AI的各种能力，包括工具使用、Agent协作和专业技能。

## 子目录说明

### tools/ - 工具相关能力
- `tool_usage_guide.prompt` - 通用工具使用指南
- `tool_format.prompt` - 工具调用格式说明
- 特定工具的使用指南

### agents/ - Agent协作能力
- `agent_collaboration.prompt` - Agent协作通用指南
- `agent_formats.prompt` - Agent调用格式说明
- 特定Agent的协作指南

### skills/ - 专业技能
- `data_analysis.prompt` - 数据分析能力
- `customer_service.prompt` - 客服能力
- `coding.prompt` - 编程能力
- 其他专业技能描述

## 设计原则

1. **明确性**：清楚描述能力边界
2. **实用性**：提供具体使用方法
3. **示例性**：包含使用示例
4. **扩展性**：易于添加新能力

## 动态生成

部分能力描述（如可用工具列表）在运行时动态生成，确保始终是最新的。