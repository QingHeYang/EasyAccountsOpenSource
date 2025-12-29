# 模板标签管理

> Tag Controller

## 接口列表

### 1. 添加标签

**接口路径**: `POST /tag/addTag`

#### 请求参数


**请求体 (templateTag)**:
```json
{
  "color": "string",
  "id": "integer",
  "name": "string"
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

### 2. 停用标签

**接口路径**: `DELETE /tag/deleteTag/{id}`

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

### 3. 获取指定标签

**接口路径**: `GET /tag/getTag/{id}`

#### 请求参数

- **id** (路径参数): integer - id

#### 响应结果

```json
{
  "code": "integer",
  "data": {
    "color": "string",
    "id": "integer",
    "name": "string"
  },
  "msg": "string"
}
```

#### 认证要求

需要 UUID 认证

---

### 4. 获取全部标签

**接口路径**: `GET /tag/getTags`

#### 请求参数

无参数
#### 响应结果

```json
{
  "code": "integer",
  "data": [{
    "color": "string",
    "id": "integer",
    "name": "string"
  }],
  "msg": "string"
}
```

#### 认证要求

需要 UUID 认证

---

### 5. 更新标签

**接口路径**: `PUT /tag/updateTag`

#### 请求参数


**请求体 (templateTagDetails)**:
```json
{
  "color": "string",
  "id": "integer",
  "name": "string"
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

