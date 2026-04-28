package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.utils.ScheduledFlowConst;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.LocalTime;
import java.time.YearMonth;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;
import java.util.Date;
import java.util.LinkedHashMap;

// v2.7.0 (auto-excel): 自动月度 Excel 提前提醒派发
//
// 策略：每天 remind_time 扫一次（由 ReminderDispatchTask 触发） + (NOTICE_TYPE_AUTO_EXCEL_REMIND, runDate) 防重
//      = 等效"只发一次"（与定时记账提醒一致）
//
// 提醒内容：告诉用户"N 天后将生成 X 月账单"，让用户有机会先把当月数据补齐 / 修正
@Slf4j
@Service
public class AutoExcelReminderService {

    private static final DateTimeFormatter YYYY_MM    = DateTimeFormatter.ofPattern("yyyy-MM");
    private static final DateTimeFormatter YYYY_MM_DD = DateTimeFormatter.ofPattern("yyyy-MM-dd");

    @Autowired
    private AutoExcelConfigService configService;

    @Autowired
    private UserNoticeService noticeService;

    @Autowired
    private MailService mailService;

    /**
     * 资格判断 + 防重 + 派发。不符合条件静默返回。
     * 由 ReminderDispatchTask 在每天 remind_time 扫描时调用。
     */
    public void checkAndDispatch() {
        if (!configService.isEnabled()) return;
        if (!configService.isRemindEnabled()) return;

        LocalDate today = LocalDate.now();
        LocalTime runTime = parseTime(configService.getTime());
        LocalDate runDate = AutoExcelConfigService.computeNextRunDate(today, configService.getDayOfMonth(), runTime);
        if (runDate == null) return;

        // 在 [runDate - remindBeforeDays, runDate] 窗口内才提醒
        long days = ChronoUnit.DAYS.between(today, runDate);
        int n = configService.getRemindBeforeDays();
        if (days < 0 || days > n) return;

        Date runDateAsDate = toDate(runDate);

        // 防重：(NOTICE_TYPE_AUTO_EXCEL_REMIND, runDate) 等效只发一次
        if (noticeService.existsForTypeAndDate(
                ScheduledFlowConst.NOTICE_TYPE_AUTO_EXCEL_REMIND, runDateAsDate)) {
            return;
        }

        YearMonth targetYm = AutoExcelConfigService.computeTargetYearMonth(runDate, configService.getTarget());
        String yearMonth = targetYm.format(YYYY_MM);

        String title = "自动生成账单提醒：" + yearMonth;

        // 站内通知用纯文本
        String plainContent = buildPlainContent(runDate, today, yearMonth);
        noticeService.create(ScheduledFlowConst.NOTICE_TYPE_AUTO_EXCEL_REMIND,
                title, plainContent, null, runDateAsDate);

        // 邮件用 envelope 结构化
        if (configService.isRemindEmailEnabled()) {
            String summary = "您的自动月度账单 Excel 即将生成。";
            LinkedHashMap<String, String> fields = buildEmailFields(runDate, today, yearMonth);
            String advice = "如需调整生成时间或取消，请前往「系统设置 - 自动账单」修改配置。";
            mailService.sendAutoExcelReminder(yearMonth, summary, fields, advice);
        }

        log.info("auto_excel reminder dispatched: yearMonth={}, runDate={}, email={}",
                yearMonth, runDate, configService.isRemindEmailEnabled());
    }

    /** 站内通知正文（纯文本，App 内展示） */
    private String buildPlainContent(LocalDate runDate, LocalDate today, String yearMonth) {
        long days = ChronoUnit.DAYS.between(today, runDate);
        String daysText = days == 0 ? "今天" : (days == 1 ? "明天" : days + " 天后");

        return "您的自动月度账单 Excel 即将生成。\n\n" +
               "  执行时间：" + runDate.format(YYYY_MM_DD) + " " + configService.getTime() + "（" + daysText + "）\n" +
               "  生成对象：" + yearMonth + " 月账单\n" +
               "  发送方式：" + (configService.isSendEmail() ? "邮件 + 站内通知" : "仅站内通知") + "\n\n" +
               "如需调整生成时间或取消，请前往「系统设置 - 自动账单」修改配置。";
    }

    /** 邮件结构化字段 */
    private LinkedHashMap<String, String> buildEmailFields(LocalDate runDate, LocalDate today, String yearMonth) {
        long days = ChronoUnit.DAYS.between(today, runDate);
        String daysText = days == 0 ? "今天" : (days == 1 ? "明天" : days + " 天后");

        LinkedHashMap<String, String> fields = new LinkedHashMap<>();
        fields.put("执行时间", runDate.format(YYYY_MM_DD) + " " + configService.getTime() + "（" + daysText + "）");
        fields.put("生成对象", yearMonth + " 月账单");
        fields.put("发送方式", configService.isSendEmail() ? "邮件 + 站内通知" : "仅站内通知");
        return fields;
    }

    private static LocalTime parseTime(String hhmm) {
        try { return LocalTime.parse(hhmm); } catch (Exception e) { return LocalTime.of(21, 0); }
    }

    private static Date toDate(LocalDate d) {
        return Date.from(d.atStartOfDay(ZoneId.systemDefault()).toInstant());
    }
}
