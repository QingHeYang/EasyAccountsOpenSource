package com.deepblue.yd_jz.utils;

import com.deepblue.yd_jz.exception.BusinessException;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

// v2.7.0 (config-ui): CronBuilder 单测
class CronBuilderTest {

    // ── daily ─────────────────────────────
    @Test
    void daily_22_00() {
        assertEquals("0 0 22 * * ?", CronBuilder.build("daily", "22:00", null, null));
    }

    @Test
    void daily_09_30() {
        assertEquals("0 30 9 * * ?", CronBuilder.build("daily", "09:30", null, null));
    }

    @Test
    void daily_ignores_dow_dom() {
        // daily 模式下 dayOfWeek/dayOfMonth 应被忽略
        assertEquals("0 0 0 * * ?", CronBuilder.build("daily", "00:00", 5, 15));
    }

    // ── weekly ────────────────────────────
    @Test
    void weekly_monday_22() {
        assertEquals("0 0 22 ? * MON", CronBuilder.build("weekly", "22:00", 1, null));
    }

    @Test
    void weekly_sunday_late() {
        assertEquals("0 59 23 ? * SUN", CronBuilder.build("weekly", "23:59", 7, null));
    }

    @Test
    void weekly_friday() {
        assertEquals("0 15 14 ? * FRI", CronBuilder.build("weekly", "14:15", 5, null));
    }

    // ── monthly ───────────────────────────
    @Test
    void monthly_first_day() {
        assertEquals("0 0 22 1 * ?", CronBuilder.build("monthly", "22:00", null, 1));
    }

    @Test
    void monthly_28th() {
        assertEquals("0 30 8 28 * ?", CronBuilder.build("monthly", "08:30", null, 28));
    }

    // ── 校验失败 ───────────────────────────
    @Test
    void invalidFrequency_throws() {
        assertThrows(BusinessException.class,
                () -> CronBuilder.build("yearly", "22:00", null, null));
    }

    @Test
    void nullFrequency_throws() {
        assertThrows(BusinessException.class,
                () -> CronBuilder.build(null, "22:00", null, null));
    }

    @Test
    void invalidTimeFormat_throws() {
        assertThrows(BusinessException.class,
                () -> CronBuilder.build("daily", "25:00", null, null));
        assertThrows(BusinessException.class,
                () -> CronBuilder.build("daily", "9:30", null, null)); // 必须 HH:mm 两位
        assertThrows(BusinessException.class,
                () -> CronBuilder.build("daily", null, null, null));
    }

    @Test
    void weekly_invalidDayOfWeek_throws() {
        assertThrows(BusinessException.class,
                () -> CronBuilder.build("weekly", "22:00", 0, null));
        assertThrows(BusinessException.class,
                () -> CronBuilder.build("weekly", "22:00", 8, null));
        assertThrows(BusinessException.class,
                () -> CronBuilder.build("weekly", "22:00", null, null));
    }

    @Test
    void monthly_invalidDayOfMonth_throws() {
        assertThrows(BusinessException.class,
                () -> CronBuilder.build("monthly", "22:00", null, 0));
        assertThrows(BusinessException.class,
                () -> CronBuilder.build("monthly", "22:00", null, 29));  // UI 限制 ≤ 28
        assertThrows(BusinessException.class,
                () -> CronBuilder.build("monthly", "22:00", null, 31));
        assertThrows(BusinessException.class,
                () -> CronBuilder.build("monthly", "22:00", null, null));
    }
}
