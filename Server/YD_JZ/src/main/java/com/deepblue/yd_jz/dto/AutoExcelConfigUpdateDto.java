package com.deepblue.yd_jz.dto;

import lombok.Data;

// v2.7.0 (config-ui + auto-excel): 自动月度 Excel 配置更新；null=不修改
@Data
public class AutoExcelConfigUpdateDto {
    private Boolean enabled;
    private Integer dayOfMonth;            // 1-28
    private String  time;                  // HH:mm
    private String  target;                // LAST_MONTH / CURRENT_MONTH
    private Boolean sendEmail;             // 生成成功后是否邮件发送
    private Boolean remindEnabled;         // 是否提前提醒
    private Integer remindBeforeDays;      // 提前 N 天
    private Boolean remindEmailEnabled;    // 提醒是否邮件（与站内通知独立）
}
