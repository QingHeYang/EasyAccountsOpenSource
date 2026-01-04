# Excel 样式增强开发日志

本文档记录 EasyExcel 升级及 Excel 导出样式增强的开发过程。

---

## 概览

| 项目 | 内容 |
|------|------|
| **分支** | 2.6.0-server-upgrade |
| **开发时间** | 2026-01-04 |
| **状态** | 部分完成 |

---

## 一、已完成功能

### 1.1 EasyExcel 版本升级

| 项目 | 旧版本 | 新版本 |
|------|--------|--------|
| EasyExcel | 2.2.4 | 4.0.3 |

**升级原因：**
- EasyExcel 2.2.4 使用 cglib 动态代理，在 Java 17 模块系统下触发 `InaccessibleObjectException`
- 必须升级才能兼容 Spring Boot 3.x + Java 17

**API 变更：**

| 变更项 | 旧版本 (2.2.4) | 新版本 (4.0.3) |
|--------|----------------|----------------|
| CellWriteHandler | 多个回调方法 | 单一 `afterCellDispose(CellWriteHandlerContext context)` |
| CellData | `CellData` | `WriteCellData` |
| 样式设置 | 直接操作 POI CellStyle | 使用 `WriteCellStyle.getOrCreateStyle()` |
| 模板填充 | 自动处理 | 大数据需添加 `.inMemory(true)` |

### 1.2 Excel 模板格式迁移

| 模板文件 | 旧格式 | 新格式 |
|----------|--------|--------|
| auto_excel | .xls | .xlsx |
| screen_excel | .xls | .xlsx |
| analysis_excel | 已删除 | - |

**配置文件更新：**
```properties
# application-local.properties / application-server.properties
baseAutoExcel=xxx/auto_excel.xlsx
baseScreenExcel=xxx/screen_excel.xlsx
```

### 1.3 金额格式优化

**修改内容：**
- 去掉金额前的 `￥` 符号
- 支出 (handle=1) 金额显示为负数（如 `-100.00`）

**修改文件：**
- `ExcelService.java` - `getExcelForMonth()` 方法
- `ScreenService.java` - `makeScreenExcel()` 方法

**代码示例：**
```java
int handle = (int) map.get("handle");
String money = (String) map.get("money");
// 支出显示为负数，去掉￥符号
if (handle == 1) {
    flow.setMoney("-" + money);
} else {
    flow.setMoney(money);
}
```

### 1.4 E 列自定义 RGB 字体颜色

**功能描述：**
- 只对 E 列（金额列，columnIndex=4）设置字体颜色
- 根据 `handle` 字段动态设置颜色

**颜色定义（来自 UI 指南 `ui-guide.md`）：**

| handle | 类型 | 颜色 | RGB |
|--------|------|------|-----|
| 0 | 收入 | 绿色 | #52C41A |
| 1 | 支出 | 红色 | #F5222D |
| 2 | 转账 | 蓝色 | #1890FF |

**关键实现：**

EasyExcel 的 `WriteFont` 不支持自定义 RGB 颜色，只能使用 `IndexedColors` 预设颜色。要实现自定义 RGB 颜色，需要：

1. 直接操作 POI 的 `XSSFWorkbook`、`XSSFCellStyle`、`XSSFFont`
2. 使用 `java.awt.Color` 创建 `XSSFColor`
3. 使用 `context.getFirstCellData().setOriginCellStyle()` 设置样式（而不是直接设置 Cell）
4. 缓存样式避免创建过多（Excel 最多支持约 64000 个样式）

**完整代码实现：**

