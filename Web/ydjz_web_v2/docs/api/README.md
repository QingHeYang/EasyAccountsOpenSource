# API 文档总览

> EasyAccounts 后台接口文档 vv2.4.0

下列接口均为nginx前端请求使用接口

## 基础信息

- **Base URL**: `www.lllama.cn:10672/`
- **版本**: v2.4.0
- **联系人**: [Mercy](https://github.com/QingHeYang/EasyAccounts)
- **许可证**: [MIT License](https://github.com/QingHeYang/EasyAccounts?tab=MIT-1-ov-file)

## 认证方式

大部分接口需要在请求头中携带 UUID 进行认证。

## API 模块

### [账户管理](./account.md)

> Account Controller

**接口数量**: 6

**主要接口**:

- `POST /account/addAccount` - 添加账户
- `DELETE /account/deleteAccount/{id}` - 停用账户
- `GET /account/getAccount` - 获取全部账户
- `GET /account/getAccount/{id}` - 获取指定账户
- `GET /account/getAccountNoLimit` - getAllAccountNoLimit
- ...[查看更多](./account.md)

### [收支管理](./action.md)

> Action Controller

**接口数量**: 4

**主要接口**:

- `POST /action/addAction` - 添加收支
- `GET /action/getAction` - 获取全部收支
- `GET /action/getAction/{id}` - 获取指定收支
- `PUT /action/updateAction/{id}` - 更新收支

### [财务分析](./analysis.md)

> Analysis Controller

**接口数量**: 4

**主要接口**:

- `GET /analysis/doAnalysis` - 财务分析
- `GET /analysis/exportExcel` - 导出Excel
- `POST /analysis/v2/getAnalysisTypeList` - 获取时间内收支分类列表
- `POST /analysis/v2/getAnalysisTypeMonthData` - 获取时间内收支分类每月数据

### [登录注册](./auth.md)

> Auth Controller

**接口数量**: 2

**主要接口**:

- `POST /auth/login` - 登录
- `POST /auth/register` - 注册

### [流水管理](./flow.md)

> Flow Controller

**接口数量**: 7

**主要接口**:

- `POST /flow/addFlow` - 添加流水
- `PUT /flow/collectFlow/{id}/{collect}` - 收藏流水
- `DELETE /flow/deleteFlow/{id}` - 删除流水
- `GET /flow/getFlow/{id}` - 获取指定一笔流水
- `GET /flow/getFlowListMain/{chooseHandle}/{chooseOrder}/{date}` - 获取主业流水
- ...[查看更多](./flow.md)

### [首页信息](./home.md)

> Home Controller

**接口数量**: 3

**主要接口**:

- `GET /home/getHomeInfo` - 获取首页信息
- `GET /home/getHomeInfoV2/{year}` - V2版本获取首页信息
- `GET /home/getVersion` - 获取版本信息

### [图片管理](./image.md)

> Image Controller

**接口数量**: 2

**主要接口**:

- `POST /image/upload` - 上传图片
- `GET /image/{fileName}` - 获取图片

### [筛选功能](./screen.md)

> Screen Controller

**接口数量**: 3

**主要接口**:

- `POST /screen/getFlowByScreen` - 获取筛选功能
- `POST /screen/makeExcel` - 生成Excel
- `POST /screen/makeScreenExcel` - makeScreenExcel

### [模板标签管理](./tag.md)

> Tag Controller

**接口数量**: 5

**主要接口**:

- `POST /tag/addTag` - 添加标签
- `DELETE /tag/deleteTag/{id}` - 停用标签
- `GET /tag/getTag/{id}` - 获取指定标签
- `GET /tag/getTags` - 获取全部标签
- `PUT /tag/updateTag` - 更新标签

### [快记模板](./flow-template.md)

> Flow Template Controller

**接口数量**: 6

**主要接口**:

- `POST /template/addTemplate` - 添加模板
- `DELETE /template/deleteTemplate/{id}` - 删除模板
- `GET /template/getAllTemplates` - 获取全部模板
- `GET /template/getAllTemplatesByTag/{tagId}` - 根据TagId获取全部模板
- `GET /template/getTemplateById/{id}` - 获取单个模板
- ...[查看更多](./flow-template.md)

### [分类管理](./type.md)

> Type Controller

**接口数量**: 10

**主要接口**:

- `POST /type/addType` - 添加分类
- `PUT /type/archiveType/{id}` - 归档分类
- `DELETE /type/deleteType/{id}` - 停用分类
- `GET /type/getType` - 获取所有分类
- `GET /type/getType/noLimit` - 获取所有分类（无归档、停用限制）
- ...[查看更多](./type.md)

## 快速开始

### 1. 登录获取 Token

```bash
curl -X POST "http://www.lllama.cn:10672/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```

### 2. 使用 Token 访问受保护接口

```bash
curl -X GET "http://www.lllama.cn:10672/account/getAccount" \
  -H "UUID: your_token_here"
```

## 通用响应格式

所有接口返回的数据都遵循以下格式:

```json
{
  "code": 200,        // 状态码
  "message": "成功",  // 提示信息
  "data": {}          // 业务数据
}
```

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器错误 |

## 更新日志

当前版本: **v2.4.0**

查看 [OpenAPI 规范文件](./openapi.json) 获取完整的接口定义。
