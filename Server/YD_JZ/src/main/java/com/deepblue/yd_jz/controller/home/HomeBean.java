package com.deepblue.yd_jz.controller.home;

import lombok.Data;

import java.util.List;

@Data
public class HomeBean {
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


@Data
    public static class HomeAccountBean {
        private int id;
        private String accountName;
        private String accountAsset;
        private String exemptAsset;
        private String percent;
        private String note;

    }

  //  public static
}