```java
// ExcelService.java - ExcelWriteHandler 类

public static class ExcelWriteHandler implements CellWriteHandler {
    private final List<MonthExcelData.Flow> flowList;
    private final int dataStartRow;  // 数据开始的行号（0-indexed，第4行=3）
    // 缓存样式，避免创建过多
    private XSSFCellStyle incomeStyle;   // 收入样式
    private XSSFCellStyle expenseStyle;  // 支出样式
    private XSSFCellStyle transferStyle; // 转账样式

    public ExcelWriteHandler() {
        this.flowList = null;
        this.dataStartRow = 0;
    }

    public ExcelWriteHandler(List<MonthExcelData.Flow> flowList, int dataStartRow) {
        this.flowList = flowList;
        this.dataStartRow = dataStartRow;
    }

    @Override
    public void afterCellDispose(CellWriteHandlerContext context) {
        if (context.getFirstCellData() != null) {
            WriteCellStyle writeCellStyle = context.getFirstCellData().getOrCreateStyle();

            // 设置边框
            writeCellStyle.setBorderBottom(BorderStyle.THIN);
            writeCellStyle.setBorderLeft(BorderStyle.THIN);
            writeCellStyle.setBorderRight(BorderStyle.THIN);
            writeCellStyle.setBorderTop(BorderStyle.THIN);
            writeCellStyle.setBottomBorderColor((short) 0);
            writeCellStyle.setTopBorderColor((short) 0);
            writeCellStyle.setLeftBorderColor((short) 0);
            writeCellStyle.setRightBorderColor((short) 0);

            // 只对 E 列(金额列, columnIndex=4) 根据 handle 设置字体颜色
            if (flowList != null && context.getRowIndex() != null && context.getColumnIndex() != null
                    && context.getColumnIndex() == 4) {
                int dataIndex = context.getRowIndex() - dataStartRow;
                if (dataIndex >= 0 && dataIndex < flowList.size()) {
                    Integer handle = flowList.get(dataIndex).getHandle();
                    if (handle != null) {
                        Cell cell = context.getCell();
                        if (cell != null && cell.getSheet().getWorkbook() instanceof XSSFWorkbook) {
                            XSSFWorkbook workbook = (XSSFWorkbook) cell.getSheet().getWorkbook();
                            XSSFCellStyle colorStyle = getOrCreateColorStyle(workbook, handle, cell.getCellStyle());
                            if (colorStyle != null) {
                                // 用 setOriginCellStyle 设置样式
                                context.getFirstCellData().setOriginCellStyle(colorStyle);
                            }
                        }
                    }
                }
            }
        }
    }

    private XSSFCellStyle getOrCreateColorStyle(XSSFWorkbook workbook, int handle,
            org.apache.poi.ss.usermodel.CellStyle baseStyle) {
        XSSFCellStyle targetStyle;
        Color awtColor;

        switch (handle) {
            case 0:  // 收入 - 绿色 #52C41A
                if (incomeStyle != null) return incomeStyle;
                awtColor = new Color(0x52, 0xC4, 0x1A);
                break;
            case 1:  // 支出 - 红色 #F5222D
                if (expenseStyle != null) return expenseStyle;
                awtColor = new Color(0xF5, 0x22, 0x2D);
                break;
            case 2:  // 转账 - 蓝色 #1890FF
                if (transferStyle != null) return transferStyle;
                awtColor = new Color(0x18, 0x90, 0xFF);
                break;
            default:
                return null;
        }

        targetStyle = workbook.createCellStyle();
        targetStyle.cloneStyleFrom(baseStyle);
        // 设置边框
        targetStyle.setBorderBottom(BorderStyle.THIN);
        targetStyle.setBorderLeft(BorderStyle.THIN);
        targetStyle.setBorderRight(BorderStyle.THIN);
        targetStyle.setBorderTop(BorderStyle.THIN);

        XSSFFont font = workbook.createFont();
        XSSFColor xssfColor = new XSSFColor(awtColor, workbook.getStylesSource().getIndexedColors());
        font.setColor(xssfColor);
        targetStyle.setFont(font);

        // 缓存
        switch (handle) {
            case 0: incomeStyle = targetStyle; break;
            case 1: expenseStyle = targetStyle; break;
            case 2: transferStyle = targetStyle; break;
        }
        return targetStyle;
    }
}
```

**使用方式：**
```java
ExcelWriter excelWriter = EasyExcel.write().file(excelPath)
        .withTemplate(baseExcelPath)
        .inMemory(true)  // EasyExcel 4.x 大数据量模板填充需要
        .registerWriteHandler(new ExcelWriteHandler(monthExcelData.getFlow(), 3))  // 3 = 第4行开始
        .build();
```

