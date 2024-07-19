package com.deepblue.yd_jz.service;

import com.alibaba.excel.EasyExcel;
import com.alibaba.excel.ExcelWriter;
import com.alibaba.excel.metadata.CellData;
import com.alibaba.excel.metadata.Head;
import com.alibaba.excel.write.handler.CellWriteHandler;
import com.alibaba.excel.write.metadata.WriteSheet;
import com.alibaba.excel.write.metadata.fill.FillWrapper;
import com.alibaba.excel.write.metadata.holder.WriteSheetHolder;
import com.alibaba.excel.write.metadata.holder.WriteTableHolder;
import com.deepblue.yd_jz.dao.account.Account;
import com.deepblue.yd_jz.dao.account.AccountDao;
import com.deepblue.yd_jz.dao.action.ActionDao;
import com.deepblue.yd_jz.dao.flow.FlowDao;
import com.deepblue.yd_jz.dao.flow.FlowType;
import com.deepblue.yd_jz.utils.*;
import com.google.gson.Gson;
import lombok.extern.slf4j.Slf4j;
import org.apache.poi.ss.usermodel.BorderStyle;
import org.apache.poi.ss.usermodel.Cell;
import org.apache.poi.ss.usermodel.CellStyle;
import org.apache.poi.ss.usermodel.Row;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.stereotype.Service;

import java.io.File;
import java.math.BigDecimal;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.stream.Collectors;
import java.util.stream.Stream;

@Slf4j
@Service
public class ExcelService {
    @Autowired
    FlowDao flowDao;

    @Autowired
    ActionDao actionDao;

    @Autowired
    AccountDao accountDao;

    @Autowired
    FileMakeWebHook fileMakeWebHook;

    @Value("${baseAutoExcel}")
    public String baseExcelPath;

    @Value("${excelAutoFolder}")
    public String excelFolder;

    // ss mm hh dd MM yy
    public ExcelBean makeMonthExcel(String dateStr) {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM"); // 格式化字符串需要与你的输入日期格式匹配
        try {
            Date date = sdf.parse(dateStr); // 尝试解析传入的日期字符串
            ExcelBean excelBean = getExcelForMonth(date); // 获取该日期的Excel报表数据
            log.info(new Gson().toJson(excelBean));
            writeMonthExcel(dateStr,excelBean);
            return excelBean;
        } catch (ParseException e) {
            // 处理ParseException异常，可以记录日志或返回错误信息
            e.printStackTrace(); // 打印堆栈信息（在实际项目中可能需要更合适的错误处理方式）
            return null; // 返回null或者抛出一个自定义异常
        }
    }

    private ExcelBean getExcelForMonth(Date date) {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM");
        Calendar calendar = Calendar.getInstance();
        calendar.setTime(date); // 设置为当前时间
        int month = calendar.get(Calendar.MONTH);
        calendar.set(Calendar.MONTH, month);
        date = calendar.getTime();
        String curDate = sdf.format(date) + "%";
        List<Map<String, Object>> flows = flowDao.getFlowByMain(3, 0, curDate);
        List<ExcelBean.Flow> flowList = new ArrayList<>();
        BigDecimal moneyIn = new BigDecimal("0");
        BigDecimal moneyOut = new BigDecimal("0");

        ExcelBean excelBean = new ExcelBean();

        for (Map<String, Object> map : flows) {
            ExcelBean.Flow flow = new ExcelBean.Flow();
            SimpleDateFormat sdfDate = new SimpleDateFormat("yyyy-MM-dd");
            Date fDate = (Date) map.get("f_date");
            flow.setFlowDate(sdfDate.format(fDate));
            flow.setMoney("￥" + map.get("money"));
            if (map.get("p_t_name") != null) {
                flow.setTypeName(map.get("p_t_name") + "/" + map.get("t_name"));
            } else {
                flow.setTypeName((String) map.get("t_name"));
            }
            flow.setNote((String) map.get("note"));
            flow.setActionName((String) map.get("h_name"));
            flowList.add(flow);
            flow.setAccountName((String) map.get("a_name"));
            if ((int) map.get("handle") == 1) {
                moneyOut = moneyOut.add(new BigDecimal((String) map.get("money")));
            } else if ((int) map.get("handle") == 0) {
                moneyIn = moneyIn.add(new BigDecimal((String) map.get("money")));
            } else {
                flow.setAccountName(map.get("a_name") + "->" + map.get("t_a_name"));
            }
        }
        excelBean.setMonthTotalIn("￥" + moneyIn.toString());
        excelBean.setMonthTotalOut("￥" + moneyOut.toString());
        excelBean.setMonthTotalEarn("￥" + (moneyIn.subtract(moneyOut)).toString());
        SimpleDateFormat sdfExcel = new SimpleDateFormat("yyyy年MM月");
        String excelDate = sdfExcel.format(date);
        excelBean.setCurrentMonth(excelDate);
        excelBean.setFlow(flowList);

        List<Account> accounts = accountDao.queryAllAccount();
        List<ExcelBean.Account> excelAccounts = new ArrayList<>();
        BigDecimal totalAsset = new BigDecimal("0");
        for (Account a : accounts) {
            ExcelBean.Account excelA = new ExcelBean.Account();
            excelA.setAccountMoney(a.getMoney());
            excelA.setAccountName(a.getaName());
            totalAsset = totalAsset.add(new BigDecimal(a.getMoney()));
            excelAccounts.add(excelA);
        }
        excelBean.setExcelAccounts(excelAccounts);
        excelBean.setAllAsset("￥" + totalAsset.toString());
        return excelBean;

    }



