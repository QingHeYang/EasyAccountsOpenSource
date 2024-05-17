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
        excelBean = makeAnaylizeExcel(excelBean, date);

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

    private ExcelBean makeAnaylizeExcel(ExcelBean excelBean, Date date) {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM");
        Calendar calendar = Calendar.getInstance();
        calendar.setTime(date); // 设置为当前时间
        String curDate = sdf.format(date) + "%";
        List<FlowType> currFlowTypes = flowDao.getFlowsByMonthAndType(curDate);
        currFlowTypes = addRootToList(currFlowTypes);
        calendar.set(Calendar.YEAR, calendar.get(Calendar.YEAR) - 1);
        List<FlowType> lastYearFlowTypes = flowDao.getFlowsByMonthAndType(sdf.format(calendar.getTime()) + "%");
        lastYearFlowTypes = addRootToList(lastYearFlowTypes);
        calendar.set(Calendar.YEAR, calendar.get(Calendar.YEAR) + 1);
        calendar.set(Calendar.MONTH, calendar.get(Calendar.MONTH) - 1);
        List<FlowType> lastMonthFlowTypes = flowDao.getFlowsByMonthAndType(sdf.format(calendar.getTime()) + "%");
        lastMonthFlowTypes = addRootToList(lastMonthFlowTypes);
        Map<Integer, ExcelBean.Analyze> analyzeMap = new HashMap<>();

        // Create or update analyzes for all flow types
        Stream.of(currFlowTypes, lastYearFlowTypes, lastMonthFlowTypes).flatMap(Collection::stream)
                .forEach(flow -> {
                    ExcelBean.Analyze analyze = analyzeMap.computeIfAbsent(flow.getId(), k -> new ExcelBean.Analyze());
                    if (analyze.getName() == null && flow.getTName() != null) {
                        analyze.setId(flow.getId());
                        analyze.setParent(flow.getParent());
                        analyze.setRoot(flow.getParent() == -1);
                        if (!analyze.isRoot()){
                            analyze.setName("　● "+flow.getTName());
                        }else {
                            analyze.setName(flow.getTName());
                        }
                    }
                });

        // Set current month money
        for (FlowType flow : currFlowTypes) {
            analyzeMap.get(flow.getId()).setMoney(flow.getMoney());
        }

        // Set last year money
        for (FlowType flow : lastYearFlowTypes) {
            analyzeMap.get(flow.getId()).setLastYearMoney(flow.getMoney());
        }

        // Set last month money
        for (FlowType flow : lastMonthFlowTypes) {
            analyzeMap.get(flow.getId()).setLastMonthMoney(flow.getMoney());
        }

        // Add all analyzes to ExcelBean
        List<ExcelBean.Analyze> analyzeList = new ArrayList<>(analyzeMap.values());
        excelBean.setAnalyzeList(orderList(analyzeList));
        return excelBean;
    }

    private List<ExcelBean.Analyze> orderList(List<ExcelBean.Analyze> analyzeList) {
        Map<Integer, ExcelBean.Analyze> analyzeMap = analyzeList.stream()
                .collect(Collectors.toMap(ExcelBean.Analyze::getId, a -> a));

        List<ExcelBean.Analyze> orderedList = new ArrayList<>();

        // 筛选出根节点并按原始列表中的顺序排序
        List<ExcelBean.Analyze> roots = analyzeList.stream()
                .filter(ExcelBean.Analyze::isRoot)
                .collect(Collectors.toList());

        // 为每个根节点添加它及其所有子节点
        for (ExcelBean.Analyze root : roots) {
            orderedList.add(root);
            addChildren(root, orderedList, analyzeMap);
        }

        for (ExcelBean.Analyze analyze : orderedList) {
            analyze.calculateMetrics();
        }

        return orderedList;
    }

    // 递归添加子节点的函数
    private void addChildren(ExcelBean.Analyze parent, List<ExcelBean.Analyze> orderedList, Map<Integer, ExcelBean.Analyze> analyzeMap) {
        for (ExcelBean.Analyze analyze : analyzeMap.values()) {
            if (analyze.getParent() == parent.getId()) {
                orderedList.add(analyze);
                addChildren(analyze, orderedList, analyzeMap); // 递归添加子子节点
            }
        }
    }


    private List<FlowType> addRootToList(List<FlowType> flowList) {
        Map<Integer, FlowType> rootFlowMap = new HashMap<>();
        for (FlowType flow : flowList) {
            if (flow.getParent() != -1 ) {
                if (!rootFlowMap.containsKey(flow.getParent())) {
                    FlowType rootFlow = new FlowType();
                    rootFlow.setId(flow.getParent());
                    rootFlow.setParent(-1);
                    rootFlow.setTName(flow.getParentName());
                    rootFlow.setMoney(flow.getMoney());
                    rootFlowMap.put(flow.getParent(), rootFlow);
                }else {
                    FlowType rootFlow = rootFlowMap.get(flow.getParent());
                    BigDecimal bigDecimal = rootFlow.getMoney();
                    rootFlow.setMoney(flow.getMoney().add(bigDecimal));
                }
            }
        }
        flowList.addAll(rootFlowMap.values());
        return flowList;
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
        excelWriter.fill(new FillWrapper("analyze",excelBean.getAnalyzeList()), writeSheet);
        //  excelWriter.write(flowList,writeSheet);
        excelWriter.finish();
        uploadExcel(excelPath, excelFileName, excelDate);
    }

    private void uploadExcel(String excelPath, String excelFileName, String title) {
        if (FileUtils.isExist(excelPath)) {
            fileMakeWebHook.sendFile(new File(excelPath), "month_excel", excelFileName);
            /*ossUtils.doUpload(new File(excelPath), "YD_JZ/excel/auto/", excelFileName, new OssUtils.OssUploadCallBack() {
                @Override
                public void onUploadSuccess(String ossUrl) {
                    LogUtils.log_print("上传完成，地址为： " + ossUrl);
                    sendEmail(ossUrl, title);
                }

                @Override
                public void onUploadFailed(String msg) {
                    LogUtils.log_print("上传失败: " + msg);

                }
            });*/
        }
    }

    private void sendEmail(String fileUrl, String title) {
//        emailUtils.setTitle(title + "月度账单生成报告");
//        emailUtils.setContent(title + "已生成");
//        emailUtils.sendEmail(fileUrl);
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
