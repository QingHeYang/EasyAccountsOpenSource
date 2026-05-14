package com.deepblue.yd_jz.utils;

import org.springframework.stereotype.Component;

import java.time.DateTimeException;
import java.time.LocalDate;
import java.time.YearMonth;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;

@Component
public class DateUtils {

    /**
     * 根据给定的日期字符串，返回 yyyy-MM-dd 格式。
     *
     * v2.7.0 起放开月级精度，支持前端按"具体日期"做分析（如某一天的饼图）：
     * - 入参 "yyyy-MM-dd"（三段，如 "2026-05-14"）：直接解析为该日期，isStartOfMonth 参数被忽略
     * - 入参 "yyyy-MM" / "yyyy-M"（两段）：保留旧逻辑，按 isStartOfMonth 取月初或月末
     *   月末特殊：若是当前月，则返回今天
     *
     * @param yearMonthOrDate 年月字符串或具体日期字符串
     * @param isStartOfMonth 仅对两段 yyyy-MM 输入生效；三段 yyyy-MM-dd 忽略
     * @return "yyyy-MM-dd" 格式的日期字符串
     */
    public  String buildFullDate(String yearMonthOrDate, boolean isStartOfMonth) {
        if (yearMonthOrDate == null) {
            throw new IllegalArgumentException("日期不能为空");
        }
        String input = yearMonthOrDate.trim();
        String[] parts = input.split("-");

        // 三段：yyyy-MM-dd 或 yyyy-M-d，直接按用户给定的日期返回
        if (parts.length == 3) {
            try {
                int y = Integer.parseInt(parts[0].trim());
                int m = Integer.parseInt(parts[1].trim());
                int d = Integer.parseInt(parts[2].trim());
                return LocalDate.of(y, m, d).format(DateTimeFormatter.ISO_LOCAL_DATE);
            } catch (NumberFormatException | DateTimeException e) {
                throw new IllegalArgumentException("无效的日期格式: " + input + "，应为 yyyy-MM-dd", e);
            }
        }

        // 两段：yyyy-MM / yyyy-M，按月初或月末逻辑
        if (parts.length != 2) {
            throw new IllegalArgumentException(
                    "无效的日期格式: " + input + "，应为 yyyy-MM 或 yyyy-MM-dd");
        }

        String yearStr = parts[0].trim();
        String monthStr = parts[1].trim();

        // 2. 如果 monthStr 长度只有1位，加一个前缀 "0"（如 "1" -> "01"）
        if (monthStr.length() == 1) {
            monthStr = "0" + monthStr;
        }

        // 3. 转为 int
        int year;
        int month;
        try {
            year = Integer.parseInt(yearStr);
            month = Integer.parseInt(monthStr);
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("无法解析年份或月份为整数: " + input, e);
        }

        // 4. 根据 year 和 month 构建 YearMonth 对象
        YearMonth ym;
        try {
            ym = YearMonth.of(year, month);
        } catch (DateTimeException e) {
            throw new IllegalArgumentException("无效的年份或月份: " + input, e);
        }

        // 5. 区分月初还是月末
        if (isStartOfMonth) {
            // 月初固定为 1 号
            LocalDate firstDay = ym.atDay(1);
            return firstDay.format(DateTimeFormatter.ISO_LOCAL_DATE);
        } else {
            // 月末
            // 先判断是否是当前系统时间所在的年-月
            LocalDate now = LocalDate.now();
            YearMonth currentYm = YearMonth.of(now.getYear(), now.getMonth());

            if (ym.equals(currentYm)) {
                // 如果传入的年月 == 当前年月，则返回当前系统日期
                return now.format(DateTimeFormatter.ISO_LOCAL_DATE);
            } else {
                // 否则返回该月最后一天
                LocalDate lastDay = ym.atEndOfMonth();
                return lastDay.format(DateTimeFormatter.ISO_LOCAL_DATE);
            }
        }
    }

}
