# Excel 生成运行流程

本文档详细介绍 EasyAccounts Server 模块中 Excel 导出功能的完整运行流程，包括三种类型的 Excel 生成：月度账单、筛选账单和财务分析报表。

---

## 目录

1. [功能概述](#功能概述)
2. [技术栈](#技术栈)
3. [模板文件](#模板文件)
4. [配置项](#配置项)
5. [月度账单 Excel 流程](#月度账单-excel-流程)
6. [筛选账单 Excel 流程](#筛选账单-excel-流程)
7. [财务分析 Excel 流程](#财务分析-excel-流程)
8. [WebHook 通知流程](#webhook-通知流程)
9. [数据模型定义](#数据模型定义)
10. [错误处理](#错误处理)

---

## 功能概述

系统提供三种 Excel 导出功能：

| 类型 | 接口 | 服务类 | 模板文件 | 说明 |
|------|------|--------|----------|------|
| 月度账单 | `GET /flow/makeExcel/{date}` | ExcelService | auto_excel.xls | 导出指定月份的所有流水 |
| 筛选账单 | `POST /screen/makeExcel` | ScreenService | screen_excel.xls | 按条件筛选导出流水 |
| 财务分析 | `GET /analysis/exportExcel` | AnalysisService | analysis_excel.xls | 导出财务分析报表（含同比环比） |

---

## 技术栈

| 组件 | 版本 | 用途 |
|------|------|------|
| EasyExcel | 2.2.4 | 阿里巴巴开源 Excel 处理库 |
| Apache POI | - | EasyExcel 底层依赖 |
| OkHttp | 4.9.1 | WebHook 文件上传 |

**核心依赖：**
```xml
<dependency>
    <groupId>com.alibaba</groupId>
    <artifactId>easyexcel</artifactId>
    <version>2.2.4</version>
</dependency>
```

---

## 模板文件

### 模板位置

```
Server/excel_template/
├── auto_excel.xls      # 月度账单模板 (28KB)
├── screen_excel.xls    # 筛选账单模板 (36KB)
└── analysis_excel.xls  # 财务分析模板 (26KB)
```

> **注意：** 模板文件不应修改，它们定义了 Excel 的格式和样式。

### 模板占位符

EasyExcel 使用模板填充模式，模板中的占位符格式为 `{fieldName}` 或 `{.fieldName}`（列表项）。

**月度账单模板占位符：**
- `{currentMonth}` - 当前月份
- `{monthTotalIn}` - 月总收入
- `{monthTotalOut}` - 月总支出
- `{monthTotalEarn}` - 月结余
- `{allAsset}` - 总资产
- `{flow.flowDate}` - 流水日期
- `{flow.actionName}` - 操作类型
- `{flow.typeName}` - 分类名称
- `{flow.accountName}` - 账户名称
- `{flow.money}` - 金额
- `{flow.note}` - 备注

---

## 配置项

### application.properties 配置

```properties
# 月度账单 Excel
baseAutoExcel = /Ledger/excel_template/auto_excel.xls
excelAutoFolder = /Ledger/excel/month/

# 筛选账单 Excel
baseScreenExcel = /Ledger/excel_template/screen_excel.xls
excelScreenFolder = /Ledger/excel/screen/

# 财务分析 Excel
baseAnalysisExcel = /Ledger/excel_template/analysis_excel.xls
excelAnalysisFolder = /Ledger/excel/analysis/

# WebHook 地址
webhook_url = http://webhook:8083/webhook
```

### 配置项说明

| 配置项 | 说明 |
|--------|------|
| `baseAutoExcel` | 月度账单模板路径 |
| `excelAutoFolder` | 月度账单输出目录 |
| `baseScreenExcel` | 筛选账单模板路径 |
| `excelScreenFolder` | 筛选账单输出目录 |
| `baseAnalysisExcel` | 财务分析模板路径 |
| `excelAnalysisFolder` | 财务分析输出目录 |
| `webhook_url` | WebHook 服务地址 |

---

## 月度账单 Excel 流程

### 接口定义

```
GET /flow/makeExcel/{date}

路径参数：
- date: 月份 (格式: yyyy-MM，如 "2024-01")

响应：
{
    "code": 0,
    "msg": "Success",
    "data": {
        "log": "文件生成成功\n调用webhook成功\n邮件发送成功",
        "success": true
    }
}
```

### 完整流程图

```
┌──────────────────────────────────────────────────────────────────┐
│                      FlowController                               │
│  GET /flow/makeExcel/{date}                                      │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                      ExcelService                                 │
│  makeMonthExcel(dateStr)                                         │
│                                                                   │
│  1. 解析日期字符串 (yyyy-MM)                                      │
│  2. 调用 getExcelForMonth(date) 获取数据                          │
│  3. 调用 writeMonthExcel(dateStr, data) 生成文件                  │
│  4. 返回结果字符串                                                │
└─────────────────────────────┬────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────────────┐
│   getExcelForMonth()    │     │      writeMonthExcel()          │
│                         │     │                                  │
│ 1. 查询当月流水数据      │     │ 1. 生成文件名:                   │
│    flowDao.getFlowByMain│     │    {date}月账单_{timestamp}.xls │
│                         │     │                                  │
│ 2. 遍历流水计算:         │     │ 2. 使用 EasyExcel 填充模板      │
│    - 总收入             │     │    - fill(data, writeSheet)     │
│    - 总支出             │     │    - FillWrapper("flow", flows) │
│    - 总结余             │     │    - FillWrapper("account", acc)│
│                         │     │                                  │
│ 3. 查询账户余额          │     │ 3. 调用 uploadExcel() 上传      │
│    accountService       │     │                                  │
│    .getAccountByDate()  │     │                                  │
│                         │     │                                  │
│ 4. 构建 MonthExcelData  │     │                                  │
└─────────────────────────┘     └─────────────────────────────────┘
                                              │
                                              ▼
                              ┌─────────────────────────────────┐
                              │      uploadExcel()              │
                              │                                  │
                              │ 1. 检查文件是否存在              │
                              │ 2. 调用 FileMakeWebHook         │
                              │    .sendFile() 发送到 WebHook   │
                              └─────────────────────────────────┘
```

### 代码流程详解

**1. 控制器入口 (FlowController.java:78-90)**

```java
@ApiOperation(value = "月度流水Excel")
@GetMapping("/makeExcel/{date}")
public BaseDto<ExcelDto> getExcel(@PathVariable String date) {
    // 调用 ExcelService 生成 Excel
    String result = excelService.makeMonthExcel(date);

    // 解析结果
    ExcelDto excelDto = new ExcelDto();
    String flag = result.substring(result.length() - 2);
    String log = result.substring(0, result.length() - 2);
    excelDto.setLog(log);
    excelDto.setSuccess(flag.contains("0"));  // "|0" 表示成功

    BaseDto baseDto = BaseDto.setSuccessBean();
    baseDto.setData(excelDto);
    return baseDto;
}
```

**2. 服务层主方法 (ExcelService.java:58-71)**

```java
public String makeMonthExcel(String dateStr) {
    SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM");
    try {
        // 1. 解析日期
        Date date = sdf.parse(dateStr);

        // 2. 获取数据
        MonthExcelData monthExcelData = getExcelForMonth(date);

        // 3. 写入 Excel
        String result = writeMonthExcel(dateStr, monthExcelData);

        return "文件生成成功" + result;
    } catch (ParseException e) {
        return "Excel生成失败|1";
    }
}
```

**3. 数据查询 (ExcelService.java:73-134)**

```java
private MonthExcelData getExcelForMonth(Date date) {
    // 1. 构建日期查询条件
    String curDate = sdf.format(date) + "%";  // 如 "2024-01%"

    // 2. 查询流水数据 (MyBatis)
    List<Map<String, Object>> flows = flowDao.getFlowByMain(3, 0, curDate);

    // 3. 遍历处理流水
    BigDecimal moneyIn = new BigDecimal("0");
    BigDecimal moneyOut = new BigDecimal("0");
    List<MonthExcelData.Flow> flowList = new ArrayList<>();

    for (Map<String, Object> map : flows) {
        MonthExcelData.Flow flow = new MonthExcelData.Flow();
        flow.setFlowDate(sdfDate.format(fDate));
        flow.setMoney("￥" + map.get("money"));

        // 处理分类名称（含父分类）
        if (map.get("p_t_name") != null) {
            flow.setTypeName(map.get("p_t_name") + "/" + map.get("t_name"));
        } else {
            flow.setTypeName((String) map.get("t_name"));
        }

        // 累计收入/支出
        if ((int) map.get("handle") == 1) {
            moneyOut = moneyOut.add(new BigDecimal((String) map.get("money")));
        } else if ((int) map.get("handle") == 0) {
            moneyIn = moneyIn.add(new BigDecimal((String) map.get("money")));
        }

        flowList.add(flow);
    }

    // 4. 查询账户余额
    List<Account> accounts = accountService.getAccountByDate(accountsDate);

    // 5. 构建返回对象
    MonthExcelData monthExcelData = new MonthExcelData();
    monthExcelData.setMonthTotalIn("￥" + moneyIn.toString());
    monthExcelData.setMonthTotalOut("￥" + moneyOut.toString());
    monthExcelData.setMonthTotalEarn("￥" + (moneyIn.subtract(moneyOut)).toString());
    monthExcelData.setFlow(flowList);
    monthExcelData.setExcelAccounts(excelAccounts);

    return monthExcelData;
}
```

**4. 写入 Excel (ExcelService.java:139-155)**

```java
private String writeMonthExcel(String excelDate, MonthExcelData monthExcelData) {
    // 1. 生成文件名
    Date date = new Date();
    String excelFileName = excelDate + "月账单_" + date.getTime() + ".xls";
    String excelPath = excelFolder + excelFileName;

    // 2. 使用 EasyExcel 填充模板
    ExcelWriter excelWriter = EasyExcel.write()
            .file(excelPath)
            .withTemplate(baseExcelPath)  // 使用模板
            .registerWriteHandler(new ExcelWriteHandler())  // 自定义样式处理器
            .build();

    WriteSheet writeSheet = EasyExcel.writerSheet().build();

    // 3. 填充数据
    excelWriter.fill(monthExcelData, writeSheet);  // 填充基本字段
    excelWriter.fill(new FillWrapper("flow", monthExcelData.getFlow()), writeSheet);  // 填充流水列表
    excelWriter.fill(new FillWrapper("account", monthExcelData.getExcelAccounts()), writeSheet);  // 填充账户列表

    // 4. 完成写入
    excelWriter.finish();

    // 5. 上传文件
    return uploadExcel(excelPath, excelFileName, excelDate);
}
```

**5. 自定义样式处理器 (ExcelService.java:169-199)**

```java
public static class ExcelWriteHandler implements CellWriteHandler {
    @Override
    public void afterCellDispose(...) {
        // 为每个单元格添加边框样式
        CellStyle cellStyle = cell.getCellStyle();
        cellStyle.setBorderBottom(BorderStyle.THIN);
        cellStyle.setBorderLeft(BorderStyle.THIN);
        cellStyle.setBorderRight(BorderStyle.THIN);
        cellStyle.setBorderTop(BorderStyle.THIN);
        cell.setCellStyle(cellStyle);
    }
}
```

---

## 筛选账单 Excel 流程

### 接口定义

```
POST /screen/makeExcel?excelName={name}

请求体：
{
    "chooseHandle": 0,        // 0:全部 1:支出 2:收入
    "accountId": 0,           // 账户ID，0表示全部
    "startDate": "2024-01-01",
    "endDate": "2024-12-31",
    "isSingleMonth": false,
    "collect": false,
    "note": "",
    "actions": [1, 2],        // 操作类型ID列表
    "types": [5, 6, 7]        // 分类ID列表
}

查询参数：
- excelName: Excel 文件名称

响应：
{
    "code": 0,
    "msg": "Success",
    "data": {
        "log": "文件生成成功",
        "success": true
    }
}
```

### 流程图

```
┌──────────────────────────────────────────────────────────────────┐
│                    ScreenController                               │
│  POST /screen/makeExcel?excelName=xxx                            │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    ScreenService                                  │
│  makeScreenExcel(screenFlowRequestDto, excelName)                │
│                                                                   │
│  1. 调用 getFlowByScreen() 获取筛选后的流水                       │
│  2. 检查数据是否为空                                              │
│  3. 构建 ScreenExcelData                                         │
│  4. 调用 doMakeExcel() 生成文件                                   │
│  5. 调用 uploadExcel() 上传                                       │
└─────────────────────────────┬────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────────────┐
│   getFlowByScreen()     │     │      doMakeExcel()              │
│                         │     │                                  │
│ 1. 查询流水数据          │     │ 1. 生成文件路径                  │
│    flowDao              │     │                                  │
│    .getFlowByScreen()   │     │ 2. EasyExcel 填充模板:          │
│                         │     │    - fill(excelBean, sheet)     │
│ 2. 按条件过滤:           │     │    - FillWrapper("flow", flows) │
│    - 分类筛选           │     │                                  │
│    - 操作类型筛选        │     │ 3. 完成写入                     │
│                         │     │                                  │
│ 3. 计算统计:             │     │                                  │
│    - 总收入/支出/结余    │     │                                  │
│    - 分类统计           │     │                                  │
│                         │     │                                  │
│ 4. 返回 FlowListDto     │     │                                  │
└─────────────────────────┘     └─────────────────────────────────┘
```

### 代码流程详解

**1. 服务层主方法 (ScreenService.java:186-212)**

```java
@Transactional(rollbackFor = Exception.class)
public String makeScreenExcel(ScreenFlowRequestDto screenFlowRequestDto,
                               String excelName) throws Exception {
    // 1. 获取筛选后的流水
    FlowListDto flowListDto = getFlowByScreen(screenFlowRequestDto);

    // 2. 检查数据
    if (flowListDto.getFlows().size() == 0) {
        return "筛选条件无数据|1";
    }

    // 3. 转换数据格式
    ScreenExcelData excelBean = new ScreenExcelData();
    excelBean.setFlow(new ArrayList<>());

    flowListDto.getFlows().forEach((item) -> {
        MonthExcelData.Flow flow = new MonthExcelData.Flow();
        flow.setFlowDate(item.getFDate());
        flow.setAccountName(item.getAName());
        flow.setTypeName(item.getTName());
        flow.setNote(item.getNote());
        flow.setActionName(item.getHName());
        flow.setMoney(item.getMoney());
        excelBean.getFlow().add(flow);
    });

    // 4. 设置汇总数据
    excelBean.setTotalIn(flowListDto.getTotalIn());
    excelBean.setTotalOut(flowListDto.getTotalOut());
    excelBean.setDate(screenFlowRequestDto.getStartDate() + " 至 " +
                      screenFlowRequestDto.getEndDate());
    excelBean.setName(excelName);

    // 5. 生成文件名
    SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd_HHmmss");
    String dateStr = sdf.format(new Date());
    excelName = excelName + "_" + dateStr + ".xls";

    // 6. 生成 Excel
    String excelPath = doMakeExcel(excelBean, excelName);

    // 7. 上传
    return uploadExcel(excelPath, excelName + ".xls", excelBean.getName());
}
```

**2. 筛选逻辑 (ScreenService.java:51-151)**

筛选支持多种条件组合：
- 操作类型筛选 (`actions`)
- 分类筛选 (`types`) - 支持父子分类
- 账户筛选 (`accountId`)
- 日期范围 (`startDate`, `endDate`)
- 收藏筛选 (`collect`)
- 备注关键词 (`note`)

```java
// 筛选逻辑示例
if (!getBean.useTypeScreen() && !getBean.useActionScreen()) {
    // 不筛选类型和操作 - 全部通过
    currentDataCanUse = true;
} else if (getBean.useTypeScreen() && !getBean.useActionScreen()) {
    // 只筛选类型 - 检查类型ID或父类型ID
    currentDataCanUse = getBean.getTypes().contains(typeId) ||
                        getBean.getTypes().contains(parentTypeId);
} else if (!getBean.useTypeScreen() && getBean.useActionScreen()) {
    // 只筛选操作
    currentDataCanUse = getBean.getActions().contains(actionId);
} else {
    // 同时筛选类型和操作
    currentDataCanUse = (getBean.getTypes().contains(typeId) ||
                         getBean.getTypes().contains(parentTypeId)) &&
                        getBean.getActions().contains(actionId);
}
```

---

## 财务分析 Excel 流程

### 接口定义

```
GET /analysis/exportExcel?start={start}&end={end}

查询参数：
- start: 开始月份 (yyyy-MM)
- end: 结束月份 (可选)

响应：
{
    "code": 0,
    "msg": "Success",
    "data": {
        "currentCircle": "当前周期: 2024-01",
        "yoyCircle": "同比周期: 2023-01",
        "momCircle": "环比周期: 2023-12",
        "analyzeList": [...]
    }
}
```

### 流程图

```
┌──────────────────────────────────────────────────────────────────┐
│                   AnalysisController                              │
│  GET /analysis/exportExcel?start=xxx&end=xxx                     │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                   AnalysisService                                 │
│  doMakeAnalysisExcel(startMonth, endMonth)                       │
│                                                                   │
│  1. 计算同比周期 (去年同期)                                        │
│  2. 计算环比周期 (上月，仅单月时)                                   │
│  3. 查询当前周期数据                                              │
│  4. 查询同比周期数据                                              │
│  5. 查询环比周期数据                                              │
│  6. 合并计算增长率                                                │
│  7. 调用 writeExcel() 生成文件                                    │
└─────────────────────────────┬────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ 查询当前周期数据  │ │ 查询同比周期数据  │ │ 查询环比周期数据  │
│                  │ │                  │ │                  │
│ flowDao          │ │ flowDao          │ │ flowDao          │
│ .getFlowsType    │ │ .getFlowsType    │ │ .getFlowsType    │
│ ByStartMonth     │ │ ByStartMonth     │ │ ByStartMonth     │
│ AndEndMonth()    │ │ AndEndMonth()    │ │ AndEndMonth()    │
└──────────────────┘ └──────────────────┘ └──────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │      makeCombineExcel()       │
              │                               │
              │ 1. 合并三个周期的数据          │
              │ 2. 按分类层级排序             │
              │ 3. 计算同比增长率:            │
              │    yoyIncrease = cur - yoy    │
              │    yoyGrowthRate = %          │
              │ 4. 计算环比增长率:            │
              │    momIncrease = cur - mom    │
              │    momGrowthRate = %          │
              └───────────────┬───────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │       writeMonthExcel()       │
              │                               │
              │ 1. 生成文件名                 │
              │ 2. EasyExcel 填充模板         │
              │ 3. 上传到 WebHook            │
              └───────────────────────────────┘
```

### 同比环比计算逻辑

**同比 (Year-over-Year, YoY):**
- 当前月份 `2024-01` 对比 去年同期 `2023-01`
- 增长额 = 当前金额 - 去年金额
- 增长率 = (增长额 / 去年金额) × 100%

**环比 (Month-over-Month, MoM):**
- 仅在查询单月时计算
- 当前月份 `2024-01` 对比 上月 `2023-12`
- 增长额 = 当前金额 - 上月金额
- 增长率 = (增长额 / 上月金额) × 100%

### 代码流程详解

**增长率计算 (AnalysisExcelData.java:30-65)**

```java
public void caculateComparison() {
    calculateYoyComparison();
    calculateMomComparison();
}

public void calculateYoyComparison() {
    if (money == null || lastYearMoney == null) {
        yoyIncrease = null;
        yoyGrowthRate = null;
    } else {
        // 同比增长额
        yoyIncrease = money.subtract(lastYearMoney);

        if (money.compareTo(BigDecimal.ZERO) == 0 ||
            lastYearMoney.compareTo(BigDecimal.ZERO) == 0) {
            yoyGrowthRate = "";
        } else {
            // 同比增长率
            BigDecimal rate = yoyIncrease
                .divide(lastYearMoney, 4, BigDecimal.ROUND_HALF_UP)
                .multiply(BigDecimal.valueOf(100))
                .setScale(2, BigDecimal.ROUND_HALF_UP);
            yoyGrowthRate = rate.toString() + "%";
        }
    }
}
```

---

## WebHook 通知流程

### 流程概述

Excel 生成完成后，通过 WebHook 将文件发送到外部服务（用于邮件通知等）。

### 流程图

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Excel Service  │────>│ FileMakeWebHook │────>│ WebHook 服务     │
│                 │     │                 │     │ (FastAPI)       │
│ uploadExcel()   │     │ sendFile()      │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │                         │
                              │   POST /webhook         │
                              │   multipart/form-data   │
                              │   - file: 文件          │
                              │   - file_type: 类型     │
                              │   - file_name: 文件名   │
                              │ ───────────────────────>│
                              │                         │
                              │   {"status": "ok",      │
                              │    "result": "..."}     │
                              │ <───────────────────────│
```

### FileMakeWebHook 实现

**位置：** `utils/FileMakeWebHook.java`

```java
@Component
public class FileMakeWebHook {

    @Value("${webhook_url}")
    private String WEBHOOK_URL;

    public String sendFile(File file, String fileType, String fileName) {
        OkHttpClient client = new OkHttpClient();

        // 构建 multipart 请求体
        RequestBody fileBody = RequestBody.create(file,
            MediaType.parse("application/octet-stream"));

        MultipartBody requestBody = new MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart("file", fileName, fileBody)
                .addFormDataPart("file_type", fileType)
                .addFormDataPart("file_name", fileName)
                .build();

        Request request = new Request.Builder()
                .url(WEBHOOK_URL)
                .post(requestBody)
                .build();

        try {
            Response response = client.newCall(request).execute();
            if (response.isSuccessful()) {
                WebHookDto webHookDto = GsonUtils.gson.fromJson(
                    response.body().string(), WebHookDto.class);

                if (!"ok".equals(webHookDto.getStatus())) {
                    return "\n调用webhook失败：\n" + webHookDto.getMessage() + "|1";
                } else {
                    return "\n调用webhook成功\n" + webHookDto.getResult() + "|0";
                }
            } else {
                return "\n调用webhook失败：\n" + response.message() + "|1";
            }
        } catch (IOException e) {
            return "\n上传文件失败：\n" + e.getMessage() + "|1";
        }
    }
}
```

### 文件类型标识

| file_type | 说明 |
|-----------|------|
| `month_excel` | 月度账单 |
| `screen_excel` | 筛选账单 |
| `analysis_excel` | 财务分析 |
| `sql_backup` | SQL 备份 |

---

## 数据模型定义

### MonthExcelData（月度账单）

**位置：** `data/MonthExcelData.java`

```java
@Data
public class MonthExcelData {
    private String currentMonth;     // 当前月份 (如 "2024年01月")
    private String monthTotalIn;     // 月总收入 (如 "￥8000.00")
    private String monthTotalOut;    // 月总支出
    private String monthTotalEarn;   // 月结余
    private String allAsset;         // 总资产
    private List<Flow> flow;         // 流水列表
    private List<Account> excelAccounts;  // 账户列表

    @Data
    public static class Flow {
        private String flowDate;     // 日期 (yyyy-MM-dd)
        private String actionName;   // 操作名称 (收入/支出/转账)
        private String typeName;     // 分类名称 (含父分类)
        private String accountName;  // 账户名称
        private String money;        // 金额 (如 "￥100.00")
        private String note;         // 备注
    }

    @Data
    public static class Account {
        private String accountName;  // 账户名称
        private String accountMoney; // 账户余额
    }
}
```

### ScreenExcelData（筛选账单）

**位置：** `data/ScreenExcelData.java`

```java
public class ScreenExcelData {
    private String date;           // 日期范围 (如 "2024-01-01 至 2024-12-31")
    private String name;           // Excel 名称
    private String totalIn;        // 总收入
    private String totalOut;       // 总支出
    private String totalEarn;      // 总结余
    private List<MonthExcelData.Flow> flow;  // 复用月度流水格式
}
```

### AnalysisExcelData（财务分析）

**位置：** `data/AnalysisExcelData.java`

```java
@Data
public class AnalysisExcelData {
    private String currentCircle;   // 当前周期
    private String yoyCircle;       // 同比周期
    private String momCircle;       // 环比周期
    private List<Analyze> analyzeList;  // 分析列表

    @Data
    public static class Analyze {
        private String name;            // 分类名称
        private boolean isRoot;         // 是否顶级分类
        private int id;                 // 分类ID
        private int parent;             // 父分类ID
        private BigDecimal money;       // 当前金额
        private BigDecimal lastYearMoney;   // 去年同期金额
        private BigDecimal lastMonthMoney;  // 上月金额
        private BigDecimal yoyIncrease;     // 同比增长额
        private String yoyGrowthRate;       // 同比增长率 (如 "15.00%")
        private BigDecimal momIncrease;     // 环比增长额
        private String momGrowthRate;       // 环比增长率
    }
}
```

---

## 错误处理

### 返回值格式

所有 Excel 生成方法返回字符串，格式为：
```
{日志信息}|{状态码}
```

- `|0` - 成功
- `|1` - 失败

### 常见错误

| 错误信息 | 原因 | 处理方式 |
|----------|------|----------|
| `Excel生成失败\|1` | 日期解析失败 | 检查日期格式 |
| `筛选条件无数据\|1` | 筛选结果为空 | 调整筛选条件 |
| `文件上传失败\|1` | 文件不存在 | 检查输出目录权限 |
| `调用webhook失败\|1` | WebHook 服务异常 | 检查 WebHook 服务状态 |

### 日志记录

所有服务类使用 `@Slf4j` 注解，关键步骤有日志输出：

```java
@Slf4j
@Service
public class ExcelService {
    public String makeMonthExcel(String dateStr) {
        log.info(new Gson().toJson(monthExcelData));
        // ...
    }
}
```

---

## 相关文件路径

| 类型 | 路径 |
|------|------|
| 控制器 | `controller/FlowController.java` |
| 控制器 | `controller/ScreenController.java` |
| 控制器 | `controller/AnalysisController.java` |
| 服务 | `service/ExcelService.java` |
| 服务 | `service/ScreenService.java` |
| 服务 | `service/AnalysisService.java` |
| 数据模型 | `data/MonthExcelData.java` |
| 数据模型 | `data/ScreenExcelData.java` |
| 数据模型 | `data/AnalysisExcelData.java` |
| WebHook | `utils/FileMakeWebHook.java` |
| 模板 | `excel_template/*.xls` |
