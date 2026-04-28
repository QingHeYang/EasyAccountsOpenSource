package com.deepblue.yd_jz.service;

import com.alibaba.excel.EasyExcel;
import com.alibaba.excel.ExcelWriter;
import com.alibaba.excel.write.handler.CellWriteHandler;
import com.alibaba.excel.write.handler.context.CellWriteHandlerContext;
import com.alibaba.excel.write.metadata.WriteSheet;
import com.alibaba.excel.write.metadata.fill.FillWrapper;
import com.alibaba.excel.write.metadata.style.WriteCellStyle;
import com.alibaba.excel.write.metadata.style.WriteFont;
import com.deepblue.yd_jz.entity.Account;
import com.deepblue.yd_jz.dao.mybatis.FlowDao;
import com.deepblue.yd_jz.data.MonthExcelData;
import com.deepblue.yd_jz.utils.*;
import com.google.gson.Gson;
import lombok.extern.slf4j.Slf4j;
import org.apache.poi.ss.usermodel.BorderStyle;
import org.apache.poi.ss.usermodel.Cell;
import org.apache.poi.ss.usermodel.IndexedColors;
import org.apache.poi.xssf.usermodel.XSSFCellStyle;
import org.apache.poi.xssf.usermodel.XSSFColor;
import org.apache.poi.xssf.usermodel.XSSFFont;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import java.awt.Color;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.File;
import java.math.BigDecimal;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.*;

@Slf4j
@Service
public class ExcelService {
    @Autowired
    FlowDao flowDao;

    @Autowired
    ActionService actionService;

    @Autowired
    AccountService accountService;

    @Autowired
    MailService mailService;

    @Autowired
    DateUtils dateUtils;

    @Value("${baseAutoExcel}")
    public String baseExcelPath;

    @Value("${excelAutoFolder}")
    public String excelFolder;


    // ss mm hh dd MM yy
    public String makeMonthExcel(String dateStr) {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM"); // 格式化字符串需要与你的输入日期格式匹配
        try {
            Date date = sdf.parse(dateStr); // 尝试解析传入的日期字符串
            MonthExcelData monthExcelData = getExcelForMonth(date); // 获取该日期的Excel报表数据
            log.info(new Gson().toJson(monthExcelData));
            String result = writeMonthExcel(dateStr, monthExcelData);
            return "文件生成成功"+result;
        } catch (ParseException e) {
            // 处理ParseException异常，可以记录日志或返回错误信息
            e.printStackTrace(); // 打印堆栈信息（在实际项目中可能需要更合适的错误处理方式）
            return "Excel生成失败|1"; // 返回null或者抛出一个自定义异常
        }
    }

    private MonthExcelData getExcelForMonth(Date date) {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM");
        Calendar calendar = Calendar.getInstance();
        calendar.setTime(date); // 设置为当前时间
        int month = calendar.get(Calendar.MONTH);
        calendar.set(Calendar.MONTH, month);
        date = calendar.getTime();
        String curDate = sdf.format(date) + "%";
        List<Map<String, Object>> flows = flowDao.getFlowByMain(3, 0, curDate);
        List<MonthExcelData.Flow> flowList = new ArrayList<>();
        BigDecimal moneyIn = new BigDecimal("0");
        BigDecimal moneyOut = new BigDecimal("0");

        MonthExcelData monthExcelData = new MonthExcelData();

        for (Map<String, Object> map : flows) {
            MonthExcelData.Flow flow = new MonthExcelData.Flow();
            SimpleDateFormat sdfDate = new SimpleDateFormat("yyyy-MM-dd");
            Date fDate = (Date) map.get("f_date");
            flow.setFlowDate(sdfDate.format(fDate));

            int handle = (int) map.get("handle");
            String money = (String) map.get("money");
            // 支出显示为负数，去掉￥符号
            if (handle == 1) {
                flow.setMoney("-" + money);
            } else {
                flow.setMoney(money);
            }

            if (map.get("p_t_name") != null) {
                flow.setTypeName(map.get("p_t_name") + "/" + map.get("t_name"));
            } else {
                flow.setTypeName((String) map.get("t_name"));
            }
            flow.setNote((String) map.get("note"));
            flow.setActionName((String) map.get("h_name"));
            flow.setHandle(handle);
            flowList.add(flow);
            flow.setAccountName((String) map.get("a_name"));
            if (handle == 1) {
                moneyOut = moneyOut.add(new BigDecimal(money));
            } else if (handle == 0) {
                moneyIn = moneyIn.add(new BigDecimal(money));
            } else {
                flow.setAccountName(map.get("a_name") + "->" + map.get("t_a_name"));
            }
        }
        monthExcelData.setMonthTotalIn("￥" + moneyIn.toString());
        monthExcelData.setMonthTotalOut("￥" + moneyOut.toString());
        monthExcelData.setMonthTotalEarn("￥" + (moneyIn.subtract(moneyOut)).toString());
        SimpleDateFormat sdfExcel = new SimpleDateFormat("yyyy年MM月");
        String excelDate = sdfExcel.format(date);
        monthExcelData.setCurrentMonth(excelDate);
        monthExcelData.setFlow(flowList);

        String accountsDate = dateUtils.buildFullDate(sdf.format(date), false);
        log.info("accountsDate: " + accountsDate);
        List<Account> accounts = accountService.getAccountByDate(accountsDate);
        List<MonthExcelData.Account> excelAccounts = new ArrayList<>();
        BigDecimal totalAsset = new BigDecimal("0");
        for (Account a : accounts) {
            MonthExcelData.Account excelA = new MonthExcelData.Account();
            excelA.setAccountMoney(a.getMoney());
            excelA.setAccountName(a.getAName());
            totalAsset = totalAsset.add(new BigDecimal(a.getMoney()));
            excelAccounts.add(excelA);
        }
        monthExcelData.setExcelAccounts(excelAccounts);
        monthExcelData.setAllAsset("￥" + totalAsset.toString());
        return monthExcelData;

    }



