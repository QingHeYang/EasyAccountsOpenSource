package com.deepblue.yd_jz.service;

import com.alibaba.excel.EasyExcel;
import com.alibaba.excel.ExcelWriter;
import com.alibaba.excel.write.metadata.WriteSheet;
import com.alibaba.excel.write.metadata.fill.FillWrapper;
import com.deepblue.yd_jz.controller.analysis.AnalysisBean;
import com.deepblue.yd_jz.controller.analysis.AnalysisExcelBean;
import com.deepblue.yd_jz.dao.flow.FlowDao;
import com.deepblue.yd_jz.dao.flow.FlowType;
import com.deepblue.yd_jz.utils.ExcelBean;
import com.deepblue.yd_jz.utils.FileMakeWebHook;
import com.deepblue.yd_jz.utils.FileUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.File;
import java.math.BigDecimal;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.stream.Collectors;
import java.util.stream.Stream;

@Service
@Slf4j
public class AnalysisService {

    @Autowired
    FlowDao flowDao;

    @Value("${baseAnalysisExcel}")
    private String baseExcelPath;

    @Value("${excelAnalysisFolder}")
    private String excelFolder;

    @Autowired
    FileMakeWebHook fileMakeWebHook;

    public AnalysisBean doAnalysis(String startMonth, String endMonth) {
        log.info("开始分析数据");
        String yoyStartMonth = "";
        String yoyEndMonth = "";
        String momStartMonth = "";
        boolean canDoMomAnalysis = false;
        if (startMonth != null && !startMonth.isEmpty()) {
            String[] startParts = startMonth.split("-");
            if (startParts.length == 2) {
                int year = Integer.parseInt(startParts[0]);
                int month = Integer.parseInt(startParts[1]);
                yoyStartMonth = (year - 1) + "-" + String.format("%02d", month);  // 保证月份是两位数字
            }
        }

        // 环比计算
        if ((endMonth == null || endMonth.isEmpty()) || startMonth.equals(endMonth)) {
            canDoMomAnalysis = true;
            if (startMonth != null && !startMonth.isEmpty()) {
                String[] startParts = startMonth.split("-");
                if (startParts.length == 2) {
                    int year = Integer.parseInt(startParts[0]);
                    int month = Integer.parseInt(startParts[1]);
                    if (month == 1) {
                        momStartMonth = (year - 1) + "-12";
                    } else {
                        momStartMonth = year + "-" + String.format("%02d", month - 1);  // 保证月份是两位数字
                    }
                }
            }
        } else { //不能做环比，因为有两个月份
            canDoMomAnalysis = false;
            String[] endParts = endMonth.split("-");
            if (endParts.length == 2) {
                int year = Integer.parseInt(endParts[0]);
                int month = Integer.parseInt(endParts[1]);
                yoyEndMonth = (year - 1) + "-" + String.format("%02d", month);  // 保证月份是两位数字
            }
            startMonth = startMonth + "-01";
            endMonth = convertToMaxDayOfMonth(endMonth);
        }
        log.info("当前起始月份: " + startMonth);
        log.info("当前结束月份: " + endMonth);
        log.info("同比起始月份: " + yoyStartMonth);
        log.info("同比结束月份: " + yoyEndMonth);
        log.info("环比起始月份: " + momStartMonth);
        String endYoyMonth = convertToMaxDayOfMonth(yoyEndMonth);
        log.info("同比处理后结束日期:  " + endYoyMonth);
        List<FlowType> currFlowTypes = flowDao.getFlowsTypeByStartMonthAndEndMonth(startMonth, endMonth);
        String yoyStartMonth_String = endYoyMonth==null? yoyStartMonth : yoyStartMonth + "-01";
        List<FlowType> yoyFlowTypes = flowDao.getFlowsTypeByStartMonthAndEndMonth(yoyStartMonth_String, endYoyMonth);
        List<FlowType> momFlowTypes = new ArrayList<>();
        if (canDoMomAnalysis) {
            momFlowTypes = flowDao.getFlowsTypeByStartMonthAndEndMonth(momStartMonth, "");
        }
        // 输出结果
        AnalysisBean analysisBean = new AnalysisBean();
        AnalysisExcelBean analysisExcelBean = new AnalysisExcelBean();
        String currentCircle = "";
        if (endMonth == null || endMonth.isEmpty()) {
            currentCircle = startMonth;
        } else {
            currentCircle = startMonth + " - " + endMonth;
        }
        analysisBean.setCurrentCircle(currentCircle);
        String yoyCircle = "";
        if (yoyEndMonth == null || yoyEndMonth.isEmpty()) {
            yoyCircle = yoyStartMonth;
        } else {
            yoyCircle = yoyStartMonth + " - " + yoyEndMonth;
        }

        analysisBean.setYoyCircle(yoyCircle);
        if (!momStartMonth.isEmpty()) {
            analysisBean.setMomCircle(momStartMonth);
        }

        currFlowTypes = addRootToList(currFlowTypes);
        if (yoyFlowTypes == null || yoyFlowTypes.isEmpty()) {
            log.info("同比数据为空");
            analysisBean.setYoyList(new ArrayList<>(0));
        } else {
            log.info("同比数据不为空，合计: " + yoyFlowTypes.size() + " 条");
            yoyFlowTypes = addRootToList(yoyFlowTypes);
            List<AnalysisBean.SingleTypeBean> yoyAList = makeCombine(currFlowTypes, yoyFlowTypes);
            analysisBean.setYoyList(yoyAList);
        }
        if (momFlowTypes == null || momFlowTypes.isEmpty()) {
            log.info("环比数据为空");
            analysisBean.setMomList(new ArrayList<>(0));
        } else {
            log.info("环比数据不为空，合计: " + momFlowTypes.size() + " 条");
            momFlowTypes = addRootToList(momFlowTypes);
            List<AnalysisBean.SingleTypeBean> momAList = makeCombine(currFlowTypes, momFlowTypes);
            analysisBean.setMomList(momAList);
        }
        log.info("分析数据完成");

        return analysisBean;
    }

