# Agent专属配置（Agents）

本目录存放特定Agent的完整配置或覆盖规则。

## 目录结构

```
agents/
└── {agent_id}/
    ├── overrides.prompt     # 覆盖默认行为
    ├── custom_base.prompt   # 自定义基础层
    └── special_rules.prompt # 特殊规则
```

## 用途

1. **完全定制**：某些Agent需要完全不同的提示词结构
2. **特殊覆盖**：覆盖分层系统的某些部分
3. **实验性功能**：测试新的提示词设计
4. **向后兼容**：保留旧版Agent的行为

## 优先级

Agent专属配置具有最高优先级，会覆盖分层系统的对应部分。

## 使用场景

- 特殊用途的Agent（如纯工具Agent）
- 需要保持特定行为的遗留Agent
- 实验性的新型Agent
- 客户定制的专属Agent