**需要的 import：**
```java
import org.apache.poi.ss.usermodel.BorderStyle;
import org.apache.poi.ss.usermodel.Cell;
import org.apache.poi.ss.usermodel.IndexedColors;
import org.apache.poi.xssf.usermodel.XSSFCellStyle;
import org.apache.poi.xssf.usermodel.XSSFColor;
import org.apache.poi.xssf.usermodel.XSSFFont;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import java.awt.Color;
```

### 1.5 大数据量模板填充修复

**问题：** 超过 80+ 条数据时，第 5-87 行数据丢失

**原因：** EasyExcel 4.x 的模板填充模式在处理大数据时需要 `.inMemory(true)`

**解决方案：**
```java
ExcelWriter excelWriter = EasyExcel.write().file(excelPath)
        .withTemplate(baseExcelPath)
        .inMemory(true)  // 关键！
        .registerWriteHandler(new ExcelWriteHandler())
        .build();
```

---

## 二、未完成功能

### 2.1 月度账单汇总区域样式

**需求描述：**
月度账单（auto_excel.xlsx）的汇总区域需要设置背景颜色和白色文字。

**目标位置：**
- 列：I 列 (columnIndex = 8)
- 合并单元格行：

| 行号 (1-based) | rowIndex (0-based) | 内容 | 合并范围 | 背景颜色 | 字体颜色 |
|----------------|---------------------|------|----------|----------|----------|
| 5-6 | 4-5 | 收入 | I5:I6 | #52C41A (绿) | 白色 |
| 7-8 | 6-7 | 支出 | I7:I8 | #F5222D (红) | 白色 |
| 9-10 | 8-9 | 结余 | I9:I10 | ？待确认 | 白色 |
| 11-12 | 10-11 | 总资产 | I11:I12 | ？待确认 | 白色 |

**待确认：**
- 结余的背景颜色（建议：转账蓝 #1890FF 或 备注黄 #FAAD14）
- 总资产的背景颜色（建议：主色调蓝 #1890FF 或 灰色）

**实现思路：**

在 `ExcelWriteHandler.afterCellDispose()` 中增加对汇总区域的处理：

```java
// 伪代码 - 处理汇总区域 I 列
if (context.getColumnIndex() != null && context.getColumnIndex() == 8) {  // I 列
    Integer rowIndex = context.getRowIndex();
    if (rowIndex != null) {
        XSSFCellStyle summaryStyle = null;

        // 收入行 (5-6, rowIndex 4-5)
        if (rowIndex == 4 || rowIndex == 5) {
            summaryStyle = getOrCreateSummaryStyle(workbook, "income", baseStyle);
        }
        // 支出行 (7-8, rowIndex 6-7)
        else if (rowIndex == 6 || rowIndex == 7) {
            summaryStyle = getOrCreateSummaryStyle(workbook, "expense", baseStyle);
        }
        // 结余行 (9-10, rowIndex 8-9)
        else if (rowIndex == 8 || rowIndex == 9) {
            summaryStyle = getOrCreateSummaryStyle(workbook, "balance", baseStyle);
        }
        // 总资产行 (11-12, rowIndex 10-11)
        else if (rowIndex == 10 || rowIndex == 11) {
            summaryStyle = getOrCreateSummaryStyle(workbook, "total", baseStyle);
        }

        if (summaryStyle != null) {
            context.getFirstCellData().setOriginCellStyle(summaryStyle);
        }
    }
}
```

**设置背景颜色的关键代码：**