    public AnalysisExcelBean doMakeAnalysisExcel(String startMonth, String endMonth) {
        log.info("开始分析数据");
        String yoyStartMonth = "";
        String yoyEndMonth = "";
        String momStartMonth = "";
        boolean canDoMomAnalysis = false;
        if (startMonth != null && !startMonth.isEmpty()) {
            String[] startParts = startMonth.split("-");
            if (startParts.length == 2) {
                int year = Integer.parseInt(startParts[0]);
                int month = Integer.parseInt(startParts[1]);
                yoyStartMonth = (year - 1) + "-" + String.format("%02d", month);  // 保证月份是两位数字
            }
        }

        // 环比计算
        if ((endMonth == null || endMonth.isEmpty()) || startMonth.equals(endMonth)) {
            canDoMomAnalysis = true;
            if (startMonth != null && !startMonth.isEmpty()) {
                String[] startParts = startMonth.split("-");
                if (startParts.length == 2) {
                    int year = Integer.parseInt(startParts[0]);
                    int month = Integer.parseInt(startParts[1]);
                    if (month == 1) {
                        momStartMonth = (year - 1) + "-12";
                    } else {
                        momStartMonth = year + "-" + String.format("%02d", month - 1);  // 保证月份是两位数字
                    }
                }
            }
        } else {
            canDoMomAnalysis = false;
            String[] endParts = endMonth.split("-");
            if (endParts.length == 2) {
                int year = Integer.parseInt(endParts[0]);
                int month = Integer.parseInt(endParts[1]);
                yoyEndMonth = (year - 1) + "-" + String.format("%02d", month);  // 保证月份是两位数字
            }
            startMonth = startMonth + "-01";
            endMonth = convertToMaxDayOfMonth(endMonth);
        }
        log.info("当前起始月份: " + startMonth);
        log.info("当前结束月份: " + endMonth);
        log.info("同比起始月份: " + yoyStartMonth);
        log.info("同比结束月份: " + yoyEndMonth);
        log.info("环比起始月份: " + momStartMonth);
        String endYoyMonth = convertToMaxDayOfMonth(yoyEndMonth);
        log.info("同比处理后结束日期:  " + endYoyMonth);
        List<FlowType> currFlowTypes = flowDao.getFlowsTypeByStartMonthAndEndMonth(startMonth, endMonth);
        String yoyStartMonth_String = endYoyMonth==null ? yoyStartMonth : yoyStartMonth + "-01";
        List<FlowType> yoyFlowTypes = flowDao.getFlowsTypeByStartMonthAndEndMonth(yoyStartMonth_String, endYoyMonth);
        List<FlowType> momFlowTypes = new ArrayList<>();
        if (canDoMomAnalysis) {
            momFlowTypes = flowDao.getFlowsTypeByStartMonthAndEndMonth(momStartMonth, "");
        }
        // 输出结果
        AnalysisExcelBean excelBean = new AnalysisExcelBean();
        String currentCircle = "";
        if (endMonth == null || endMonth.isEmpty()) {
            currentCircle = startMonth;
        } else {
            currentCircle = startMonth + " - " + endMonth;
        }
        excelBean.setCurrentCircle("当前周期:  "+currentCircle);
        String yoyCircle = "";
        if (yoyEndMonth == null || yoyEndMonth.isEmpty()) {
            yoyCircle = yoyStartMonth;
        } else {
            yoyCircle = yoyStartMonth + " - " + yoyEndMonth;
        }

        excelBean.setYoyCircle("同比周期:  "+yoyCircle);
        if (!momStartMonth.isEmpty()) {
            excelBean.setMomCircle("环比周期:  "+momStartMonth);
        }

        currFlowTypes = addRootToList(currFlowTypes);
        yoyFlowTypes = addRootToList(yoyFlowTypes);
        momFlowTypes = addRootToList(momFlowTypes);
        List<AnalysisExcelBean.Analyze> analyzeList = makeCombineExcel(currFlowTypes, yoyFlowTypes, momFlowTypes);
        excelBean.setAnalyzeList(analyzeList);

        log.info("分析数据完成");
        writeExcel(excelBean);
        return excelBean;
    }

