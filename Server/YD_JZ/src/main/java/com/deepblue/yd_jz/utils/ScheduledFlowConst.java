package com.deepblue.yd_jz.utils;

// v2.7.0: 定时记账相关常量
public class ScheduledFlowConst {

    // ── 周期类型 ─────────────────────────────
    public static final int CYCLE_DAILY   = 1;  // 每日
    public static final int CYCLE_WEEKLY  = 2;  // 每周，cycle_dates = [1-7]（ISO 1=周一 7=周日）
    public static final int CYCLE_MONTHLY = 3;  // 每月，cycle_dates = [1-31]
    public static final int CYCLE_YEARLY  = 4;  // 每年，cycle_dates = ["MM-DD"]

    // ── 规则状态 ─────────────────────────────
    public static final int STATUS_NOT_START = 1;  // 未开始
    public static final int STATUS_RUNNING   = 2;  // 开始
    public static final int STATUS_PAUSED    = 3;  // 暂停
    public static final int STATUS_COMPLETED = 4;  // 完成
    public static final int STATUS_INVALID   = 5;  // 失效

    // ── 执行日志失败分类 ──────────────────────
    public static final int FAIL_MASTER_DATA = 1;  // 主数据类（账户停用/分类停用/归档）
    public static final int FAIL_OTHER       = 2;  // 其他类（余额不足/代码异常等）

    // ── 通知类型 ─────────────────────────────
    public static final int NOTICE_TYPE_PRE_REMIND          = 1;  // 定时记账事前提醒
    // v2.7.0 (auto-excel): 自动月度 Excel 相关通知
    public static final int NOTICE_TYPE_AUTO_EXCEL_REMIND    = 2;  // 自动月度 Excel 提前提醒
    public static final int NOTICE_TYPE_AUTO_EXCEL_GENERATED = 3;  // 自动月度 Excel 已生成
    public static final int NOTICE_TYPE_AUTO_EXCEL_NO_FLOW   = 4;  // 当月无流水，已跳过
    public static final int NOTICE_TYPE_AUTO_EXCEL_FAILED    = 5;  // 自动生成失败

    // ── Flow.from 枚举值 ────────────────────
    public static final String FLOW_FROM_SCHEDULED = "scheduled";
    // note 尾部拼接的定时标记，与外部来源（如 Claw "#Claw记账"）的格式风格一致
    public static final String NOTE_TAG_SCHEDULED  = " #定时";

    // ── app_config 配置 ─────────────────────
    public static final String CONFIG_DOMAIN_SCHEDULED_FLOW = "scheduled_flow";
    public static final String CONFIG_KEY_REMIND_BEFORE_DAYS = "remind_before_days";
    public static final String CONFIG_KEY_REMIND_TIME        = "remind_time";
}
