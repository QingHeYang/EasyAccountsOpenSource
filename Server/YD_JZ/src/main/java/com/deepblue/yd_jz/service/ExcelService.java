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
    FileMakeWebHook fileMakeWebHook;

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
            return fileMakeWebHook.sendFile(new File(excelPath), "month_excel", excelFileName);
        }else {
            return "\n文件上传失败\n"+excelPath+excelFileName+"不存在|1";
        }
    }

    private void sendEmail(String fileUrl, String title) {

    }

    public static class ExcelWriteHandler implements CellWriteHandler {
        private final List<MonthExcelData.Flow> flowList;
        private final int dataStartRow;  // 数据开始的行号
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
    }


}