    private List<AnalysisBean.SingleTypeBean> makeCombine(List<FlowType> cur, List<FlowType> circle) {
        Map<Integer, AnalysisBean.SingleTypeBean> analyzeMap = new HashMap<>();

        // Create or update analyzes for all flow types
        Stream.of(cur, circle).flatMap(Collection::stream)
                .forEach(flow -> {
                    AnalysisBean.SingleTypeBean analyze = analyzeMap.computeIfAbsent(flow.getId(), k -> new AnalysisBean.SingleTypeBean());
                    if (analyze.getName() == null && flow.getTName() != null) {
                        analyze.setId(flow.getId());
                        analyze.setParent(flow.getParent());
                        analyze.setRoot(flow.getParent() == -1);
                        if (!analyze.isRoot()) {
                            analyze.setName("　● " + flow.getTName());
                        } else {
                            analyze.setName(flow.getTName());
                        }
                    }
                });
        for (FlowType flow : cur) {
            //log.info("当前数据: " + flow.getTName() + " " + flow.getMoney());
            analyzeMap.get(flow.getId()).setMoney(flow.getMoney());
            //log.info("设置完: " + analyzeMap.get(flow.getId()).getMoney());
        }

        for (FlowType flow : circle) {
            analyzeMap.get(flow.getId()).setCompareMoney(flow.getMoney());
        }
        List<AnalysisBean.SingleTypeBean> analyzeList = new ArrayList<>(analyzeMap.values());


        Map<Integer, AnalysisBean.SingleTypeBean> analyzeRebaseMap = analyzeList.stream()
                .collect(Collectors.toMap(AnalysisBean.SingleTypeBean::getId, a -> a));

        List<AnalysisBean.SingleTypeBean> orderedList = new ArrayList<>();

        // 筛选出根节点并按原始列表中的顺序排序
        List<AnalysisBean.SingleTypeBean> roots = analyzeList.stream()
                .filter(AnalysisBean.SingleTypeBean::isRoot)
                .collect(Collectors.toList());

        // 为每个根节点添加它及其所有子节点
        for (AnalysisBean.SingleTypeBean root : roots) {
            orderedList.add(root);
            addChildren(root, orderedList, analyzeRebaseMap);
        }

        for (AnalysisBean.SingleTypeBean analyze : orderedList) {
            analyze.calculateComparison();
        }
        return orderedList;
    }

    private List<AnalysisExcelBean.Analyze> makeCombineExcel(List<FlowType> cur, List<FlowType> yoy, List<FlowType> mom) {
        Map<Integer, AnalysisExcelBean.Analyze> analyzeMap = new HashMap<>();

        // Create or update analyzes for all flow types
        Stream.of(cur, yoy, mom).flatMap(Collection::stream)
                .forEach(flow -> {
                    AnalysisExcelBean.Analyze analyze = analyzeMap.computeIfAbsent(flow.getId(), k -> new AnalysisExcelBean.Analyze());
                    if (analyze.getName() == null && flow.getTName() != null) {
                        analyze.setId(flow.getId());
                        analyze.setParent(flow.getParent());
                        analyze.setRoot(flow.getParent() == -1);
                        if (!analyze.isRoot()) {
                            analyze.setName("　● " + flow.getTName());
                        } else {
                            analyze.setName(flow.getTName());
                        }
                    }
                });
        for (FlowType flow : cur) {
            //log.info("当前数据: " + flow.getTName() + " " + flow.getMoney());
            analyzeMap.get(flow.getId()).setMoney(flow.getMoney());
            //log.info("设置完: " + analyzeMap.get(flow.getId()).getMoney());
        }

        for (FlowType flow : yoy) {
            analyzeMap.get(flow.getId()).setLastYearMoney(flow.getMoney());
        }

        for (FlowType flow : mom) {
            analyzeMap.get(flow.getId()).setLastMonthMoney(flow.getMoney());
        }

        List<AnalysisExcelBean.Analyze> analyzeList = new ArrayList<>(analyzeMap.values());


        Map<Integer, AnalysisExcelBean.Analyze> analyzeRebaseMap = analyzeList.stream()
                .collect(Collectors.toMap(AnalysisExcelBean.Analyze::getId, a -> a));

        List<AnalysisExcelBean.Analyze> orderedList = new ArrayList<>();

        // 筛选出根节点并按原始列表中的顺序排序
        List<AnalysisExcelBean.Analyze> roots = analyzeList.stream()
                .filter(AnalysisExcelBean.Analyze::isRoot)
                .collect(Collectors.toList());

        // 为每个根节点添加它及其所有子节点
        for (AnalysisExcelBean.Analyze root : roots) {
            orderedList.add(root);
            addChildrenExcel(root, orderedList, analyzeRebaseMap);
        }

        for (AnalysisExcelBean.Analyze analyze : orderedList) {
            analyze.caculateComparison();
        }
        return orderedList;
    }


