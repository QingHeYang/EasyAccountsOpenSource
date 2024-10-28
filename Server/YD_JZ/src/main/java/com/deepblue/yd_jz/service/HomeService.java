package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.dto.HomeDto;
import com.deepblue.yd_jz.entity.Account;
import com.deepblue.yd_jz.dao.jpa.AccountRepository;
import com.deepblue.yd_jz.dao.mybatis.FlowDao;
import com.deepblue.yd_jz.entity.FlowYear;
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
    AccountRepository accountDao;

    @Autowired
    ActionService actionDao;


    @Transactional(rollbackFor = Exception.class)
    public HomeDto getHomeBean() {
        List<Account> accounts = accountDao.findByDisableFalse();
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
        HomeDto homeDto = new HomeDto();
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
            hab.setPercent(percentStr.substring(0,percentStr.length()-1));
            homeAccounts.add(hab);
        }
        homeDto.setAccounts(homeAccounts);
        int currentYear = Year.now().getValue();

        FlowYear flowYear = flowDao.getYearlySummary(currentYear);
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
}
