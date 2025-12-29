# 收支管理

> Action Controller

## 接口列表

### 1. 添加收支

**接口路径**: `POST /action/addAction`

#### 请求参数


**请求体 (action)**:
```json
{
  "exempt": "boolean",
  "handle": "integer",
  "hname": "string",
  "id": "integer"
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

### 2. 获取全部收支

**接口路径**: `GET /action/getAction`

#### 请求参数

无参数
#### 响应结果

```json
{
  "code": "integer",
  "data": [{
    "exempt": "boolean",
    "handle": "integer",
    "hname": "string",
    "id": "integer"
  }],
  "msg": "string"
}
```

#### 认证要求

需要 UUID 认证

---

### 3. 获取指定收支

**接口路径**: `GET /action/getAction/{id}`

#### 请求参数

- **id** (路径参数): integer - id

#### 响应结果

```json
{
  "code": "integer",
  "data": {
    "exempt": "boolean",
    "handle": "integer",
    "hname": "string",
    "id": "integer"
  },
  "msg": "string"
}
```

#### 认证要求

需要 UUID 认证

---

### 4. 更新收支

**接口路径**: `PUT /action/updateAction/{id}`

#### 请求参数


**请求体 (action)**:
```json
{
  "exempt": "boolean",
  "handle": "integer",
  "hname": "string",
  "id": "integer"
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

