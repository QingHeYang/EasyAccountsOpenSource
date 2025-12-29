# 角色层（Role Layer）

角色层定义AI的身份、性格特征和角色扮演相关的内容。

## 目录结构

每个角色可以有自己的子目录，包含：
- `identity.prompt` - 身份定义
- `behavior.prompt` - 行为特征
- `knowledge.prompt` - 专业知识背景

## 数据来源

主要从`.role`文件中读取的8个字段：
- `role` - 角色定义
- `cos_role` - 特殊身份
- `name` - 名字
- `character` - 性格特征
- `user_role` - 对话者角色
- `user_role_description` - 对话者描述
- `user_scene` - 对话场景
- `location` - 所在位置

## 设计原则

1. **个性化**：每个角色有独特的特征
2. **一致性**：行为符合角色设定
3. **情境化**：考虑对话场景
4. **关系化**：明确与用户的关系

## 占位符

角色层提示词支持以下占位符：
- `{role}` - 角色名称
- `{name}` - AI名字
- `{character}` - 性格描述
- `{user_role}` - 用户角色
- 等等...