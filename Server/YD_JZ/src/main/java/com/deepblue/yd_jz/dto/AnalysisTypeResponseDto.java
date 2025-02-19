package com.deepblue.yd_jz.dto;

import lombok.Data;

import java.util.List;

@Data
public class AnalysisTypeResponseDto {
    private int typeId;
    private String typeName;
    private String totalIncome;
    private String totalOutcome;
    private List<YearData> yearData;

    @Data
    public static class YearData{
        private int year;
        private String income;
        private String outcome;
        private List<MonthData> monthData;
    }

    @Data
    public static class MonthData{
        private int month;
        private String income;
        private String outcome;
    }
}
