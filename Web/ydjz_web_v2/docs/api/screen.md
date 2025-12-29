# 筛选功能

> Screen Controller

## 接口列表

### 1. 获取筛选功能

**接口路径**: `POST /screen/getFlowByScreen`

#### 请求参数


**请求体 (screenFlowRequestDto)**:
```json
{
  "accountId": "integer",
  "actions": [],
  "chooseHandle": "integer",
  "collect": "boolean",
  "endDate": "string",
  "note": "string",
  "singleMonth": "boolean",
  "startDate": "string",
  "types": []
}
```

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

### 2. 生成Excel

**接口路径**: `POST /screen/makeExcel`

#### 请求参数

- **excelName** (查询参数, 必填): string - excelName

**请求体 (screenFlowRequestDto)**:
```json
{
  "accountId": "integer",
  "actions": [],
  "chooseHandle": "integer",
  "collect": "boolean",
  "endDate": "string",
  "note": "string",
  "singleMonth": "boolean",
  "startDate": "string",
  "types": []
}
```

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

### 3. makeScreenExcel

**接口路径**: `POST /screen/makeScreenExcel`

> ⚠️ **已废弃**

#### 请求参数


**请求体 (screenFlowRequestDto)**:
```json
{
  "accountId": "integer",
  "actions": [],
  "chooseHandle": "integer",
  "collect": "boolean",
  "endDate": "string",
  "note": "string",
  "singleMonth": "boolean",
  "startDate": "string",
  "types": []
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

