package com.deepblue.yd_jz.dto;

import lombok.Data;

import java.util.List;

@Data
public class HomeDto {

    private String totalAsset;
    private String netAsset;
    private String curIncome;
    private String curOutCome;
    //年度收入
    private String yearIncome;
    //年度支出
    private String yearOutCome;
    //年度结余
    private String yearBalance;
    private List<HomeAccountBean> accounts;
    private List<HomeMonthDetailBean> monthDetails;

    @Data
    public static class HomeAccountBean {
        private int id;
        private String accountName;
        private String accountAsset;
        private String exemptAsset;
        private String percent;
        private String note;
    }

    @Data
    public static class HomeMonthDetailBean {
        private String month;
        private String income;
        private String outcome;
        private String balance;
    }
}
