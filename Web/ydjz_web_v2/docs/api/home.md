# 首页信息

> Home Controller

## 接口列表

### 1. 获取首页信息

**接口路径**: `GET /home/getHomeInfo`

#### 请求参数

无参数
#### 响应结果

```json
{
  "code": "integer",
  "data": {
    "accounts": [{
      "accountAsset": "string",
      "accountName": "string",
      "exemptAsset": "string",
      "id": "integer",
      "note": "string",
      "percent": "string"
    }],
    "curIncome": "string",
    "curOutCome": "string",
    "monthDetails": [{
      "balance": "string",
      "income": "string",
      "month": "string",
      "outcome": "string"
    }],
    "netAsset": "string",
    "totalAsset": "string",
    "yearBalance": "string",
    "yearIncome": "string",
    "yearOutCome": "string"
  },
  "msg": "string"
}
```

#### 认证要求

需要 UUID 认证

---

### 2. V2版本获取首页信息

**接口路径**: `GET /home/getHomeInfoV2/{year}`

#### 请求参数

- **year** (路径参数): integer - year

#### 响应结果

```json
{
  "code": "integer",
  "data": {
    "accounts": [{
      "accountAsset": "string",
      "accountName": "string",
      "exemptAsset": "string",
      "id": "integer",
      "note": "string",
      "percent": "string"
    }],
    "curIncome": "string",
    "curOutCome": "string",
    "monthDetails": [{
      "balance": "string",
      "income": "string",
      "month": "string",
      "outcome": "string"
    }],
    "netAsset": "string",
    "totalAsset": "string",
    "yearBalance": "string",
    "yearIncome": "string",
    "yearOutCome": "string"
  },
  "msg": "string"
}
```

#### 认证要求

需要 UUID 认证

---

### 3. 获取版本信息

**接口路径**: `GET /home/getVersion`

#### 请求参数

无参数
#### 响应结果

```json
{
  "code": "integer",
  "data": {
    "backendBranch": "string",
    "fontBranch": "string",
    "mysqlBranch": "string",
    "release": "string"
  },
  "msg": "string"
}
```

#### 认证要求

需要 UUID 认证

---