```java
private XSSFCellStyle getOrCreateSummaryStyle(XSSFWorkbook workbook, String type,
        org.apache.poi.ss.usermodel.CellStyle baseStyle) {

    XSSFCellStyle style = workbook.createCellStyle();
    style.cloneStyleFrom(baseStyle);

    Color bgColor;
    switch (type) {
        case "income":
            bgColor = new Color(0x52, 0xC4, 0x1A);  // 绿色
            break;
        case "expense":
            bgColor = new Color(0xF5, 0x22, 0x2D);  // 红色
            break;
        case "balance":
            bgColor = new Color(0x18, 0x90, 0xFF);  // 蓝色（待确认）
            break;
        case "total":
            bgColor = new Color(0x18, 0x90, 0xFF);  // 蓝色（待确认）
            break;
        default:
            return null;
    }

    // 设置背景颜色
    XSSFColor xssfBgColor = new XSSFColor(bgColor, workbook.getStylesSource().getIndexedColors());
    style.setFillForegroundColor(xssfBgColor);
    style.setFillPattern(FillPatternType.SOLID_FOREGROUND);

    // 设置白色字体
    XSSFFont font = workbook.createFont();
    font.setColor(new XSSFColor(Color.WHITE, workbook.getStylesSource().getIndexedColors()));
    style.setFont(font);

    return style;
}
```

**需要额外 import：**
```java
import org.apache.poi.ss.usermodel.FillPatternType;
```

---

## 三、踩坑记录

### 3.1 EasyExcel 样式被覆盖问题

**问题：** 在 `afterCellDispose` 中直接设置 `cell.setCellStyle()` 后样式不生效

**原因：** EasyExcel 内部有 `FillStyleCellWriteHandler`，会在后续用 `WriteCellStyle` 覆盖自定义样式

**错误方案：**
```java
// 这样会导致边框等其他样式也丢失
context.getFirstCellData().setWriteCellStyle(null);
```

**正确方案：**
```java
// 使用 setOriginCellStyle 设置样式
context.getFirstCellData().setOriginCellStyle(colorStyle);
```

### 3.2 IndexedColors vs 自定义 RGB

**问题：** `WriteFont.setColor()` 只接受 `short` 类型的 IndexedColors 索引

**解决：** 直接操作 POI 的 XSSFFont：
```java
XSSFFont font = workbook.createFont();
XSSFColor xssfColor = new XSSFColor(new java.awt.Color(r, g, b),
    workbook.getStylesSource().getIndexedColors());
font.setColor(xssfColor);
```

### 3.3 XSSFColor 构造函数

**问题：** `new XSSFColor(byte[] rgb, null)` 可能导致颜色显示为黑色

**解决：** 使用 `java.awt.Color` 并传入正确的 IndexedColorMap：
```java
XSSFColor xssfColor = new XSSFColor(
    new java.awt.Color(0x52, 0xC4, 0x1A),
    workbook.getStylesSource().getIndexedColors()
);
```

### 3.4 样式数量限制

**问题：** Excel 最多支持约 64000 个样式，每行创建新样式会超限

**解决：** 缓存已创建的样式并复用：
```java
private XSSFCellStyle incomeStyle;
private XSSFCellStyle expenseStyle;
private XSSFCellStyle transferStyle;

// 在 getOrCreateColorStyle 中先检查缓存
if (incomeStyle != null) return incomeStyle;
```

---

## 四、相关文件

| 文件 | 说明 |
|------|------|
| `ExcelService.java` | 月度账单 Excel 生成服务 |
| `ScreenService.java` | 筛选账单 Excel 生成服务 |
| `MonthExcelData.java` | 月度账单数据模型（Flow 类含 handle 字段） |
| `auto_excel.xlsx` | 月度账单模板 |
| `screen_excel.xlsx` | 筛选账单模板 |
| `ui-guide.md` | UI 颜色定义（Web 端） |

---

## 五、参考资料

- [EasyExcel 官方文档](https://easyexcel.opensource.alibaba.com/)
- [easyexcel设置正文字体使用自定义RGB颜色 - CSDN](https://blog.csdn.net/XKEYUAN/article/details/143684414)
- [EasyExcel 拦截器设置单元格格式不生效 - 简书](https://www.jianshu.com/p/32c5a6ec2d91)
- [Apache POI XSSFColor API](https://poi.apache.org/apidocs/dev/org/apache/poi/xssf/usermodel/XSSFColor.html)

---

*文档创建时间：2026-01-04*
