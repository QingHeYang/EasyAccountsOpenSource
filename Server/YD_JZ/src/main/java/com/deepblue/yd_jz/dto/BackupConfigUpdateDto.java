package com.deepblue.yd_jz.dto;

import lombok.Data;

// v2.7.0 (config-ui): 备份配置更新请求；null=不修改
@Data
public class BackupConfigUpdateDto {
    private Boolean enabled;        // 是否启用自动备份
    private String frequency;       // daily / weekly / monthly
    private String time;            // HH:mm
    private Integer dayOfWeek;      // 1-7（1=周一），仅 weekly 用
    private Integer dayOfMonth;     // 1-28，仅 monthly 用
}
