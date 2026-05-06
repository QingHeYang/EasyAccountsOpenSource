package com.deepblue.yd_jz.dto;

import lombok.Data;

// v2.7.0: 定时记账全局提醒配置
@Data
public class ReminderConfigDto {
    private Integer remindBeforeDays;  // 1~5
    private String remindTime;          // HH:mm
}
