# 快记模板

> Flow Template Controller

## 接口列表

### 1. 添加模板

**接口路径**: `POST /template/addTemplate`

#### 请求参数


**请求体 (flowTemplateRequestDto)**:
```json
{
  "accountId": "integer",
  "accountToId": "integer",
  "actionId": "integer",
  "dateType": "integer",
  "id": "integer",
  "money": "string",
  "name": "string",
  "tagId": "integer",
  "typeId": "integer"
}
```

#### 响应结果

```json
{
  "code": "integer",
  "data": "object",
  "msg": "string"
}
```

#### 认证要求

需要 UUID 认证

---

### 2. 删除模板

**接口路径**: `DELETE /template/deleteTemplate/{id}`

#### 请求参数

- **id** (路径参数): integer - id

#### 响应结果

```json
{
  "code": "integer",
  "data": "object",
  "msg": "string"
}
```

#### 认证要求

需要 UUID 认证

---

### 3. 获取全部模板

**接口路径**: `GET /template/getAllTemplates`

#### 请求参数

无参数
#### 响应结果

```json
{
  "code": "integer",
  "data": [{
    "account": {
      "card": "string",
      "createTime": "string",
      "exemptMoney": "string",
      "id": "integer",
      "money": "string",
      "name": "string",
      "note": "string"
    },
    "accountId": "integer",
    "accountTo": {
      "card": "string",
      "createTime": "string",
      "exemptMoney": "string",
      "id": "integer",
      "money": "string",
      "name": "string",
      "note": "string"
    },
    "accountToId": "integer",
    "action": {
      "exempt": "boolean",
      "handle": "integer",
      "hname": "string",
      "id": "integer"
    },
    "actionId": "integer",
    "dateType": "integer",
    "id": "integer",
    "money": "string",
    "name": "string",
    "tag": {
      "color": "string",
      "id": "integer",
      "name": "string"
    },
    "tagId": "integer",
    "type": {
      "action": {
        "exempt": "boolean",
        "handle": "integer",
        "hname": "string",
        "id": "integer"
      },
      "analysisDisable": "boolean",
      "archive": "boolean",
      "childrenTypes": [{ /* circular reference to TypeListResponseDto */ }],
      "disable": "boolean",
      "hasChild": "boolean",
      "id": "integer",
      "parent": "integer",
      "tname": "string"
    },
    "typeId": "integer"
  }],
  "msg": "string"
}
```

#### 认证要求

需要 UUID 认证

---

### 4. 根据TagId获取全部模板

**接口路径**: `GET /template/getAllTemplatesByTag/{tagId}`

#### 请求参数

- **tagId** (路径参数): integer - tagId

#### 响应结果

```json
{
  "code": "integer",
  "data": [{
    "account": {
      "card": "string",
      "createTime": "string",
      "exemptMoney": "string",
      "id": "integer",
      "money": "string",
      "name": "string",
      "note": "string"
    },
    "accountId": "integer",
    "accountTo": {
      "card": "string",
      "createTime": "string",
      "exemptMoney": "string",
      "id": "integer",
      "money": "string",
      "name": "string",
      "note": "string"
    },
    "accountToId": "integer",
    "action": {
      "exempt": "boolean",
      "handle": "integer",
      "hname": "string",
      "id": "integer"
    },
    "actionId": "integer",
    "dateType": "integer",
    "id": "integer",
    "money": "string",
    "name": "string",
    "tag": {
      "color": "string",
      "id": "integer",
      "name": "string"
    },
    "tagId": "integer",
    "type": {
      "action": {
        "exempt": "boolean",
        "handle": "integer",
        "hname": "string",
        "id": "integer"
      },
      "analysisDisable": "boolean",
      "archive": "boolean",
      "childrenTypes": [{ /* circular reference to TypeListResponseDto */ }],
      "disable": "boolean",
      "hasChild": "boolean",
      "id": "integer",
      "parent": "integer",
      "tname": "string"
    },
    "typeId": "integer"
  }],
  "msg": "string"
}
```

#### 认证要求

需要 UUID 认证

---

### 5. 获取单个模板

**接口路径**: `GET /template/getTemplateById/{id}`

#### 请求参数

- **id** (路径参数): integer - id

#### 响应结果

```json
{
  "code": "integer",
  "data": {
    "account": {
      "card": "string",
      "createTime": "string",
      "exemptMoney": "string",
      "id": "integer",
      "money": "string",
      "name": "string",
      "note": "string"
    },
    "accountId": "integer",
    "accountTo": {
      "card": "string",
      "createTime": "string",
      "exemptMoney": "string",
      "id": "integer",
      "money": "string",
      "name": "string",
      "note": "string"
    },
    "accountToId": "integer",
    "action": {
      "exempt": "boolean",
      "handle": "integer",
      "hname": "string",
      "id": "integer"
    },
    "actionId": "integer",
    "dateType": "integer",
    "id": "integer",
    "money": "string",
    "name": "string",
    "tag": {
      "color": "string",
      "id": "integer",
      "name": "string"
    },
    "tagId": "integer",
    "type": {
      "action": {
        "exempt": "boolean",
        "handle": "integer",
        "hname": "string",
        "id": "integer"
      },
      "analysisDisable": "boolean",
      "archive": "boolean",
      "childrenTypes": [{ /* circular reference to TypeListResponseDto */ }],
      "disable": "boolean",
      "hasChild": "boolean",
      "id": "integer",
      "parent": "integer",
      "tname": "string"
    },
    "typeId": "integer"
  },
  "msg": "string"
}
```

#### 认证要求

需要 UUID 认证

---

### 6. 更新模板

**接口路径**: `PUT /template/updateTemplate`

#### 请求参数


**请求体 (flowTemplateRequestDto)**:
```json
{
  "accountId": "integer",
  "accountToId": "integer",
  "actionId": "integer",
  "dateType": "integer",
  "id": "integer",
  "money": "string",
  "name": "string",
  "tagId": "integer",
  "typeId": "integer"
}
```

#### 响应结果

```json
{
  "code": "integer",
  "data": "object",
  "msg": "string"
}
```

#### 认证要求

需要 UUID 认证

---

