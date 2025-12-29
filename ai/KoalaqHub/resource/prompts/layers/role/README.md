# 角色层（Role Layer）

角色层定义AI的身份、性格特征。

## 文件说明

- `default.prompt` - 通用角色模板

## 数据来源

从 `resource/role/*.role` 文件读取，支持以下字段：
- `role` - 角色定义
- `cos_role` - 特殊身份
- `name` - 名字
- `character` - 性格特征
- `user_role` - 对话者角色
- `user_role_description` - 对话者描述
- `user_scene` - 对话场景
- `location` - 所在位置

## 占位符替换

模板中的 `{字段名}` 会被 `.role` 文件中的对应值替换。

示例：
```
你是{name}，一位{role}。
```
→
```
你是小U，一位恒银科技制造的专业的sqlite数据库数据查询员。
```
