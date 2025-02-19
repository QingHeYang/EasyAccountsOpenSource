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
     * 根据给定的年-月字符串，返回指定的完整日期。
     *
     * @param yearMonth      年月字符串（可能是 "2024-1" 或 "2024-01" 等）
     * @param isStartOfMonth true 表示获取该月第一天，false 表示获取该月末尾日期
     * @return "yyyy-MM-dd" 格式的日期字符串
     */
    public  String buildFullDate(String yearMonth, boolean isStartOfMonth) {
        // 1. 解析 year 和 month
        //    yearMonth 可能是 "2024-1" 或 "2024-01"
        //    先 split，得到 [year, month]
        String[] parts = yearMonth.split("-");
        if (parts.length != 2) {
            throw new IllegalArgumentException("无效的年月格式: " + yearMonth + "，正确格式应为 yyyy-MM 或 yyyy-M");
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
            throw new IllegalArgumentException("无法解析年份或月份为整数: " + yearMonth, e);
        }

        // 4. 根据 year 和 month 构建 YearMonth 对象
        YearMonth ym;
        try {
            ym = YearMonth.of(year, month);
        } catch (DateTimeException e) {
            throw new IllegalArgumentException("无效的年份或月份: " + yearMonth, e);
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
