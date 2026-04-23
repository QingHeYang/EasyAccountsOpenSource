package com.deepblue.yd_jz.utils;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import lombok.extern.slf4j.Slf4j;

import java.lang.reflect.Type;
import java.time.LocalDate;
import java.time.YearMonth;
import java.util.*;

// v2.7.0: 定时记账周期计算器
// 纯函数工具类，无 Spring 依赖，所有比较一律 LocalDate 整体比，不拆字段
@Slf4j
public class CycleCalculator {

    private static final Gson GSON = new Gson();
    private static final Type INT_LIST_TYPE = new TypeToken<List<Integer>>(){}.getType();
    private static final Type STR_LIST_TYPE = new TypeToken<List<String>>(){}.getType();

    // =====================================================================
    // 入口 1：算下一个执行日（严格大于 from 的最近一天）
    // cycleDatesJson 来自 scheduled_flow_rule.cycle_dates 字段原样
    // =====================================================================
    public static LocalDate nextRunDate(int cycleType, String cycleDatesJson, LocalDate from) {
        switch (cycleType) {
            case ScheduledFlowConst.CYCLE_DAILY:
                return nextDaily(from);
            case ScheduledFlowConst.CYCLE_WEEKLY:
                return nextWeekly(parseIntList(cycleDatesJson), from);
            case ScheduledFlowConst.CYCLE_MONTHLY:
                return nextMonthly(parseIntList(cycleDatesJson), from);
            case ScheduledFlowConst.CYCLE_YEARLY:
                return nextYearly(parseStrList(cycleDatesJson), from);
            default:
                throw new IllegalArgumentException("unknown cycleType: " + cycleType);
        }
    }

    // =====================================================================
    // 入口 2：预览下一轮执行日（每月=下个月 / 每年=下一年 / 每日/每周=空列表）
    // anchor 一般传 today
    // =====================================================================
    public static List<LocalDate> previewNextCycle(int cycleType, String cycleDatesJson, LocalDate anchor) {
        switch (cycleType) {
            case ScheduledFlowConst.CYCLE_DAILY:
            case ScheduledFlowConst.CYCLE_WEEKLY:
                return Collections.emptyList();
            case ScheduledFlowConst.CYCLE_MONTHLY:
                return previewMonthly(parseIntList(cycleDatesJson), anchor);
            case ScheduledFlowConst.CYCLE_YEARLY:
                return previewYearly(parseStrList(cycleDatesJson), anchor);
            default:
                throw new IllegalArgumentException("unknown cycleType: " + cycleType);
        }
    }

    // =====================================================================
    // 每日：下一个执行日就是 from+1
    // =====================================================================
    private static LocalDate nextDaily(LocalDate from) {
        return from.plusDays(1);
    }

    // =====================================================================
    // 每周：cycleDates = [1-7]（ISO：1=周一 7=周日）
    // 从 from+1 起逐天扫，至多 7 天内必命中
    // =====================================================================
    private static LocalDate nextWeekly(List<Integer> weekdays, LocalDate from) {
        requireNonEmpty(weekdays);
        Set<Integer> set = new HashSet<>(weekdays);
        for (int i = 1; i <= 7; i++) {
            LocalDate c = from.plusDays(i);
            if (set.contains(c.getDayOfWeek().getValue())) {
                return c;
            }
        }
        // 正常走不到这里
        throw new IllegalStateException("weekly calc failed: dates=" + weekdays + ", from=" + from);
    }

    // =====================================================================
    // 每月：cycleDates = [1-31]（每月几号）
    // 从 from 所在月开始，生成本月完整 LocalDate 候选（月末回退），找严格 > from 的最小
    // 本月没有就翻下月重新生成
    // =====================================================================
    private static LocalDate nextMonthly(List<Integer> days, LocalDate from) {
        requireNonEmpty(days);
        YearMonth cursor = YearMonth.from(from);
        // 最多尝试 2 次循环足以跳过月末回退场景（本月没有→下月必有）
        for (int loop = 0; loop < 12; loop++) {
            List<LocalDate> candidates = buildMonthlyCandidates(cursor, days);
            for (LocalDate c : candidates) {
                if (c.isAfter(from)) {
                    return c;
                }
            }
            cursor = cursor.plusMonths(1);
        }
        throw new IllegalStateException("monthly calc failed: dates=" + days + ", from=" + from);
    }

