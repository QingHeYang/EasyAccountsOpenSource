package com.deepblue.yd_jz.dto;

import lombok.Data;

// v2.7.0 (config-ui): 邮件配置回显（password 始终为空字符串脱敏）
@Data
public class MailConfigResponseDto {
    private String smtpServer;
    private String smtpPort;
    private String fromEmail;
    private String password;        // 永远 ""，前端据此判断是否已设置（非空=已设置）→ 改为：has_password 由前端用 isPasswordSet 字段判断
    private Boolean isPasswordSet;  // true=DB 中已有密文，false=未配置
    private String toList;
    private Boolean sendSqlBackup;
    private Boolean sendExcel;
}
