package com.deepblue.yd_jz.utils;

import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

// v2.7.0: CycleCalculator 单测，覆盖月末/闰年/跨月跨年边界
class CycleCalculatorTest {

    // ─────────────────────────────────────────
    // 每日
    // ─────────────────────────────────────────
    @Test
    void daily_nextIsTomorrow() {
        LocalDate from = LocalDate.of(2026, 4, 23);
        LocalDate next = CycleCalculator.nextRunDate(
                ScheduledFlowConst.CYCLE_DAILY, null, from);
        assertEquals(LocalDate.of(2026, 4, 24), next);
    }

    @Test
    void daily_acrossMonth() {
        LocalDate next = CycleCalculator.nextRunDate(
                ScheduledFlowConst.CYCLE_DAILY, null, LocalDate.of(2026, 4, 30));
        assertEquals(LocalDate.of(2026, 5, 1), next);
    }

    // ─────────────────────────────────────────
    // 每周
    // ─────────────────────────────────────────
    @Test
    void weekly_singleDay() {
        // 每周一；2026-4-23 是周四（ISO 4），下个周一 = 2026-4-27
        LocalDate from = LocalDate.of(2026, 4, 23);
        LocalDate next = CycleCalculator.nextRunDate(
                ScheduledFlowConst.CYCLE_WEEKLY, "[1]", from);
        assertEquals(LocalDate.of(2026, 4, 27), next);
    }

    @Test
    void weekly_multiDays_picksNearest() {
        // 每周一、四；2026-4-23 是周四（ISO 4）。严格大于 → 下一个周一 4/27
        LocalDate from = LocalDate.of(2026, 4, 23);
        LocalDate next = CycleCalculator.nextRunDate(
                ScheduledFlowConst.CYCLE_WEEKLY, "[1,4]", from);
        assertEquals(LocalDate.of(2026, 4, 27), next);
    }

    @Test
    void weekly_acrossYear() {
        // 2026-12-31 是周四（ISO 4），每周二 → 2027-1-5
        LocalDate from = LocalDate.of(2026, 12, 31);
        LocalDate next = CycleCalculator.nextRunDate(
                ScheduledFlowConst.CYCLE_WEEKLY, "[2]", from);
        assertEquals(LocalDate.of(2027, 1, 5), next);
    }

    // ─────────────────────────────────────────
    // 每月
    // ─────────────────────────────────────────
    @Test
    void monthly_sameMonth() {
        // 每月 5/20，from=5/1 → 5/5
        LocalDate next = CycleCalculator.nextRunDate(
                ScheduledFlowConst.CYCLE_MONTHLY, "[5,20]", LocalDate.of(2026, 5, 1));
        assertEquals(LocalDate.of(2026, 5, 5), next);
    }

    @Test
    void monthly_monthEndCrossesToNext() {
        // 用户核心关注：from=5/30，每月 5/20 → 严格大于 → 6/5
        LocalDate next = CycleCalculator.nextRunDate(
                ScheduledFlowConst.CYCLE_MONTHLY, "[5,20]", LocalDate.of(2026, 5, 30));
        assertEquals(LocalDate.of(2026, 6, 5), next);
    }

    @Test
    void monthly_day31_fallbackToMonthEnd_feb() {
        // 每月 31 号，from=1/31 → 2/28（平年）
        LocalDate next = CycleCalculator.nextRunDate(
                ScheduledFlowConst.CYCLE_MONTHLY, "[31]", LocalDate.of(2026, 1, 31));
        assertEquals(LocalDate.of(2026, 2, 28), next);
    }

    @Test
    void monthly_day31_fallbackToMonthEnd_leapFeb() {
        // 闰年 2028，每月 31 号，from=1/31 → 2/29
        LocalDate next = CycleCalculator.nextRunDate(
                ScheduledFlowConst.CYCLE_MONTHLY, "[31]", LocalDate.of(2028, 1, 31));
        assertEquals(LocalDate.of(2028, 2, 29), next);
    }

    @Test
    void monthly_day31_fallbackToMonthEnd_april() {
        // 每月 31 号，from=3/31 → 4/30
        LocalDate next = CycleCalculator.nextRunDate(
                ScheduledFlowConst.CYCLE_MONTHLY, "[31]", LocalDate.of(2026, 3, 31));
        assertEquals(LocalDate.of(2026, 4, 30), next);
    }

    @Test
    void monthly_multipleDays_withMonthEnd() {
        // 每月 1/15/31；from=5/15 → 5/31（本月 31 有效，大于 15）
        LocalDate next = CycleCalculator.nextRunDate(
                ScheduledFlowConst.CYCLE_MONTHLY, "[1,15,31]", LocalDate.of(2026, 5, 15));
        assertEquals(LocalDate.of(2026, 5, 31), next);
    }

