package com.deepblue.yd_jz.dto;

import lombok.Data;

// v2.7.0 (config-ui): 备份配置回显
@Data
public class BackupConfigResponseDto {
    private Boolean enabled;
    private String frequency;
    private String time;
    private Integer dayOfWeek;
    private Integer dayOfMonth;
    private String cron;            // 由 5 字段拼出，前端展示 / 调试用
}
