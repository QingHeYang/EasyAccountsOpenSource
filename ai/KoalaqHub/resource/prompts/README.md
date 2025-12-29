# 提示词系统目录

本目录采用简化的分层架构设计。

## 目录结构

```
prompts/
├── layers/          # 分层提示词片段
│   ├── task/        # 任务层：Agent专属指导（核心）
│   └── role/        # 角色层：身份定位模板
└── functions/       # 功能型提示词（独立使用）
```

注：上下文层（context）从数据库动态获取，无对应目录

## 设计理念

1. **任务层为核心**：每个Agent都需要一个详细的任务指导文件，包含：
   - 具体业务规则
   - 工具使用指南（什么情况用什么工具）
   - 回复规范

2. **角色层定位**：通过角色模板和角色文件组合定义Agent身份

3. **上下文层动态**：从数据库获取历史会话信息

## 使用方式

### 创建新Agent

1. 在 `resource/role/` 创建角色文件（.role）
2. 在 `layers/task/` 创建任务指导文件（.prompt）
3. 在 `resource/config/agent.ini` 添加Agent配置

### 配置示例

```ini
[my-agent]
role = my_role.role
task_instructions_file = my_instructions.prompt
```

## 文件说明

- `layers/task/*.prompt` - 任务指导，每个Agent一个
- `layers/role/default.prompt` - 角色模板
- `functions/*.prompt` - 功能型提示词（总结、标题生成等）