    private void writeMonthExcel(String excelDate, ExcelBean excelBean) {
        Date date = new Date();
        String excelFileName = excelDate + "月账单_" + date.getTime() + ".xls";
        String excelPath = excelFolder + excelFileName;
        ExcelWriter excelWriter = EasyExcel.write().file(excelPath)
                .withTemplate(baseExcelPath)
                .registerWriteHandler(new ExcelWriteHandler())
                .build();
        WriteSheet writeSheet = EasyExcel.writerSheet().build();
        excelWriter.fill(excelBean, writeSheet);
        excelWriter.fill(new FillWrapper("flow", excelBean.getFlow()), writeSheet);
        excelWriter.fill(new FillWrapper("account", excelBean.getExcelAccounts()), writeSheet);
        //excelWriter.fill(new FillWrapper("analyze",excelBean.getAnalyzeList()), writeSheet);
        //  excelWriter.write(flowList,writeSheet);
        excelWriter.finish();
        uploadExcel(excelPath, excelFileName, excelDate);
    }

    private void uploadExcel(String excelPath, String excelFileName, String title) {
        if (FileUtils.isExist(excelPath)) {
            fileMakeWebHook.sendFile(new File(excelPath), "month_excel", excelFileName);
        }
    }

    private void sendEmail(String fileUrl, String title) {

    }

    public static class ExcelWriteHandler implements CellWriteHandler {

        @Override
        public void beforeCellCreate(WriteSheetHolder writeSheetHolder, WriteTableHolder writeTableHolder, Row row, Head head, Integer integer, Integer integer1, Boolean aBoolean) {

        }

        @Override
        public void afterCellCreate(WriteSheetHolder writeSheetHolder, WriteTableHolder writeTableHolder, Cell cell, Head head, Integer integer, Boolean aBoolean) {

        }

        @Override
        public void afterCellDataConverted(WriteSheetHolder writeSheetHolder, WriteTableHolder writeTableHolder, CellData cellData, Cell cell, Head head, Integer integer, Boolean aBoolean) {

        }

        @Override
        public void afterCellDispose(WriteSheetHolder writeSheetHolder, WriteTableHolder writeTableHolder, List<CellData> list, Cell cell, Head head, Integer integer, Boolean aBoolean) {
            CellStyle cellStyle = cell.getCellStyle();
            cellStyle.setBorderBottom(BorderStyle.THIN);
            cellStyle.setBorderLeft(BorderStyle.THIN);
            cellStyle.setBorderRight(BorderStyle.THIN);
            cellStyle.setBorderTop(BorderStyle.THIN);
            cellStyle.setBottomBorderColor((short) 0);
            cellStyle.setTopBorderColor((short) 0);
            cellStyle.setLeftBorderColor((short) 0);
            cellStyle.setRightBorderColor((short) 0);
            cell.setCellStyle(cellStyle);
        }
    }


}
