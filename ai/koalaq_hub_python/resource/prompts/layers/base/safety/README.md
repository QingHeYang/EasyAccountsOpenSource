# 安全规范模块

定义AI的安全边界和隐私保护规范。

## 文件说明

- `safety_rules.prompt` - 通用安全规范
- `privacy_protection.prompt` - 隐私保护规范
- `content_filter.prompt` - 内容过滤规则
- `data_security.prompt` - 数据安全规范

## 核心原则

1. **隐私保护**：不泄露用户信息
2. **内容安全**：不生成有害内容
3. **行为边界**：明确能做和不能做的事
4. **责任声明**：适当的免责说明

## 重要性

安全规范是所有AI都应该遵守的底线，建议默认包含在base_modules中。