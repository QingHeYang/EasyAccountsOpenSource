package com.deepblue.yd_jz.utils;

// v2.7.0 (config-ui): 系统配置 UI 化相关常量（mail / backup / auth）
public class SystemConfigConst {

    // ── domain ─────────────────────────────
    public static final String DOMAIN_MAIL       = "mail";
    public static final String DOMAIN_BACKUP     = "backup";
    public static final String DOMAIN_AUTH       = "auth";
    public static final String DOMAIN_AUTO_EXCEL = "auto_excel";

    // ── mail ───────────────────────────────
    public static final String MAIL_SMTP_SERVER     = "smtp_server";
    public static final String MAIL_SMTP_PORT       = "smtp_port";
    public static final String MAIL_FROM_EMAIL      = "from_email";
    public static final String MAIL_PASSWORD        = "password";
    public static final String MAIL_TO_LIST         = "to_list";
    public static final String MAIL_SEND_SQL_BACKUP = "send_sql_backup";
    public static final String MAIL_SEND_EXCEL      = "send_excel";

    // ── backup ─────────────────────────────
    public static final String BACKUP_ENABLED      = "enabled";
    public static final String BACKUP_FREQUENCY    = "frequency";
    public static final String BACKUP_TIME         = "time";
    public static final String BACKUP_DAY_OF_WEEK  = "day_of_week";
    public static final String BACKUP_DAY_OF_MONTH = "day_of_month";

    // 备份频率枚举值
    public static final String FREQ_DAILY   = "daily";
    public static final String FREQ_WEEKLY  = "weekly";
    public static final String FREQ_MONTHLY = "monthly";

    // ── auth ───────────────────────────────
    public static final String AUTH_LOGIN_ENABLE          = "login_enable";
    public static final String AUTH_SINGLE_LOGIN          = "single_login";
    public static final String AUTH_TOKEN_EXPIRED_MINUTES = "token_expired_minutes";

    // ── 默认值（DB 行缺失时兜底，与 seed 一致） ───────
    public static final String MAIL_SMTP_PORT_DEFAULT       = "465";
    public static final String MAIL_SEND_SQL_BACKUP_DEFAULT = "true";
    public static final String MAIL_SEND_EXCEL_DEFAULT      = "true";

    public static final String BACKUP_ENABLED_DEFAULT      = "true";
    public static final String BACKUP_FREQUENCY_DEFAULT    = FREQ_DAILY;
    public static final String BACKUP_TIME_DEFAULT         = "22:00";
    public static final String BACKUP_DAY_OF_WEEK_DEFAULT  = "1";
    public static final String BACKUP_DAY_OF_MONTH_DEFAULT = "1";

    public static final String AUTH_LOGIN_ENABLE_DEFAULT          = "true";
    public static final String AUTH_SINGLE_LOGIN_DEFAULT          = "true";
    public static final String AUTH_TOKEN_EXPIRED_MINUTES_DEFAULT = "30";

    // ── auto_excel ─────────────────────────
    public static final String AUTO_EXCEL_ENABLED              = "enabled";
    public static final String AUTO_EXCEL_DAY_OF_MONTH         = "day_of_month";
    public static final String AUTO_EXCEL_TIME                 = "time";
    public static final String AUTO_EXCEL_TARGET               = "target";        // LAST_MONTH / CURRENT_MONTH
    public static final String AUTO_EXCEL_SEND_EMAIL           = "send_email";
    public static final String AUTO_EXCEL_REMIND_ENABLED       = "remind_enabled";
    public static final String AUTO_EXCEL_REMIND_BEFORE_DAYS   = "remind_before_days";
    public static final String AUTO_EXCEL_REMIND_EMAIL_ENABLED = "remind_email_enabled";
    public static final String AUTO_EXCEL_LAST_RUN_DATE        = "last_run_date";

    public static final String AUTO_EXCEL_TARGET_LAST_MONTH    = "LAST_MONTH";
    public static final String AUTO_EXCEL_TARGET_CURRENT_MONTH = "CURRENT_MONTH";

    public static final String AUTO_EXCEL_ENABLED_DEFAULT              = "false";
    public static final String AUTO_EXCEL_DAY_OF_MONTH_DEFAULT         = "4";
    public static final String AUTO_EXCEL_TIME_DEFAULT                 = "21:00";
    public static final String AUTO_EXCEL_TARGET_DEFAULT               = AUTO_EXCEL_TARGET_LAST_MONTH;
    public static final String AUTO_EXCEL_SEND_EMAIL_DEFAULT           = "true";
    public static final String AUTO_EXCEL_REMIND_ENABLED_DEFAULT       = "true";
    public static final String AUTO_EXCEL_REMIND_BEFORE_DAYS_DEFAULT   = "3";
    public static final String AUTO_EXCEL_REMIND_EMAIL_ENABLED_DEFAULT = "false";

    private SystemConfigConst() {}
}
