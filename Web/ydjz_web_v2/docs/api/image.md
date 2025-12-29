# 图片管理

> Image Controller

## 接口列表

### 1. 上传图片

**接口路径**: `POST /image/upload`

#### 请求参数


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

### 2. 获取图片

**接口路径**: `GET /image/{fileName}`

#### 请求参数

- **fileName** (路径参数): string - fileName

#### 响应结果

```json
{
  "description": "string",
  "file": {
    "absolute": "boolean",
    "absoluteFile": { /* circular reference to File */ },
    "absolutePath": "string",
    "canonicalFile": { /* circular reference to File */ },
    "canonicalPath": "string",
    "directory": "boolean",
    "file": "boolean",
    "freeSpace": "integer",
    "hidden": "boolean",
    "name": "string",
    "parent": "string",
    "parentFile": { /* circular reference to File */ },
    "path": "string",
    "totalSpace": "integer",
    "usableSpace": "integer"
  },
  "filename": "string",
  "inputStream": {},
  "open": "boolean",
  "readable": "boolean",
  "uri": {
    "absolute": "boolean",
    "authority": "string",
    "fragment": "string",
    "host": "string",
    "opaque": "boolean",
    "path": "string",
    "port": "integer",
    "query": "string",
    "rawAuthority": "string",
    "rawFragment": "string",
    "rawPath": "string",
    "rawQuery": "string",
    "rawSchemeSpecificPart": "string",
    "rawUserInfo": "string",
    "scheme": "string",
    "schemeSpecificPart": "string",
    "userInfo": "string"
  },
  "url": {
    "authority": "string",
    "content": "object",
    "defaultPort": "integer",
    "file": "string",
    "host": "string",
    "path": "string",
    "port": "integer",
    "protocol": "string",
    "query": "string",
    "ref": "string",
    "userInfo": "string"
  }
}
```

#### 认证要求

需要 UUID 认证

---

