# Agent能力定义目录

本目录存放各个Agent的能力定义文件（.yaml格式），用于主Agent理解和调用子Agent。

## 文件说明

- `{agent-id}.yaml` - Agent能力定义文件
- `{agent-id}.prompt` - Agent指南文件（已废弃，改用yaml）
- `agent-template.yaml` - 能力定义模板

## 核心设计理念

**从"对话"到"调用"**：Agent间的交互应该是函数调用而非角色扮演。

## YAML文件结构

### 1. 基本信息
```yaml
agent_id: {agent-id}  # 唯一标识
name: {显示名称}      # 用于展示
```

### 2. 工具列表（原子能力）
```yaml
tools:
  - name: {工具名}
    description: {简短描述}
    required: {是否必需}  # 可选
```

### 3. 核心能力（能力概述）
```yaml
capabilities:
  - {能力类别}: {具体描述}
```

### 4. 调用模式（执行路径）
```yaml
required_patterns:
  - name: {模式名}
    condition: {触发条件}
    主agent指导: "{协调指导}"
    sequence: [工具调用顺序]
```

### 5. 典型用例（转述示例）
```yaml
examples:
  - user_input: "{用户说的话}"
    agent_input: "@agent-id {转述后的指令}"
    pattern: {使用的模式}
```

### 6. 约束限制（边界条件）
```yaml
constraints:
  - {限制说明}
```

## 编写原则

1. **简洁明确**：每个字段都应该信息密集，避免冗余
2. **面向调用**：重点是"能做什么"和"怎么调用"
3. **工具原子化**：工具是最小单位，不要描述工具内部细节
4. **模式清晰**：明确什么情况用什么调用顺序
5. **示例驱动**：通过例子展示如何从用户需求转换为Agent调用

## 主Agent的职责

根据YAML定义，主Agent需要：
1. **意图识别**：理解用户需求，匹配到对应的Agent和模式
2. **信息提取**：从用户输入中提取关键参数
3. **任务转述**：将用户语言转换为Agent调用指令
4. **路径规划**：根据调用模式指导执行顺序
5. **结果整合**：将Agent返回结果转换为用户友好的表述

## 文件维护

- 新增Agent时，复制`agent-template.yaml`进行修改
- 保持YAML格式的一致性，便于程序解析
- 定期review，确保能力描述与实际实现同步