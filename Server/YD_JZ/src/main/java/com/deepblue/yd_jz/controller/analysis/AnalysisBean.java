package com.deepblue.yd_jz.controller.analysis;

import lombok.Data;

import java.math.BigDecimal;
import java.util.List;

@Data
public class AnalysisBean {
    private String currentCircle;
    private String yoyCircle;
    private String momCircle;
    private List<SingleTypeBean> yoyList;
    private List<SingleTypeBean> momList;

    @Data
    public static  class SingleTypeBean{
        private String name;
        private boolean isRoot;
        private int id;
        private int parent;
        private BigDecimal money;
        private BigDecimal compareMoney;
        private BigDecimal compareIncrease;
        private String compareRate;

        public void calculateComparison() {
            if (money == null || compareMoney == null) {
                compareIncrease = null;
                compareRate = null;
            } else {
                compareIncrease = money.subtract(compareMoney);
                if (compareMoney.compareTo(BigDecimal.ZERO) == 0||money.compareTo(BigDecimal.ZERO) == 0){
                    compareRate = "";
                } else {
                    BigDecimal rate = compareIncrease.divide(compareMoney, 4, BigDecimal.ROUND_HALF_UP)
                            .multiply(BigDecimal.valueOf(100)).setScale(2, BigDecimal.ROUND_HALF_UP);
                    compareRate = rate.toString() + "%";
                }
            }
        }
    }
}
