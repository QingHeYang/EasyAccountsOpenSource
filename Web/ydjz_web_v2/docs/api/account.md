# 账户管理

> Account Controller

## 接口列表

### 1. 添加账户

**接口路径**: `POST /account/addAccount`

#### 请求参数


**请求体 (accountRequestDto)**:
```json
{
  "card": "string",
  "exemptMoney": "string",
  "money": "string",
  "name": "string",
  "note": "string"
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

### 2. 停用账户

**接口路径**: `DELETE /account/deleteAccount/{id}`

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

### 3. 获取全部账户

**接口路径**: `GET /account/getAccount`

#### 请求参数

无参数
#### 响应结果

```json
{
  "code": "integer",
  "data": [{
    "card": "string",
    "createTime": "string",
    "exemptMoney": "string",
    "id": "integer",
    "money": "string",
    "name": "string",
    "note": "string"
  }],
  "msg": "string"
}
```

#### 认证要求

需要 UUID 认证

---

### 4. 获取指定账户

**接口路径**: `GET /account/getAccount/{id}`

#### 请求参数

- **id** (路径参数): integer - id

#### 响应结果

```json
{
  "code": "integer",
  "data": {
    "card": "string",
    "createTime": "string",
    "exemptMoney": "string",
    "id": "integer",
    "money": "string",
    "name": "string",
    "note": "string"
  },
  "msg": "string"
}
```

#### 认证要求

需要 UUID 认证

---

### 5. getAllAccountNoLimit

**接口路径**: `GET /account/getAccountNoLimit`

#### 请求参数

无参数
#### 响应结果

```json
{
  "code": "integer",
  "data": [{
    "card": "string",
    "createTime": "string",
    "exemptMoney": "string",
    "id": "integer",
    "money": "string",
    "name": "string",
    "note": "string"
  }],
  "msg": "string"
}
```

#### 认证要求

需要 UUID 认证

---

### 6. 更新账户

**接口路径**: `PUT /account/updateAccount/{id}`

#### 请求参数


**请求体 (accountRequestDto)**:
```json
{
  "card": "string",
  "exemptMoney": "string",
  "money": "string",
  "name": "string",
  "note": "string"
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

