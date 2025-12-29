# 分类管理

> Type Controller

## 接口列表

### 1. 添加分类

**接口路径**: `POST /type/addType`

#### 请求参数


**请求体 (type)**:
```json
{
  "actionId": "integer",
  "analysisDisable": "boolean",
  "archive": "boolean",
  "disable": "boolean",
  "id": "integer",
  "parent": "integer",
  "tname": "string"
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

### 2. 归档分类

**接口路径**: `PUT /type/archiveType/{id}`

#### 请求参数

- **archive** (查询参数, 必填): boolean - archive
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

### 3. 停用分类

**接口路径**: `DELETE /type/deleteType/{id}`

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

### 4. 获取所有分类

**接口路径**: `GET /type/getType`

#### 请求参数

无参数
#### 响应结果

```json
{
  "code": "integer",
  "data": [{
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
  }],
  "msg": "string"
}
```

#### 认证要求

需要 UUID 认证

---

### 5. 获取所有分类（无归档、停用限制）

**接口路径**: `GET /type/getType/noLimit`

#### 请求参数

无参数
#### 响应结果

```json
{
  "code": "integer",
  "data": [{
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
  }],
  "msg": "string"
}
```

#### 认证要求

需要 UUID 认证

---

### 6. 获取二级指定分类

**接口路径**: `GET /type/getType/{parent}`

#### 请求参数

- **parent** (路径参数): integer - parent

#### 响应结果

```json
{
  "code": "integer",
  "data": [{
    "action": {
      "exempt": "boolean",
      "handle": "integer",
      "hname": "string",
      "id": "integer"
    },
    "actionId": "integer",
    "analysisDisable": "boolean",
    "archive": "boolean",
    "disable": "boolean",
    "hasChild": "boolean",
    "id": "integer",
    "parent": "integer",
    "tname": "string"
  }],
  "msg": "string"
}
```

#### 认证要求

需要 UUID 认证

---

### 7. 获取归档分类

**接口路径**: `GET /type/getTypeArchive`

#### 请求参数

无参数
#### 响应结果

```json
{
  "code": "integer",
  "data": [{
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
  }],
  "msg": "string"
}
```

#### 认证要求

需要 UUID 认证

---

### 8. 获取指定收支的分类

**接口路径**: `GET /type/getTypeByActionId/{actionId}`

#### 请求参数

- **actionId** (路径参数): integer - actionId

#### 响应结果

```json
{
  "code": "integer",
  "data": [{
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
  }],
  "msg": "string"
}
```

#### 认证要求

需要 UUID 认证

---

### 9. 获取单个分类

**接口路径**: `GET /type/getTypeSingle/{id}`

#### 请求参数

- **id** (路径参数): integer - id

#### 响应结果

```json
{
  "code": "integer",
  "data": {
    "action": {
      "exempt": "boolean",
      "handle": "integer",
      "hname": "string",
      "id": "integer"
    },
    "actionId": "integer",
    "analysisDisable": "boolean",
    "archive": "boolean",
    "disable": "boolean",
    "hasChild": "boolean",
    "id": "integer",
    "parent": "integer",
    "tname": "string"
  },
  "msg": "string"
}
```

#### 认证要求

需要 UUID 认证

---

### 10. 更新分类

**接口路径**: `PUT /type/updateType/{id}`

#### 请求参数

- **id** (路径参数): integer - id

**请求体 (type)**:
```json
{
  "actionId": "integer",
  "analysisDisable": "boolean",
  "archive": "boolean",
  "disable": "boolean",
  "id": "integer",
  "parent": "integer",
  "tname": "string"
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

