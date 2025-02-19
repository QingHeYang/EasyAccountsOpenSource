package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.dao.jpa.FlowRepository;
import com.deepblue.yd_jz.dao.jpa.TypeRepository;
import com.deepblue.yd_jz.dao.mybatis.FlowDao;
import com.deepblue.yd_jz.dto.AnalysisTypeListRequestDto;
import com.deepblue.yd_jz.dto.AnalysisTypeListResponseDto;
import com.deepblue.yd_jz.dto.AnalysisTypeRequestDto;
import com.deepblue.yd_jz.dto.AnalysisTypeResponseDto;
import com.deepblue.yd_jz.entity.FlowJpaEntity;
import com.deepblue.yd_jz.entity.Type;
import com.deepblue.yd_jz.utils.DateUtils;
import org.apache.poi.ss.formula.functions.T;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class AnalysisV2Service {

    @Autowired
    FlowRepository flowRepository;

    @Autowired
    TypeRepository typeRepository;

    @Autowired
    DateUtils dateUtils;

    private HashMap<Integer, AnalysisTypeListResponseDto.TypeBean> outTypeMap;
    private HashMap<Integer, AnalysisTypeListResponseDto.TypeBean> inTypeMap;

    @Transactional(rollbackFor = Exception.class)
    public AnalysisTypeListResponseDto getAnalysisTypeList(AnalysisTypeListRequestDto requestDto) {
        AnalysisTypeListResponseDto analysis = new AnalysisTypeListResponseDto();
        analysis.setTotalIn("0.00");
        analysis.setTotalOut("0.00");
        analysis.setShowInTypeList(new ArrayList<>());
        analysis.setShowOutTypeList(new ArrayList<>());
        analysis.setAllInTypeList(new ArrayList<>());
        analysis.setAllOutTypeList(new ArrayList<>());
        String startDate = dateUtils.buildFullDate(requestDto.getStart(), true);
        String endDate = dateUtils.buildFullDate(requestDto.getEnd(), false);
        List<FlowJpaEntity> flows = flowRepository.findFlowsByHandleAndDateRange(startDate, endDate);
        if (flows == null || flows.isEmpty()) {
            return analysis;
        }
        outTypeMap = new HashMap<>();
        inTypeMap = new HashMap<>();
        for (FlowJpaEntity flow : flows) {
            // 如果不展示禁用的分类，且当前 flow 关联的 type 是禁用的，则跳过
            if (!requestDto.getShowDisableAnalysisType()) {
                if (flow.getType().getAnalysisDisable() != null && flow.getType().getAnalysisDisable()) {
                    continue;
                }
            }
            setTypeBean(analysis, flow);
        }
        if (requestDto.getCombineSubType()) {
            combineTypeBean(true);
            combineTypeBean(false);
        }
        refreshPercent(analysis);

        return analysis;
    }

    // 设置 type 对象
    private void setTypeBean(AnalysisTypeListResponseDto analysis, FlowJpaEntity flow) {
        BigDecimal flowMoney = new BigDecimal(flow.getMoney());
        BigDecimal totalIn = new BigDecimal(analysis.getTotalIn() == null ? "0" : analysis.getTotalIn());
        BigDecimal totalOut = new BigDecimal(analysis.getTotalOut() == null ? "0" : analysis.getTotalOut());
        // 获取当前 flow 关联的 type 对象
        Type type = flow.getType();
        HashMap<Integer, AnalysisTypeListResponseDto.TypeBean> typeMap;
        if (flow.getAction().getHandle() == 0) {
            totalIn = totalIn.add(flowMoney);
            analysis.setTotalIn(totalIn.setScale(2, RoundingMode.HALF_UP).toString());
            typeMap = inTypeMap;
        } else {
            totalOut = totalOut.add(flowMoney);
            analysis.setTotalOut(totalOut.setScale(2, RoundingMode.HALF_UP).toString());
            typeMap = outTypeMap;
        }
        AnalysisTypeListResponseDto.TypeBean bean = typeMap.get(type.getId());
        if (bean == null) {
            bean = new AnalysisTypeListResponseDto.TypeBean();
            bean.setId(type.getId());
            bean.setParentId(type.getParent());
            if (type.getParent() != -1) {
                Type parent = typeRepository.findTypeById(type.getParent());
                bean.setName(parent.getTName() + "/" + type.getTName());
            } else {
                bean.setName(type.getTName());
            }
            bean.setMoney(flowMoney.setScale(2, RoundingMode.HALF_UP).toString());
            typeMap.put(type.getId(), bean);
        } else {
            BigDecimal currentMoney = new BigDecimal(bean.getMoney());
            BigDecimal updatedMoney = currentMoney.add(flowMoney);
            bean.setMoney(updatedMoney.setScale(2, RoundingMode.HALF_UP).toString());
        }
    }

    // 合并子分类
    private void combineTypeBean(boolean isOut) {
        HashMap<Integer, AnalysisTypeListResponseDto.TypeBean> parentMap = new HashMap<>();
        HashMap<Integer, AnalysisTypeListResponseDto.TypeBean> dealMap = isOut ? outTypeMap : inTypeMap;
        for (AnalysisTypeListResponseDto.TypeBean bean : dealMap.values()) {
            if (bean.getParentId() != -1) {
                AnalysisTypeListResponseDto.TypeBean parentBean = parentMap.get(bean.getParentId());
                if (parentBean == null) {
                    Type parent = typeRepository.findTypeById(bean.getParentId());
                    parentBean = new AnalysisTypeListResponseDto.TypeBean();
                    parentBean.setId(bean.getParentId());
                    parentBean.setParentId(-1);
                    parentBean.setMoney(bean.getMoney());
                    parentBean.setName(parent.getTName());
                    parentMap.put(bean.getParentId(), parentBean);
                } else {
                    BigDecimal parentMoney = new BigDecimal(parentBean.getMoney());
                    BigDecimal currentMoney = new BigDecimal(bean.getMoney());
                    parentBean.setMoney(parentMoney.add(currentMoney).setScale(2, RoundingMode.HALF_UP).toString());
                }
            } else {
                parentMap.put(bean.getId(), bean);
            }
        }
        dealMap.clear();
        dealMap.putAll(parentMap);
    }

    // 刷新百分比
    private void refreshPercent(AnalysisTypeListResponseDto analysis) {
        BigDecimal totalIn = new BigDecimal(analysis.getTotalIn());
        BigDecimal totalOut = new BigDecimal(analysis.getTotalOut());
        for (AnalysisTypeListResponseDto.TypeBean bean : inTypeMap.values()) {
            BigDecimal money = new BigDecimal(bean.getMoney());
            BigDecimal percent = money.divide(totalIn, 4, RoundingMode.HALF_UP).multiply(new BigDecimal(100));
            bean.setPercent(percent.floatValue());
        }
        analysis.setAllInTypeList(sortTypeBeanToList(inTypeMap));
        analysis.setShowInTypeList(buildShowTypeList(analysis.getAllInTypeList(), 5f));
        for (AnalysisTypeListResponseDto.TypeBean bean : outTypeMap.values()) {
            BigDecimal money = new BigDecimal(bean.getMoney());
            BigDecimal percent = money.divide(totalOut, 4, RoundingMode.HALF_UP).multiply(new BigDecimal(100));
            bean.setPercent(percent.floatValue());
        }
        analysis.setAllOutTypeList(sortTypeBeanToList(outTypeMap));
        analysis.setShowOutTypeList(buildShowTypeList(analysis.getAllOutTypeList(), 5f));
    }

    // 将 map 转换为 list 并排序
    private List<AnalysisTypeListResponseDto.TypeBean> sortTypeBeanToList(HashMap<Integer, AnalysisTypeListResponseDto.TypeBean> typeMap) {
        return typeMap.entrySet()
                .stream()
                .sorted((o1, o2) -> {
                    BigDecimal money1 = new BigDecimal(o1.getValue().getMoney());
                    BigDecimal money2 = new BigDecimal(o2.getValue().getMoney());
                    return money2.compareTo(money1); // 降序
                })
                .map(Map.Entry::getValue)
                .collect(Collectors.toList());
    }

    /**
     * 从已倒序排序的列表中，取出末尾累加 percent 不超过 threshold（5%）的 bean，
     * 将它们合并为一个 "other" bean，并返回最终列表。
     *
     * @param dealList  已按 percent 倒序排序的 TypeBean 列表
     * @param threshold 合并阈值（例如 5f 表示 5%）
     * @return 合并后的列表
     */
    private List<AnalysisTypeListResponseDto.TypeBean> buildShowTypeList(List<AnalysisTypeListResponseDto.TypeBean> dealList, float threshold) {
        if (dealList == null || dealList.isEmpty()) {
            return new ArrayList<>();
        }
        ArrayList<AnalysisTypeListResponseDto.TypeBean> list = new ArrayList<>(dealList);
        BigDecimal thresholdMoney = new BigDecimal(threshold);
        BigDecimal cumulativeMoney = BigDecimal.ZERO;
        List<AnalysisTypeListResponseDto.TypeBean> groupForOther = new ArrayList<>();

        while (cumulativeMoney.compareTo(thresholdMoney) < 0) {
            AnalysisTypeListResponseDto.TypeBean bean = list.get(list.size() - 1);
            BigDecimal percent = new BigDecimal(bean.getPercent());
            if (cumulativeMoney.add(percent).compareTo(thresholdMoney) <= 0) {
                cumulativeMoney = cumulativeMoney.add(percent);
                groupForOther.add(bean);
                list.remove(bean);
            } else {
                // 超过阈值后，不包含当前 bean，直接退出循环
                break;
            }
        }

        // 如果有合并的项，则创建 "other" bean
        if (!groupForOther.isEmpty()) {
            AnalysisTypeListResponseDto.TypeBean otherBean = new AnalysisTypeListResponseDto.TypeBean();
            otherBean.setId(-2); // 特殊标识，可根据业务需求调整
            otherBean.setParentId(0);
            otherBean.setName("合并小项");

            // 累加所有合并项的 money（字符串转 BigDecimal 累加）
            BigDecimal totalMoney = BigDecimal.ZERO;
            for (AnalysisTypeListResponseDto.TypeBean bean : groupForOther) {
                totalMoney = totalMoney.add(new BigDecimal(bean.getMoney()));
            }
            otherBean.setMoney(totalMoney.setScale(2, RoundingMode.HALF_UP).toString());
            float remainingSum = 0f;
            for (AnalysisTypeListResponseDto.TypeBean bean : list) {
                remainingSum += bean.getPercent();
            }
            BigDecimal otherPercent = new BigDecimal(100f - remainingSum);
            otherBean.setPercent(otherPercent.setScale(2, RoundingMode.HALF_UP).floatValue());
            list.add(otherBean);
        }
        // 最后重新排序（倒序）保证展示顺序
        //list.sort((a, b) -> Float.compare(b.getPercent(), a.getPercent()));
        return list;
    }


    @Transactional(rollbackFor = Exception.class)
    public AnalysisTypeResponseDto getAnalysisTypeMonthData(AnalysisTypeRequestDto typeRequestDto) {
        String startDate = dateUtils.buildFullDate(typeRequestDto.getStart(), true);
        String endDate = dateUtils.buildFullDate(typeRequestDto.getEnd(), false);
        AnalysisTypeResponseDto responseDto = new AnalysisTypeResponseDto();
        responseDto.setTypeId(typeRequestDto.getTypeId());
        Type type = typeRepository.findTypeById(typeRequestDto.getTypeId());
        List<FlowJpaEntity> flows = new ArrayList<>();
        if (type.getParent() != -1) {
            Type parent = typeRepository.findTypeById(type.getParent());
            responseDto.setTypeName(parent.getTName() + "/" + type.getTName());
            flows = flowRepository.findByFDateBetweenAndType(startDate, endDate, type.getId());
        } else {
            responseDto.setTypeName(type.getTName());
            List<Type> types = typeRepository.findByParent(type.getId());
            if (types == null || types.isEmpty()) {
                flows = flowRepository.findByFDateBetweenAndType(startDate, endDate, type.getId());
            } else {
                for (Type subType : types) {
                    List<FlowJpaEntity> subFlows = flowRepository.findByFDateBetweenAndType(startDate, endDate, subType.getId());
                    flows.addAll(subFlows);
                }
            }
        }
        setYearData(responseDto, flows);
        sortYearMonthData(responseDto);
        setTotalIncomeAndOutcome(responseDto);
        return responseDto;
    }

    private void setTotalIncomeAndOutcome(AnalysisTypeResponseDto responseDto) {
        BigDecimal totalIncome = new BigDecimal("0.00");
        BigDecimal totalOutcome = new BigDecimal("0.00");
       for (AnalysisTypeResponseDto.YearData yearData : responseDto.getYearData()) {
            BigDecimal income = new BigDecimal(yearData.getIncome());
            BigDecimal outcome = new BigDecimal(yearData.getOutcome());
            totalIncome = totalIncome.add(income);
            totalOutcome = totalOutcome.add(outcome);
        }
        responseDto.setTotalIncome(totalIncome.setScale(2, RoundingMode.HALF_UP).toString());
        responseDto.setTotalOutcome(totalOutcome.setScale(2, RoundingMode.HALF_UP).toString());
    }

    private void setYearData(AnalysisTypeResponseDto responseDto, List<FlowJpaEntity> flows) {
        HashMap<String, AnalysisTypeResponseDto.YearData> yearDataMap = new HashMap<>();
        for (FlowJpaEntity flow : flows) {
            String year = flow.getFDate().substring(0, 4);
            AnalysisTypeResponseDto.YearData yearData = yearDataMap.get(year);
            if (yearData == null) {
                yearData = new AnalysisTypeResponseDto.YearData();
                yearData.setYear(Integer.parseInt(year));
                yearData.setIncome("0.00");
                yearData.setOutcome("0.00");
                yearData.setMonthData(new ArrayList<>());
                yearDataMap.put(year, yearData);
            }
            BigDecimal money = new BigDecimal(flow.getMoney());
            if (flow.getAction().getHandle() == 0) {
                BigDecimal income = new BigDecimal(yearData.getIncome());
                yearData.setIncome(income.add(money).setScale(2, RoundingMode.HALF_UP).toString());
            } else {
                BigDecimal outcome = new BigDecimal(yearData.getOutcome());
                yearData.setOutcome(outcome.add(money).setScale(2, RoundingMode.HALF_UP).toString());
            }
            setMonthData(yearData, flow);
        }
        responseDto.setYearData(new ArrayList<>(yearDataMap.values()));
    }

    private void setMonthData(AnalysisTypeResponseDto.YearData yearData, FlowJpaEntity flow) {
        String month = flow.getFDate().substring(5, 7);
        AnalysisTypeResponseDto.MonthData monthData = new AnalysisTypeResponseDto.MonthData();
        monthData.setMonth(Integer.parseInt(month));
        monthData.setIncome("0.00");
        monthData.setOutcome("0.00");
        for (AnalysisTypeResponseDto.MonthData data : yearData.getMonthData()) {
            if (data.getMonth()==(Integer.parseInt(month))) {
                monthData = data;
                break;
            }
        }
        BigDecimal money = new BigDecimal(flow.getMoney());
        if (flow.getAction().getHandle() == 0) {
            BigDecimal income = new BigDecimal(monthData.getIncome());
            monthData.setIncome(income.add(money).setScale(2, RoundingMode.HALF_UP).toString());
        } else {
            BigDecimal outcome = new BigDecimal(monthData.getOutcome());
            monthData.setOutcome(outcome.add(money).setScale(2, RoundingMode.HALF_UP).toString());
        }
        if (!yearData.getMonthData().contains(monthData)) {
            yearData.getMonthData().add(monthData);
        }
    }

    private void sortYearMonthData(AnalysisTypeResponseDto responseDto) {
        responseDto.getYearData().sort((o1, o2) -> o2.getYear() - o1.getYear());
        for (AnalysisTypeResponseDto.YearData yearData : responseDto.getYearData()) {
            yearData.getMonthData().sort((o1, o2) -> o2.getMonth() - o1.getMonth());
        }
    }
}
