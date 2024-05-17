package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.controller.home.HomeBean;
import com.deepblue.yd_jz.dao.account.Account;
import com.deepblue.yd_jz.dao.account.AccountDao;
import com.deepblue.yd_jz.dao.action.ActionDao;
import com.deepblue.yd_jz.dao.flow.FlowDao;
import com.deepblue.yd_jz.dao.flow.FlowYear;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.text.NumberFormat;
import java.time.Year;
import java.util.ArrayList;
import java.util.List;

@Service
public class HomeService {
    @Autowired
    FlowDao flowDao;

    @Autowired
    AccountDao accountDao;

    @Autowired
    ActionDao actionDao;


    @Transactional(rollbackFor = Exception.class)
    public HomeBean getHomeBean() {
        List<Account> accounts = accountDao.queryAllAccount();
        BigDecimal totalAsset = new BigDecimal("0");
        BigDecimal exemptAsset = new BigDecimal("0");
        for (Account account : accounts) {
            BigDecimal accountAsset = new BigDecimal(account.getMoney());
            String exemptStr = account.getExemptMoney();
            if (exemptStr.equals("")){
                exemptStr = "0";
            }
            BigDecimal exemptAccountAsset = new BigDecimal(exemptStr);
            totalAsset = totalAsset.add(accountAsset);
            exemptAsset = exemptAsset.add(exemptAccountAsset);
        }
        HomeBean homeBean = new HomeBean();
        homeBean.setTotalAsset(totalAsset.toString());
        homeBean.setNetAsset(totalAsset.subtract(exemptAsset).toString());
        NumberFormat nf = NumberFormat.getPercentInstance();
        List<HomeBean.HomeAccountBean> homeAccounts = new ArrayList<>();
        for (Account account : accounts) {
            HomeBean.HomeAccountBean hab = new HomeBean.HomeAccountBean();
            hab.setId(account.getId());
            hab.setAccountName(account.getaName());
            hab.setAccountAsset(account.getMoney());
            hab.setExemptAsset(account.getExemptMoney());
            hab.setNote(account.getNote());
            BigDecimal accountAsset = new BigDecimal(account.getMoney());
            BigDecimal percent = accountAsset.divide(totalAsset, 3, RoundingMode.HALF_DOWN);
            nf.setMaximumFractionDigits(2);
            String percentStr = nf.format(percent.doubleValue());
            hab.setPercent(percentStr.substring(0,percentStr.length()-1));
            homeAccounts.add(hab);
        }
        homeBean.setAccounts(homeAccounts);
        int currentYear = Year.now().getValue();

        FlowYear flowYear = flowDao.getYearlySummary(currentYear);
        BigDecimal totalEarns = new BigDecimal(flowYear.getTotalEarns());
        BigDecimal totalCosts = new BigDecimal(flowYear.getTotalCosts());
        BigDecimal totalBalance = new BigDecimal(flowYear.getTotalBalance());
        String formattedTotalCosts = totalCosts.setScale(2, RoundingMode.HALF_UP).toString();
        String formattedTotalEarns = totalEarns.setScale(2, RoundingMode.HALF_UP).toString();
        String formattedTotalBalance = totalBalance.setScale(2, RoundingMode.HALF_UP).toString();

        homeBean.setYearOutCome(formattedTotalCosts);
        homeBean.setYearIncome(formattedTotalEarns);
        homeBean.setYearBalance(formattedTotalBalance);
        return homeBean;
    }
}