    // =====================================================================
    // 每年：cycleDates = ["MM-DD"]
    // 从 from 所在年开始，生成本年候选（遇 2-30 等无效日期回退到当月末），找 > from 最小
    // =====================================================================
    private static LocalDate nextYearly(List<String> mmdds, LocalDate from) {
        requireNonEmpty(mmdds);
        int year = from.getYear();
        for (int loop = 0; loop < 10; loop++) {
            List<LocalDate> candidates = buildYearlyCandidates(year, mmdds);
            for (LocalDate c : candidates) {
                if (c.isAfter(from)) {
                    return c;
                }
            }
            year++;
        }
        throw new IllegalStateException("yearly calc failed: dates=" + mmdds + ", from=" + from);
    }

    // =====================================================================
    // 预览：每月下个月全部执行日
    // =====================================================================
    private static List<LocalDate> previewMonthly(List<Integer> days, LocalDate anchor) {
        requireNonEmpty(days);
        YearMonth next = YearMonth.from(anchor).plusMonths(1);
        return buildMonthlyCandidates(next, days);
    }

    // =====================================================================
    // 预览:每年下一年全部执行日
    // =====================================================================
    private static List<LocalDate> previewYearly(List<String> mmdds, LocalDate anchor) {
        requireNonEmpty(mmdds);
        return buildYearlyCandidates(anchor.getYear() + 1, mmdds);
    }

    // =====================================================================
    // 辅助：为指定 YearMonth 按号数列表构造完整 LocalDate（月末回退），已排序
    // =====================================================================
    private static List<LocalDate> buildMonthlyCandidates(YearMonth ym, List<Integer> days) {
        int maxDay = ym.lengthOfMonth();
        Set<LocalDate> set = new TreeSet<>();
        for (Integer d : days) {
            if (d == null || d < 1 || d > 31) continue;
            set.add(ym.atDay(Math.min(d, maxDay)));  // 31 号遇 2 月/小月 → 回退月末
        }
        return new ArrayList<>(set);
    }

    // =====================================================================
    // 辅助：为指定年份按 "MM-DD" 列表构造完整 LocalDate（月末回退），已排序
    // =====================================================================
    private static List<LocalDate> buildYearlyCandidates(int year, List<String> mmdds) {
        Set<LocalDate> set = new TreeSet<>();
        for (String mmdd : mmdds) {
            if (mmdd == null || mmdd.isEmpty()) continue;
            String[] parts = mmdd.split("-");
            if (parts.length != 2) {
                log.warn("invalid MM-DD format: {}", mmdd);
                continue;
            }
            try {
                int m = Integer.parseInt(parts[0].trim());
                int d = Integer.parseInt(parts[1].trim());
                if (m < 1 || m > 12 || d < 1 || d > 31) continue;
                YearMonth ym = YearMonth.of(year, m);
                set.add(ym.atDay(Math.min(d, ym.lengthOfMonth())));  // 2-30 → 2月末
            } catch (NumberFormatException e) {
                log.warn("unparsable MM-DD: {}", mmdd);
            }
        }
        return new ArrayList<>(set);
    }

    // =====================================================================
    // JSON 解析
    // =====================================================================
    private static List<Integer> parseIntList(String json) {
        if (json == null || json.isEmpty()) return Collections.emptyList();
        return GSON.fromJson(json, INT_LIST_TYPE);
    }

    private static List<String> parseStrList(String json) {
        if (json == null || json.isEmpty()) return Collections.emptyList();
        return GSON.fromJson(json, STR_LIST_TYPE);
    }

    private static void requireNonEmpty(List<?> list) {
        if (list == null || list.isEmpty()) {
            throw new IllegalArgumentException("cycleDates must not be empty");
        }
    }
}
