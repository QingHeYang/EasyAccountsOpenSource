# 功能型提示词（Functions）

功能型提示词是独立于系统提示词的单一功能模板，用于特定任务。

## 文件列表

- `title_summary.prompt` - 生成对话标题
- `round_summary.prompt` - 单轮对话总结
- `snapshot_summary.prompt` - 快照总结
- `conversation_summary.prompt` - 完整对话总结
- `auto_question.prompt` - 自动生成追问
- `error_analysis.prompt` - 错误分析
- `intent_recognition.prompt` - 意图识别

## 特点

1. **独立使用**：不依赖系统提示词
2. **单一功能**：每个文件一个功能
3. **参数化**：通过占位符传递参数
4. **即用即走**：完成任务后不保留状态

## 使用方式

```python
# 通过PromptManager加载
prompt = prompt_manager.load_function_prompt(
    "title_summary",
    conversation_content=messages
)
```

## 设计原则

1. **聚焦单一任务**
2. **明确输入输出**
3. **包含格式要求**
4. **提供示例**