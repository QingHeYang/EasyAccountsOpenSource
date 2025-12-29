# 财务分析

> Analysis Controller

## 接口列表

### 1. 财务分析

**接口路径**: `GET /analysis/doAnalysis`

#### 请求参数

- **end** (查询参数, 可选): string - end
- **start** (查询参数, 必填): string - start

#### 响应结果

```json
{
  "code": "integer",
  "data": {
    "currentCircle": "string",
    "momCircle": "string",
    "momList": [{
      "compareIncrease": "number",
      "compareMoney": "number",
      "compareRate": "string",
      "id": "integer",
      "money": "number",
      "name": "string",
      "parent": "integer",
      "root": "boolean"
    }],
    "yoyCircle": "string",
    "yoyList": [{
      "compareIncrease": "number",
      "compareMoney": "number",
      "compareRate": "string",
      "id": "integer",
      "money": "number",
      "name": "string",
      "parent": "integer",
      "root": "boolean"
    }]
  },
  "msg": "string"
}
```

#### 认证要求

需要 UUID 认证

---

### 2. 导出Excel

**接口路径**: `GET /analysis/exportExcel`

#### 请求参数

- **end** (查询参数, 可选): string - end
- **start** (查询参数, 必填): string - start

#### 响应结果

```json
{
  "code": "integer",
  "data": {
    "allAsset": "string",
    "currentMonth": "string",
    "excelAccounts": [{
      "aname": "string",
      "card": "string",
      "createTime": "string",
      "disable": "boolean",
      "exemptMoney": "string",
      "id": "integer",
      "money": "string",
      "note": "string"
    }],
    "flow": [{
      "accountName": "string",
      "actionName": "string",
      "flowDate": "string",
      "money": "string",
      "note": "string",
      "typeName": "string"
    }],
    "monthTotalEarn": "string",
    "monthTotalIn": "string",
    "monthTotalOut": "string"
  },
  "msg": "string"
}
```

#### 认证要求

需要 UUID 认证

---

### 3. 获取时间内收支分类列表

**接口路径**: `POST /analysis/v2/getAnalysisTypeList`

#### 请求参数


**请求体 (analysisTypeListRequestDto)**:
```json
{
  "combineSubType": "boolean",
  "end": "string",
  "showDisableAnalysisType": "boolean",
  "start": "string"
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

### 4. 获取时间内收支分类每月数据

**接口路径**: `POST /analysis/v2/getAnalysisTypeMonthData`

#### 请求参数


**请求体 (typeRequestDto)**:
```json
{
  "end": "string",
  "start": "string",
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

