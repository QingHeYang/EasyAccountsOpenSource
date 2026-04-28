package com.deepblue.yd_jz.utils;

import com.deepblue.yd_jz.exception.BusinessException;
import com.deepblue.yd_jz.exception.ErrorCode;

import java.util.regex.Pattern;

// v2.7.0 (config-ui): 备份配置 → Spring cron 表达式
// 输入：frequency + time(HH:mm) + dayOfWeek(weekly) + dayOfMonth(monthly)
// 输出：6 字段 cron "秒 分 时 日 月 周"
public class CronBuilder {

    private static final Pattern HHMM = Pattern.compile("^([01]\\d|2[0-3]):[0-5]\\d$");
    private static final String[] DOW_TOKENS = {"MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"};

    private CronBuilder() {}

    /**
     * 拼 cron 表达式。
     *
     * @param frequency  daily / weekly / monthly
     * @param time       HH:mm
     * @param dayOfWeek  1-7（1=周一），仅 weekly 用
     * @param dayOfMonth 1-28（UI 限制 ≤28 避免 29/30/31 部分月份不执行），仅 monthly 用
     */
    public static String build(String frequency, String time, Integer dayOfWeek, Integer dayOfMonth) {
        if (frequency == null) {
            throw new BusinessException(ErrorCode.PARAM_INVALID, "备份频率不能为空");
        }
        if (time == null || !HHMM.matcher(time).matches()) {
            throw new BusinessException(ErrorCode.PARAM_FORMAT_ERROR, "备份时间格式错误，应为 HH:mm");
        }

        String[] hm = time.split(":");
        int hh = Integer.parseInt(hm[0]);
        int mm = Integer.parseInt(hm[1]);

        switch (frequency) {
            case SystemConfigConst.FREQ_DAILY:
                // 每天 HH:mm
                return String.format("0 %d %d * * ?", mm, hh);

            case SystemConfigConst.FREQ_WEEKLY:
                if (dayOfWeek == null || dayOfWeek < 1 || dayOfWeek > 7) {
                    throw new BusinessException(ErrorCode.PARAM_INVALID, "dayOfWeek 必须在 1-7 之间");
                }
                // weekly：使用 MON-SUN 而非数字，避免 Spring/Quartz 中 1=Sun 还是 Mon 的歧义
                return String.format("0 %d %d ? * %s", mm, hh, DOW_TOKENS[dayOfWeek - 1]);

            case SystemConfigConst.FREQ_MONTHLY:
                if (dayOfMonth == null || dayOfMonth < 1 || dayOfMonth > 28) {
                    throw new BusinessException(ErrorCode.PARAM_INVALID, "dayOfMonth 必须在 1-28 之间");
                }
                return String.format("0 %d %d %d * ?", mm, hh, dayOfMonth);

            default:
                throw new BusinessException(ErrorCode.PARAM_INVALID,
                        "frequency 仅支持 daily / weekly / monthly");
        }
    }
}
