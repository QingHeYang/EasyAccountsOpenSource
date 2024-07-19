package com.deepblue.yd_jz.controller.analysis;

import lombok.Data;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;

@Data
public class AnalysisExcelBean {
    private String currentCircle;
    private String yoyCircle;
    private String momCircle;

    private List<Analyze> analyzeList;

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

        public void caculateComparison() {
            calculateYoyComparison();
            calculateMomComparison();
        }

        public void calculateYoyComparison() {
            if (money == null || lastYearMoney == null) {
                yoyIncrease = null;
                yoyGrowthRate = null;
            } else {
                yoyIncrease = money.subtract(lastYearMoney);
                if (money.compareTo(BigDecimal.ZERO) == 0||lastYearMoney.compareTo(BigDecimal.ZERO) == 0){
                    yoyGrowthRate = "";
                } else {
                    BigDecimal rate = yoyIncrease.divide(lastYearMoney, 4, BigDecimal.ROUND_HALF_UP)
                            .multiply(BigDecimal.valueOf(100)).setScale(2, BigDecimal.ROUND_HALF_UP);
                    yoyGrowthRate = rate.toString() + "%";
                }
            }
        }

        public void calculateMomComparison() {
            if (money == null || lastMonthMoney == null) {
                momIncrease = null;
                momGrowthRate = null;
            } else {
                momIncrease = money.subtract(lastMonthMoney);
                if (money.compareTo(BigDecimal.ZERO) == 0||lastMonthMoney.compareTo(BigDecimal.ZERO) == 0){
                    momGrowthRate = "";
                } else {
                    BigDecimal rate = momIncrease.divide(lastMonthMoney, 4, BigDecimal.ROUND_HALF_UP)
                            .multiply(BigDecimal.valueOf(100)).setScale(2, BigDecimal.ROUND_HALF_UP);
                    momGrowthRate = rate.toString() + "%";
                }
            }
        }
    }
}
