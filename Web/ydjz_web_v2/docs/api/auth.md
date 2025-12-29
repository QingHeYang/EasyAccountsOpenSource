# 登录注册

> Auth Controller

## 接口列表

### 1. 登录

**接口路径**: `POST /auth/login`

#### 请求参数


**请求体 (authRequestDto)**:
```json
{
  "password": "string",
  "username": "string"
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

### 2. 注册

**接口路径**: `POST /auth/register`

#### 请求参数


**请求体 (authRequestDto)**:
```json
{
  "password": "string",
  "username": "string"
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

