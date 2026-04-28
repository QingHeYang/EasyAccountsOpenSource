package com.deepblue.yd_jz.dto;

import lombok.Data;

// v2.7.0 (config-ui): 系统配置整体概览
// 给前端首页 / 系统状态页一次性拿到所有 domain 的当前状态
// 关键安全考量：
//   - mail：不返回 password（即使脱敏空串也不要），不返回 toList 明文（只 count）
//   - 各 domain 已有自己的 GET 接口拿详细配置；overview 只用于"概览"
@Data
public class SystemConfigOverviewDto {
    private MailOverview mail;
    private BackupOverview backup;
    private AuthOverview auth;
    private ScheduledFlowOverview scheduledFlow;
    private AutoExcelOverview autoExcel;

    @Data
    public static class MailOverview {
        private Boolean isConfigured;       // SMTP 必填项全填齐为 true
        private String smtpServer;
        private String fromEmail;
        private Integer toListCount;        // 收件人数量（不暴露邮箱本身）
        private Boolean sendSqlBackup;
        private Boolean sendExcel;
    }

    @Data
    public static class BackupOverview {
        private Boolean enabled;
        private String frequency;            // daily / weekly / monthly
        private String time;                 // HH:mm
        private Integer dayOfWeek;           // 仅 weekly 用
        private Integer dayOfMonth;          // 仅 monthly 用
        private String cron;                 // 拼好的 cron 表达式
        private String humanReadable;        // "每天 22:00" / "每周一 06:30" / "每月 4 日 21:00"
    }

    @Data
    public static class AuthOverview {
        private Boolean loginEnable;
        private Boolean singleLogin;
        private Integer tokenExpiredMinutes;
    }

    @Data
    public static class ScheduledFlowOverview {
        private Integer remindBeforeDays;
        private String remindTime;
    }

    @Data
    public static class AutoExcelOverview {
        private Boolean enabled;
        private Integer dayOfMonth;
        private String time;
        private String target;                 // LAST_MONTH / CURRENT_MONTH
        private Boolean sendEmail;
        private Boolean remindEnabled;
        private Integer remindBeforeDays;
        private Boolean remindEmailEnabled;
        private String lastRunDate;            // 仅展示
        private String nextRunDate;            // 计算字段
        private String targetYearMonth;        // 计算字段：下次将生成的 yyyy-MM
        private String humanReadable;          // "每月 4 日 21:00（生成上月）"
    }
}