    // 递归添加子节点的函数
    private void addChildren(AnalysisBean.SingleTypeBean parent, List<AnalysisBean.SingleTypeBean> orderedList, Map<Integer, AnalysisBean.SingleTypeBean> analyzeMap) {
        for (AnalysisBean.SingleTypeBean analyze : analyzeMap.values()) {
            if (analyze.getParent() == parent.getId()) {
                orderedList.add(analyze);
                addChildren(analyze, orderedList, analyzeMap); // 递归添加子子节点
            }
        }
    }


    private void addChildrenExcel(AnalysisExcelBean.Analyze parent, List<AnalysisExcelBean.Analyze> orderedList, Map<Integer, AnalysisExcelBean.Analyze> analyzeMap) {
        for (AnalysisExcelBean.Analyze analyze : analyzeMap.values()) {
            if (analyze.getParent() == parent.getId()) {
                orderedList.add(analyze);
                addChildrenExcel(analyze, orderedList, analyzeMap); // 递归添加子子节点
            }
        }
    }


    private List<FlowType> addRootToList(List<FlowType> flowList) {
        Map<Integer, FlowType> rootFlowMap = new HashMap<>();
        for (FlowType flow : flowList) {
            if (flow.getParent() != -1) {
                if (!rootFlowMap.containsKey(flow.getParent())) {
                    FlowType rootFlow = new FlowType();
                    rootFlow.setId(flow.getParent());
                    rootFlow.setParent(-1);
                    rootFlow.setTName(flow.getParentName());
                    rootFlow.setMoney(flow.getMoney());
                    rootFlowMap.put(flow.getParent(), rootFlow);
                } else {
                    FlowType rootFlow = rootFlowMap.get(flow.getParent());
                    BigDecimal bigDecimal = rootFlow.getMoney();
                    rootFlow.setMoney(flow.getMoney().add(bigDecimal));
                }
            }
        }
        flowList.addAll(rootFlowMap.values());
        return flowList;
    }

    public static String convertToMaxDayOfMonth(String dateString) {
        try {
            // 解析传入的日期字符串
            SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM");
            Calendar calendar = Calendar.getInstance();
            calendar.setTime(sdf.parse(dateString));

            // 获取当月的最大天数
            int maxDayOfMonth = calendar.getActualMaximum(Calendar.DAY_OF_MONTH);

            // 设置日期格式为yyyy-MM-dd，并将dd设置为当月的最大天数
            sdf.applyPattern("yyyy-MM-dd");
            calendar.set(Calendar.DAY_OF_MONTH, maxDayOfMonth);
            return sdf.format(calendar.getTime());
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }

    public void writeExcel(AnalysisExcelBean excelBean){
        String headerName =excelBean.getCurrentCircle().substring(6);
        writeMonthExcel(headerName+"财务分析报表",excelBean);
    }

    private void writeMonthExcel(String excelDate, AnalysisExcelBean excelBean) {
        Date date = new Date();
        String excelFileName = excelDate + "_" + date.getTime() + ".xls";
        String excelPath = excelFolder + excelFileName;
        ExcelWriter excelWriter = EasyExcel.write().file(excelPath)
                .withTemplate(baseExcelPath)
                .registerWriteHandler(new ExcelService.ExcelWriteHandler())
                .build();
        WriteSheet writeSheet = EasyExcel.writerSheet().build();
        excelWriter.fill(excelBean, writeSheet);
        excelWriter.fill(new FillWrapper("analyze", excelBean.getAnalyzeList()), writeSheet);
        //excelWriter.fill(new FillWrapper("analyze",excelBean.getAnalyzeList()), writeSheet);
        //  excelWriter.write(flowList,writeSheet);
        excelWriter.finish();
        uploadExcel(excelPath, excelFileName, excelDate);
    }

    private void uploadExcel(String excelPath, String excelFileName, String title) {
        if (FileUtils.isExist(excelPath)) {
            fileMakeWebHook.sendFile(new File(excelPath), "analysis_excel", excelFileName);
        }
    }
}