    private String writeMonthExcel(String excelDate, MonthExcelData monthExcelData) {
        Date date = new Date();
        String excelFileName = excelDate + "月账单_" + date.getTime() + ".xlsx";
        String excelPath = excelFolder + excelFileName;
        ExcelWriter excelWriter = EasyExcel.write().file(excelPath)
                .withTemplate(baseExcelPath)
                .inMemory(true)  // EasyExcel 4.x 大数据量模板填充需要
                .registerWriteHandler(new ExcelWriteHandler(monthExcelData.getFlow(), 3))
                .build();
        WriteSheet writeSheet = EasyExcel.writerSheet().build();
        excelWriter.fill(monthExcelData, writeSheet);
        excelWriter.fill(new FillWrapper("flow", monthExcelData.getFlow()), writeSheet);
        excelWriter.fill(new FillWrapper("account", monthExcelData.getExcelAccounts()), writeSheet);
        //excelWriter.fill(new FillWrapper("analyze",excelBean.getAnalyzeList()), writeSheet);
        //  excelWriter.write(flowList,writeSheet);
        excelWriter.finish();
        return uploadExcel(excelPath, excelFileName, excelDate);
    }

    private String uploadExcel(String excelPath, String excelFileName, String title) {
        if (FileUtils.isExist(excelPath)) {
            mailService.sendMonthExcel(new File(excelPath), title);
            return "\n月度 Excel 已生成并发送邮件\n" + excelFileName + "|0";
        }else {
            return "\n文件上传失败\n"+excelPath+excelFileName+"不存在|1";
        }
    }

    // ════════════════════════ v2.7.0 (auto-excel) 给自动模块用 ════════════════════════

    /**
     * 统计指定月的流水数量。
     * 给 AutoExcelExecuteService 用来判断"无流水"分支。
     * @param yearMonth yyyy-MM 格式，例如 "2026-04"
     */
    public int countMonthFlows(String yearMonth) {
        if (yearMonth == null || !yearMonth.matches("^\\d{4}-\\d{2}$")) {
            return 0;
        }
        List<Map<String, Object>> flows = flowDao.getFlowByMain(3, 0, yearMonth + "%");
        return flows == null ? 0 : flows.size();
    }

    /**
     * 仅生成月度 Excel 文件、不发邮件。
     * 给 AutoExcelExecuteService 用来"先拿到文件再决定怎么发"。
     * @param yearMonth yyyy-MM 格式
     * @return 生成的 Excel 文件；解析失败或写入失败返回 null
     */
    public File makeMonthExcelFile(String yearMonth) {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM");
        try {
            Date date = sdf.parse(yearMonth);
            MonthExcelData monthExcelData = getExcelForMonth(date);
            String excelFileName = yearMonth + "月账单_" + new Date().getTime() + ".xlsx";
            String excelPath = excelFolder + excelFileName;

            ExcelWriter excelWriter = EasyExcel.write().file(excelPath)
                    .withTemplate(baseExcelPath)
                    .inMemory(true)
                    .registerWriteHandler(new ExcelWriteHandler(monthExcelData.getFlow(), 3))
                    .build();
            WriteSheet writeSheet = EasyExcel.writerSheet().build();
            excelWriter.fill(monthExcelData, writeSheet);
            excelWriter.fill(new FillWrapper("flow", monthExcelData.getFlow()), writeSheet);
            excelWriter.fill(new FillWrapper("account", monthExcelData.getExcelAccounts()), writeSheet);
            excelWriter.finish();

            File f = new File(excelPath);
            if (!f.exists()) {
                log.error("makeMonthExcelFile: Excel 文件未生成 {}", excelPath);
                return null;
            }
            return f;
        } catch (ParseException e) {
            log.error("makeMonthExcelFile: 解析 yearMonth 失败 [{}]: {}", yearMonth, e.getMessage());
            return null;
        } catch (Exception e) {
            log.error("makeMonthExcelFile: 写入 Excel 失败 [{}]: {}", yearMonth, e.getMessage());
            return null;
        }
    }

