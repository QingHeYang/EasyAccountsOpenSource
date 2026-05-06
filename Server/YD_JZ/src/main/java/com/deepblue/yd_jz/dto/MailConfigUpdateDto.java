package com.deepblue.yd_jz.dto;

import lombok.Data;

// v2.7.0 (config-ui): 邮件配置更新请求
// 字段语义：null=不修改；非 null=覆盖（password 空字符串=清空）
@Data
public class MailConfigUpdateDto {
    private String smtpServer;
    private String smtpPort;
    private String fromEmail;
    private String password;        // 明文进；Service 内 AES 加密入库
    private String toList;          // 多收件人逗号分隔
    private Boolean sendSqlBackup;
    private Boolean sendExcel;
}
