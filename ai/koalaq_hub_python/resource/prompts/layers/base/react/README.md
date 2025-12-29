# ReAct思维模式模块

本目录包含ReAct（Reasoning + Acting）思维模式的不同风格实现。

## 文件说明

- `react_mode.prompt` - 详细版（verbose），展示完整思考过程
- `react_mode_concise.prompt` - 简洁版，保留关键步骤
- `react_mode_hidden.prompt` - 隐藏版，内部思考不展示

## 使用方式

通过Agent配置控制：
```ini
enable_react_mode = true
react_style = verbose  # 或 concise, hidden
```

## 选择建议

- **verbose**：教学、调试、复杂推理场景
- **concise**：日常任务、专业用户
- **hidden**：追求自然对话、生产环境