    public static class ExcelWriteHandler implements CellWriteHandler {
        private final List<MonthExcelData.Flow> flowList;
        private final int dataStartRow;  // 数据开始的行号
        // 缓存样式，避免创建过多
        private XSSFCellStyle incomeStyle;   // 收入样式
        private XSSFCellStyle expenseStyle;  // 支出样式
        private XSSFCellStyle transferStyle; // 转账样式
        // v2.5.1: I 列汇总区域背景色样式缓存
        private XSSFCellStyle summaryIncomeStyle;   // 收入汇总 - 绿色背景
        private XSSFCellStyle summaryExpenseStyle;  // 支出汇总 - 红色背景
        private XSSFCellStyle summaryBalanceStyle;  // 结余汇总 - 蓝色背景
        private XSSFCellStyle summaryTotalStyle;    // 总资产汇总 - 灰色背景

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

                // v2.5.1: I 列(columnIndex=8) 汇总区域设置背景颜色和白色字体
                if (context.getRowIndex() != null && context.getColumnIndex() != null
                        && context.getColumnIndex() == 8) {
                    Integer rowIndex = context.getRowIndex();
                    Cell cell = context.getCell();
                    if (cell != null && cell.getSheet().getWorkbook() instanceof XSSFWorkbook) {
                        XSSFWorkbook workbook = (XSSFWorkbook) cell.getSheet().getWorkbook();
                        XSSFCellStyle summaryStyle = null;
                        // 收入行 (5-6, rowIndex 4-5)
                        if (rowIndex == 4 || rowIndex == 5) {
                            summaryStyle = getOrCreateSummaryStyle(workbook, "income", cell.getCellStyle());
                        }
                        // 支出行 (7-8, rowIndex 6-7)
                        else if (rowIndex == 6 || rowIndex == 7) {
                            summaryStyle = getOrCreateSummaryStyle(workbook, "expense", cell.getCellStyle());
                        }
                        // 结余行 (9-10, rowIndex 8-9)
                        else if (rowIndex == 8 || rowIndex == 9) {
                            summaryStyle = getOrCreateSummaryStyle(workbook, "balance", cell.getCellStyle());
                        }
                        // 总资产行 (11-12, rowIndex 10-11)
                        else if (rowIndex == 10 || rowIndex == 11) {
                            summaryStyle = getOrCreateSummaryStyle(workbook, "total", cell.getCellStyle());
                        }
                        if (summaryStyle != null) {
                            context.getFirstCellData().setOriginCellStyle(summaryStyle);
                        }
                    }
                }
            }
        }

        private XSSFCellStyle getOrCreateColorStyle(XSSFWorkbook workbook, int handle, org.apache.poi.ss.usermodel.CellStyle baseStyle) {
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

        // v2.5.1: 创建汇总区域样式（背景色 + 白色字体）
        private XSSFCellStyle getOrCreateSummaryStyle(XSSFWorkbook workbook, String type,
                org.apache.poi.ss.usermodel.CellStyle baseStyle) {
            // 检查缓存
            switch (type) {
                case "income": if (summaryIncomeStyle != null) return summaryIncomeStyle; break;
                case "expense": if (summaryExpenseStyle != null) return summaryExpenseStyle; break;
                case "balance": if (summaryBalanceStyle != null) return summaryBalanceStyle; break;
                case "total": if (summaryTotalStyle != null) return summaryTotalStyle; break;
            }

            // v2.5.1: 使用淡色背景 + 黑字，更柔和
            Color bgColor;
            switch (type) {
                case "income":   // 收入 - 淡绿色 #E6F7E9
                    bgColor = new Color(0xE6, 0xF7, 0xE9);
                    break;
                case "expense":  // 支出 - 淡红色 #FFF0F0
                    bgColor = new Color(0xFF, 0xF0, 0xF0);
                    break;
                case "balance":  // 结余 - 淡蓝色 #E6F4FF
                    bgColor = new Color(0xE6, 0xF4, 0xFF);
                    break;
                case "total":    // 总资产 - 淡灰色 #F5F5F5
                    bgColor = new Color(0xF5, 0xF5, 0xF5);
                    break;
                default:
                    return null;
            }

            XSSFCellStyle style = workbook.createCellStyle();
            style.cloneStyleFrom(baseStyle);

            // 设置边框
            style.setBorderBottom(BorderStyle.THIN);
            style.setBorderLeft(BorderStyle.THIN);
            style.setBorderRight(BorderStyle.THIN);
            style.setBorderTop(BorderStyle.THIN);

            // 设置背景颜色
            XSSFColor xssfBgColor = new XSSFColor(bgColor, workbook.getStylesSource().getIndexedColors());
            style.setFillForegroundColor(xssfBgColor);
            style.setFillPattern(org.apache.poi.ss.usermodel.FillPatternType.SOLID_FOREGROUND);

            // 设置黑色字体
            XSSFFont font = workbook.createFont();
            font.setColor(new XSSFColor(Color.BLACK, workbook.getStylesSource().getIndexedColors()));
            font.setBold(true);
            style.setFont(font);

            // 缓存
            switch (type) {
                case "income": summaryIncomeStyle = style; break;
                case "expense": summaryExpenseStyle = style; break;
                case "balance": summaryBalanceStyle = style; break;
                case "total": summaryTotalStyle = style; break;
            }
            return style;
        }
    }


}
