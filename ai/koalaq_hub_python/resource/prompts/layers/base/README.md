# 基础层（Base Layer）

基础层定义AI的核心行为规范、输出格式和思维模式。这些是所有Agent共享的基础规则。

## 目录结构

```
base/
├── format/          # 输出格式规范
├── communication/   # 交流风格
├── react/          # ReAct思维模式
├── safety/         # 安全规范
└── other/          # 其他基础规范
```

## 模块分类

### format/ - 输出格式
- 如何组织内容结构
- Markdown使用规范
- 数据展示方式

### communication/ - 交流风格
- 语气和态度
- 交流技巧
- 语言规范

### react/ - 思维模式
- ReAct模式的不同风格
- 推理过程展示方式
- 迭代思考流程

### safety/ - 安全规范
- 隐私保护
- 内容安全
- 行为边界

## 设计原则

1. **通用性**：适用于所有Agent
2. **基础性**：定义最基本的行为准则
3. **稳定性**：很少需要修改
4. **必要性**：缺少会影响Agent基本功能

## 使用说明

基础层模块通过Agent的`base_modules`配置选择性加载。ReAct模式通过`enable_react_mode`和`react_style`控制。