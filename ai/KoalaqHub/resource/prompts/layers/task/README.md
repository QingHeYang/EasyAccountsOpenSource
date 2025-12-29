# 任务层（Task Layer）

任务层是每个Agent的**核心指导**，具有最高优先级。

## 文件命名

`{描述}_instructions.prompt`

例如：
- `workorder_instructions.prompt` - 工单Agent指导
- `device_instructions.prompt` - 设备Agent指导

## 必须包含内容

1. **核心职责** - Agent的主要任务
2. **工具使用指南** - 什么情况用什么工具（核心）
3. **回复规范** - 如何回复用户
4. **注意事项** - 禁止事项、特殊规则

## 示例结构

```markdown
# XX专家指导

## 核心职责
[描述Agent的主要职责]

## 工具联动
1. get_system_time → 获取当前时间
2. query_xxx → 什么情况下使用
3. create_report → 什么情况下使用

## 回复规范
### 查询前
- 确认需求
- 分析步骤

### 结果呈现
- 单条：突出关键信息
- 多条：不能省略

## 记住
- 先调用xxx再调用yyy
- 遇到xxx时使用zzz

## 禁止内容
- 禁止xxx
```

## 配置方式

在 `agent.ini` 中配置：
```ini
task_instructions_file = xxx_instructions.prompt
```
