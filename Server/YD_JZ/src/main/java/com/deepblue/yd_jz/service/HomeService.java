package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.dao.jpa.FlowRepository;
import com.deepblue.yd_jz.dto.HomeDto;
import com.deepblue.yd_jz.dto.VersionDto;
import com.deepblue.yd_jz.entity.Account;
import com.deepblue.yd_jz.dao.jpa.AccountRepository;
import com.deepblue.yd_jz.dao.mybatis.FlowDao;
import com.deepblue.yd_jz.entity.FlowJpaEntity;
import com.deepblue.yd_jz.entity.FlowYear;
import com.deepblue.yd_jz.utils.ContentValues;
import com.deepblue.yd_jz.utils.VersionUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.text.NumberFormat;
import java.time.Year;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class HomeService {
    @Autowired
    FlowDao flowDao;

    @Autowired
    AccountRepository accountDao;

    @Autowired
    ActionService actionDao;

    @Autowired
    FlowRepository flowRepository;

    @Autowired
    VersionUtils versionUtils;


    @Transactional(rollbackFor = Exception.class)
    public HomeDto getHomeBean() {
        HomeDto homeDto = new HomeDto();
        setAccountsBean(homeDto);
        int currentYear = Year.now().getValue();
        setYearlySummary(homeDto, currentYear);
        return homeDto;
    }

    @Transactional(rollbackFor = Exception.class)
    public HomeDto getHomeInfoByTime(int year) {
        HomeDto homeDto = new HomeDto();
        setAccountsBean(homeDto);
        setYearlySummary(homeDto, year);
        setMonthDetailBean(homeDto, year);
        return homeDto;
    }

    // 为 HomeDto 设置账户信息
    public HomeDto setAccountsBean(HomeDto homeDto) {
        BigDecimal totalAsset = new BigDecimal("0");
        BigDecimal exemptAsset = new BigDecimal("0");
        List<Account> accounts = accountDao.findByDisableFalse();
        for (Account account : accounts) {
            BigDecimal accountAsset = new BigDecimal(account.getMoney());
            String exemptStr = account.getExemptMoney();
            if (exemptStr.equals("")) {
                exemptStr = "0";
            }
            BigDecimal exemptAccountAsset = new BigDecimal(exemptStr);
            totalAsset = totalAsset.add(accountAsset);
            exemptAsset = exemptAsset.add(exemptAccountAsset);
        }
        homeDto.setTotalAsset(totalAsset.toString());
        homeDto.setNetAsset(totalAsset.subtract(exemptAsset).toString());
        NumberFormat nf = NumberFormat.getPercentInstance();
        List<HomeDto.HomeAccountBean> homeAccounts = new ArrayList<>();
        for (Account account : accounts) {
            HomeDto.HomeAccountBean hab = new HomeDto.HomeAccountBean();
            hab.setId(account.getId());
            hab.setAccountName(account.getAName());
            hab.setAccountAsset(account.getMoney());
            hab.setExemptAsset(account.getExemptMoney());
            hab.setNote(account.getNote());
            BigDecimal accountAsset = new BigDecimal(account.getMoney());
            BigDecimal percent = accountAsset.divide(totalAsset, 3, RoundingMode.HALF_DOWN);
            nf.setMaximumFractionDigits(2);
            String percentStr = nf.format(percent.doubleValue());
            hab.setPercent(percentStr.substring(0, percentStr.length() - 1));
            homeAccounts.add(hab);
        }
        homeDto.setAccounts(homeAccounts);
        return homeDto;
    }

    // 为 HomeDto 设置年度汇总
    public HomeDto setYearlySummary(HomeDto homeDto, int year) {
        FlowYear flowYear = flowDao.getYearlySummary(year);
        if (flowYear == null) {
            homeDto.setYearOutCome("0.00");
            homeDto.setYearIncome("0.00");
            homeDto.setYearBalance("0.00");
            return homeDto;
        }
        BigDecimal totalEarns = new BigDecimal(flowYear.getTotalEarns());
        BigDecimal totalCosts = new BigDecimal(flowYear.getTotalCosts());
        BigDecimal totalBalance = new BigDecimal(flowYear.getTotalBalance());
        String formattedTotalCosts = totalCosts.setScale(2, RoundingMode.HALF_UP).toString();
        String formattedTotalEarns = totalEarns.setScale(2, RoundingMode.HALF_UP).toString();
        String formattedTotalBalance = totalBalance.setScale(2, RoundingMode.HALF_UP).toString();

        homeDto.setYearOutCome(formattedTotalCosts);
        homeDto.setYearIncome(formattedTotalEarns);
        homeDto.setYearBalance(formattedTotalBalance);
        return homeDto;
    }

    // 为 HomeDto 设置月度明细
    public HomeDto setMonthDetailBean(HomeDto homeDto, int year) {
        Map<Integer, List<FlowJpaEntity>> monthlyFlows = getFlowsByYearGroupedByMonth(year);
        // 确保 monthDetails 不为空
        if (homeDto.getMonthDetails() == null) {
            homeDto.setMonthDetails(new ArrayList<>());
        }
        for (Map.Entry<Integer, List<FlowJpaEntity>> entry : monthlyFlows.entrySet()) {
            Integer month = entry.getKey();               // 月份（1~12）
            List<FlowJpaEntity> flows = entry.getValue(); // 该月的所有Flow数据

            // 创建一个月度明细对象
            HomeDto.HomeMonthDetailBean monthDetailBean = new HomeDto.HomeMonthDetailBean();
            // 将月份设置为 “1月”、“2月” 等格式
            monthDetailBean.setMonth(month+"");
            BigDecimal income = new BigDecimal("0");
            BigDecimal outcome = new BigDecimal("0");
            BigDecimal balance;
            for (FlowJpaEntity flow : flows) {
                // 计算该月的收入和支出

                if (!flow.isFDisable()) {
                    if (flow.getAction().getHandle()== ContentValues.ACTION_ADD){
                        income = income.add(new BigDecimal(flow.getMoney()));
                    }else if (flow.getAction().getHandle()== ContentValues.ACTION_SUB){
                        outcome = outcome.add(new BigDecimal(flow.getMoney()));
                    }
                }
            }
            balance = income.subtract(outcome);
            String formattedIncome = income.setScale(2, RoundingMode.HALF_UP).toString();
            String formattedOutcome = outcome.setScale(2, RoundingMode.HALF_UP).toString();
            String formattedBalance = balance.setScale(2, RoundingMode.HALF_UP).toString();
            monthDetailBean.setIncome(formattedIncome);
            monthDetailBean.setOutcome(formattedOutcome);
            monthDetailBean.setBalance(formattedBalance);
            homeDto.getMonthDetails().add(monthDetailBean);
        }
        return homeDto;
    }

    // 按年份获取每个月的 Flow 数据
    public Map<Integer, List<FlowJpaEntity>> getFlowsByYearGroupedByMonth(Integer year) {
        // 获取指定年份的所有Flow数据
        List<FlowJpaEntity> flows = flowRepository.findByYear(year);

        // 创建一个Map用于存储按月份分类的结果
        Map<Integer, List<FlowJpaEntity>> monthlyFlows = new HashMap<>();

        // 遍历所有Flow数据，按月份分类
        for (FlowJpaEntity flow : flows) {
            String monthStr = flow.getFDate().substring(5, 7); // 截取MM部分
            Integer month = Integer.valueOf(monthStr); // 将月份从字符串转换为整数
            monthlyFlows.computeIfAbsent(month, k -> new ArrayList<>()).add(flow);
        }

        return monthlyFlows;
    }

    public VersionDto getVersion() {
        return versionUtils.getVersion();
    }
}
