package com.deepblue.yd_jz.data;

import lombok.Data;

import java.util.List;

@Data
public class MonthExcelData {
    private String currentMonth;
    private String monthTotalIn;
    private String monthTotalOut;
    private String monthTotalEarn;
    private String allAsset;
    private List<Flow> flow;

    private List<Account> excelAccounts;


    @Data
    public static class Account {
        private String accountName;
        private String accountMoney;
    }

    @Data
    public static class Flow {
        private String flowDate;
        private String actionName;
        private String typeName;
        private String accountName;
        private String money;
        private String note;
    }


}