    @Test
    void monthly_acrossYear() {
        // 每月 15 号；from=12/20 → 次年 1/15
        LocalDate next = CycleCalculator.nextRunDate(
                ScheduledFlowConst.CYCLE_MONTHLY, "[15]", LocalDate.of(2026, 12, 20));
        assertEquals(LocalDate.of(2027, 1, 15), next);
    }

    // ─────────────────────────────────────────
    // 每年
    // ─────────────────────────────────────────
    @Test
    void yearly_normal() {
        // 每年 3-1、10-1；from=2026-4-23 → 2026-10-1
        LocalDate next = CycleCalculator.nextRunDate(
                ScheduledFlowConst.CYCLE_YEARLY,
                "[\"03-01\",\"10-01\"]",
                LocalDate.of(2026, 4, 23));
        assertEquals(LocalDate.of(2026, 10, 1), next);
    }

    @Test
    void yearly_acrossYear() {
        // 每年 3-1；from=2026-6-1 → 2027-3-1
        LocalDate next = CycleCalculator.nextRunDate(
                ScheduledFlowConst.CYCLE_YEARLY,
                "[\"03-01\"]",
                LocalDate.of(2026, 6, 1));
        assertEquals(LocalDate.of(2027, 3, 1), next);
    }

    @Test
    void yearly_feb29_fallbackInNonLeap() {
        // 每年 2-29；from=2026-1-1（2026 非闰年） → 2026-2-28
        LocalDate next = CycleCalculator.nextRunDate(
                ScheduledFlowConst.CYCLE_YEARLY,
                "[\"02-29\"]",
                LocalDate.of(2026, 1, 1));
        assertEquals(LocalDate.of(2026, 2, 28), next);
    }

    @Test
    void yearly_feb30_fallbackToFebEnd() {
        // 每年 2-30（无效日期）；2028 闰年 → 2-29，平年 → 2-28
        LocalDate nextLeap = CycleCalculator.nextRunDate(
                ScheduledFlowConst.CYCLE_YEARLY,
                "[\"02-30\"]",
                LocalDate.of(2028, 1, 1));
        assertEquals(LocalDate.of(2028, 2, 29), nextLeap);

        LocalDate nextNormal = CycleCalculator.nextRunDate(
                ScheduledFlowConst.CYCLE_YEARLY,
                "[\"02-30\"]",
                LocalDate.of(2026, 1, 1));
        assertEquals(LocalDate.of(2026, 2, 28), nextNormal);
    }

    @Test
    void yearly_apr31_fallbackTo30() {
        // 每年 4-31（无效）→ 4-30
        LocalDate next = CycleCalculator.nextRunDate(
                ScheduledFlowConst.CYCLE_YEARLY,
                "[\"04-31\"]",
                LocalDate.of(2026, 1, 1));
        assertEquals(LocalDate.of(2026, 4, 30), next);
    }

    // ─────────────────────────────────────────
    // 预览
    // ─────────────────────────────────────────
    @Test
    void preview_monthly_returnsNextMonthAllDates() {
        // 每月 5/31；anchor=5/15 → 下月 = 6 月 → [6/5, 6/30]（31 回退 30）
        List<LocalDate> preview = CycleCalculator.previewNextCycle(
                ScheduledFlowConst.CYCLE_MONTHLY, "[5,31]", LocalDate.of(2026, 5, 15));
        assertEquals(List.of(LocalDate.of(2026, 6, 5), LocalDate.of(2026, 6, 30)), preview);
    }

    @Test
    void preview_yearly_returnsNextYearAllDates() {
        // 每年 3-1、10-1；anchor=2026 → 2027-3-1 / 2027-10-1
        List<LocalDate> preview = CycleCalculator.previewNextCycle(
                ScheduledFlowConst.CYCLE_YEARLY,
                "[\"03-01\",\"10-01\"]",
                LocalDate.of(2026, 7, 1));
        assertEquals(List.of(LocalDate.of(2027, 3, 1), LocalDate.of(2027, 10, 1)), preview);
    }

    @Test
    void preview_daily_empty() {
        assertTrue(CycleCalculator.previewNextCycle(
                ScheduledFlowConst.CYCLE_DAILY, null, LocalDate.of(2026, 4, 23)).isEmpty());
    }

    @Test
    void preview_weekly_empty() {
        assertTrue(CycleCalculator.previewNextCycle(
                ScheduledFlowConst.CYCLE_WEEKLY, "[1,4]", LocalDate.of(2026, 4, 23)).isEmpty());
    }

    // ─────────────────────────────────────────
    // 异常
    // ─────────────────────────────────────────
    @Test
    void invalidCycleType_throws() {
        assertThrows(IllegalArgumentException.class, () ->
                CycleCalculator.nextRunDate(99, null, LocalDate.of(2026, 4, 23)));
    }

    @Test
    void emptyCycleDates_throws() {
        assertThrows(IllegalArgumentException.class, () ->
                CycleCalculator.nextRunDate(
                        ScheduledFlowConst.CYCLE_MONTHLY, "[]", LocalDate.of(2026, 4, 23)));
    }
}
