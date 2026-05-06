package com.deepblue.yd_jz.dto;

import lombok.Data;

// v2.7.0 (config-ui + auto-excel): 自动月度 Excel 配置回显
@Data
public class AutoExcelConfigResponseDto {
    private Boolean enabled;
    private Integer dayOfMonth;
    private String  time;
    private String  target;
    private Boolean sendEmail;
    private Boolean remindEnabled;
    private Integer remindBeforeDays;
    private Boolean remindEmailEnabled;

    // 状态字段（只读，由系统维护）
    private String lastRunDate;            // YYYY-MM-DD，空表示从未运行
    private String nextRunDate;            // 计算字段：下次执行日 YYYY-MM-DD
    private String targetYearMonth;        // 计算字段：下次将生成哪个月，YYYY-MM
}
