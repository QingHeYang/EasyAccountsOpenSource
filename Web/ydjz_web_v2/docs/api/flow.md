# 流水管理

> Flow Controller

## 接口列表

### 1. 添加流水

**接口路径**: `POST /flow/addFlow`

#### 请求参数


**请求体 (flowAddRequestDto)**:
```json
{
  "accountId": "integer",
  "accountToId": "integer",
  "actionId": "integer",
  "collect": "boolean",
  "createDate": "string",
  "fDate": "string",
  "from": "string",
  "images": [],
  "money": "string",
  "note": "string",
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

### 2. 收藏流水

**接口路径**: `PUT /flow/collectFlow/{id}/{collect}`

#### 请求参数

- **collect** (路径参数): integer - collect
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

### 3. 删除流水

**接口路径**: `DELETE /flow/deleteFlow/{id}`

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

### 4. 获取指定一笔流水

**接口路径**: `GET /flow/getFlow/{id}`

#### 请求参数

- **id** (路径参数): integer - id

#### 响应结果

```json
{
  "code": "integer",
  "data": {
    "account": {
      "aname": "string",
      "card": "string",
      "createTime": "string",
      "disable": "boolean",
      "exemptMoney": "string",
      "id": "integer",
      "money": "string",
      "note": "string"
    },
    "accountTo": {
      "aname": "string",
      "card": "string",
      "createTime": "string",
      "disable": "boolean",
      "exemptMoney": "string",
      "id": "integer",
      "money": "string",
      "note": "string"
    },
    "action": {
      "exempt": "boolean",
      "handle": "integer",
      "hname": "string",
      "id": "integer"
    },
    "collect": "boolean",
    "fdate": "string",
    "from": "string",
    "id": "integer",
    "images": [],
    "money": "string",
    "note": "string",
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
    }
  },
  "msg": "string"
}
```

#### 认证要求

需要 UUID 认证

---

### 5. 获取主业流水

**接口路径**: `GET /flow/getFlowListMain/{chooseHandle}/{chooseOrder}/{date}`

#### 请求参数

- **chooseHandle** (路径参数): integer - chooseHandle
- **chooseOrder** (路径参数): integer - chooseOrder
- **date** (路径参数): string - date

#### 响应结果

```json
{
  "code": "integer",
  "data": {
    "flows": [{
      "aname": "string",
      "collect": "boolean",
      "exempt": "boolean",
      "fdate": "string",
      "from": "string",
      "handle": "integer",
      "hasImages": "boolean",
      "hname": "string",
      "id": "integer",
      "money": "string",
      "note": "string",
      "tname": "string",
      "toAName": "string"
    }],
    "totalEarn": "string",
    "totalIn": "string",
    "totalOut": "string",
    "typeList": [{
      "children": [{ /* circular reference to FlowTypeDto */ }],
      "money": "string",
      "parent": "boolean",
      "typeId": "integer",
      "typeName": "string"
    }]
  },
  "msg": "string"
}
```

#### 认证要求

需要 UUID 认证

---

### 6. 月度流水Excel

**接口路径**: `GET /flow/makeExcel/{date}`

#### 请求参数

- **date** (路径参数): string - date

#### 响应结果

```json
{
  "code": "integer",
  "data": {
    "log": "string",
    "success": "boolean"
  },
  "msg": "string"
}
```

#### 认证要求

需要 UUID 认证

---

### 7. 更新流水

**接口路径**: `PUT /flow/updateFlow/{id}`

#### 请求参数


**请求体 (flowAddRequestDto)**:
```json
{
  "accountId": "integer",
  "accountToId": "integer",
  "actionId": "integer",
  "collect": "boolean",
  "createDate": "string",
  "fDate": "string",
  "from": "string",
  "images": [],
  "money": "string",
  "note": "string",
  "typeId": "integer"
}
```
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

