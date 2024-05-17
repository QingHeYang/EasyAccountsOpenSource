package com.deepblue.yd_jz.utils;

import lombok.Data;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.List;

@Data
public class ExcelBean {
    private String currentMonth;
    private String monthTotalIn;
    private String monthTotalOut;
    private String monthTotalEarn;
    private String allAsset;
    private List<Flow> flow;

    private List<Account> excelAccounts;

    private List<Analyze> analyzeList;

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

    @Data
    public static class Analyze{
        private String name;
        private boolean isRoot;
        private int id;
        private int parent;
        private BigDecimal money;
        private BigDecimal lastYearMoney;
        private BigDecimal lastMonthMoney;
        private BigDecimal yoyIncrease; // 仍然使用BigDecimal来存储增量，以保持精度
        private String yoyGrowthRate; // 存储为字符串，包括百分号
        private BigDecimal momIncrease; // 同上
        private String momGrowthRate; // 存储为字符串，包括百分号

        public void calculateMetrics() {
            BigDecimal currentMoney = (money != null) ? money : BigDecimal.ZERO;
            BigDecimal lastYear = (lastYearMoney != null) ? lastYearMoney : BigDecimal.ZERO;
            BigDecimal lastMonth = (lastMonthMoney != null) ? lastMonthMoney : BigDecimal.ZERO;

            // 计算同比增量
            yoyIncrease = currentMoney.subtract(lastYear);
            // 计算同比增速
            if (BigDecimal.ZERO.compareTo(lastYear) != 0) {
                BigDecimal yoyRate = yoyIncrease.divide(lastYear, 4, RoundingMode.HALF_UP).multiply(BigDecimal.valueOf(100));
                yoyGrowthRate = formatPercentage(yoyRate);
            } else {
                yoyGrowthRate = "0.00%"; // 基期为0时视为没有增长
            }

            // 计算环比增量
            momIncrease = currentMoney.subtract(lastMonth);
            // 计算环比增速
            if (BigDecimal.ZERO.compareTo(lastMonth) != 0) {
                BigDecimal momRate = momIncrease.divide(lastMonth, 4, RoundingMode.HALF_UP).multiply(BigDecimal.valueOf(100));
                momGrowthRate = formatPercentage(momRate);
            } else {
                momGrowthRate = "0.00%"; // 基期为0时视为没有增长
            }
        }

        // 辅助方法来格式化百分比
        private String formatPercentage(BigDecimal value) {
            return value.setScale(2, RoundingMode.HALF_UP) + "%";
        }


    }
}
