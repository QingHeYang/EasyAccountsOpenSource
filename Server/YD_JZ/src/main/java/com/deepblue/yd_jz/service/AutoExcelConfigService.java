package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.dto.AutoExcelConfigResponseDto;
import com.deepblue.yd_jz.dto.AutoExcelConfigUpdateDto;
import com.deepblue.yd_jz.event.AutoExcelConfigChangedEvent;
import com.deepblue.yd_jz.exception.BusinessException;
import com.deepblue.yd_jz.exception.ErrorCode;
import com.deepblue.yd_jz.utils.SystemConfigConst;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalTime;
import java.time.YearMonth;
import java.time.format.DateTimeFormatter;
import java.util.Set;
import java.util.regex.Pattern;

// v2.7.0 (auto-excel): 自动月度 Excel 配置语义层
// 提醒采用 A 方案：remind_enabled 总开关；开启后站内必发，邮件按 remind_email_enabled
@Slf4j
@Service
public class AutoExcelConfigService {

    private static final Pattern HHMM = Pattern.compile("^([01]\\d|2[0-3]):[0-5]\\d$");
    private static final Set<String> VALID_TARGETS = Set.of(
            SystemConfigConst.AUTO_EXCEL_TARGET_LAST_MONTH,
            SystemConfigConst.AUTO_EXCEL_TARGET_CURRENT_MONTH);
    private static final DateTimeFormatter YYYY_MM_DD = DateTimeFormatter.ofPattern("yyyy-MM-dd");
    private static final DateTimeFormatter YYYY_MM    = DateTimeFormatter.ofPattern("yyyy-MM");

    @Autowired
    private AppConfigService appConfigService;

    @Autowired
    private MailConfigService mailConfigService;

    @Autowired
    private ApplicationEventPublisher eventPublisher;

    /** 读：含计算出的 nextRunDate / targetYearMonth */
    public AutoExcelConfigResponseDto get() {
        AutoExcelConfigResponseDto dto = new AutoExcelConfigResponseDto();
        dto.setEnabled(isEnabled());
        dto.setDayOfMonth(getDayOfMonth());
        dto.setTime(getTime());
        dto.setTarget(getTarget());
        dto.setSendEmail(isSendEmail());
        dto.setRemindEnabled(isRemindEnabled());
        dto.setRemindBeforeDays(getRemindBeforeDays());
        dto.setRemindEmailEnabled(isRemindEmailEnabled());
        dto.setLastRunDate(getLastRunDate());

        LocalDate next = computeNextRunDate(LocalDate.now(), getDayOfMonth(), parseTime(getTime()));
        dto.setNextRunDate(next.format(YYYY_MM_DD));
        dto.setTargetYearMonth(computeTargetYearMonth(next, getTarget()).format(YYYY_MM));
        return dto;
    }

    /**
     * 更新：null=不修改；校验合法后入库 + 发事件触发调度重排
     */
    @Transactional(rollbackFor = Exception.class)
    public void update(AutoExcelConfigUpdateDto dto) {
        if (dto == null) return;

        // 合并新旧值（已传字段用新值，未传字段用 DB 现值），整体校验后再入库
        Boolean enabled = dto.getEnabled() != null ? dto.getEnabled() : isEnabled();
        Integer dom = dto.getDayOfMonth() != null ? dto.getDayOfMonth() : getDayOfMonth();
        String time = dto.getTime() != null ? dto.getTime().trim() : getTime();
        String target = dto.getTarget() != null ? dto.getTarget().trim() : getTarget();
        Boolean sendEmail = dto.getSendEmail() != null ? dto.getSendEmail() : isSendEmail();
        Boolean remindEnabled = dto.getRemindEnabled() != null ? dto.getRemindEnabled() : isRemindEnabled();
        Integer remindDays = dto.getRemindBeforeDays() != null ? dto.getRemindBeforeDays() : getRemindBeforeDays();
        Boolean remindEmail = dto.getRemindEmailEnabled() != null ? dto.getRemindEmailEnabled() : isRemindEmailEnabled();

        // 校验
        if (dom == null || dom < 1 || dom > 28) {
            throw new BusinessException(ErrorCode.PARAM_INVALID, "dayOfMonth 必须在 1-28 之间");
        }
        if (!HHMM.matcher(time).matches()) {
            throw new BusinessException(ErrorCode.PARAM_FORMAT_ERROR, "time 格式错误，应为 HH:mm");
        }
        if (!VALID_TARGETS.contains(target)) {
            throw new BusinessException(ErrorCode.PARAM_INVALID, "target 仅支持 LAST_MONTH / CURRENT_MONTH");
        }
        if (remindDays == null || remindDays < 1 || remindDays > 28) {
            throw new BusinessException(ErrorCode.PARAM_INVALID, "remindBeforeDays 必须在 1-28 之间");
        }

        // 启用任一邮件类开关 → 必须先配好 SMTP，否则前端体验是"以为开了，但实际收不到"
        if ((Boolean.TRUE.equals(sendEmail) || Boolean.TRUE.equals(remindEmail))
                && !mailConfigService.isMailConfigured()) {
            throw new BusinessException(ErrorCode.MAIL_NOT_CONFIGURED);
        }

        // 入库
        set(SystemConfigConst.AUTO_EXCEL_ENABLED, String.valueOf(enabled));
        set(SystemConfigConst.AUTO_EXCEL_DAY_OF_MONTH, String.valueOf(dom));
        set(SystemConfigConst.AUTO_EXCEL_TIME, time);
        set(SystemConfigConst.AUTO_EXCEL_TARGET, target);
        set(SystemConfigConst.AUTO_EXCEL_SEND_EMAIL, String.valueOf(sendEmail));
        set(SystemConfigConst.AUTO_EXCEL_REMIND_ENABLED, String.valueOf(remindEnabled));
        set(SystemConfigConst.AUTO_EXCEL_REMIND_BEFORE_DAYS, String.valueOf(remindDays));
        set(SystemConfigConst.AUTO_EXCEL_REMIND_EMAIL_ENABLED, String.valueOf(remindEmail));

        log.info("auto_excel config updated: enabled={}, dom={}, time={}, target={}, sendEmail={}, remindEnabled={}, remindDays={}, remindEmail={}",
                enabled, dom, time, target, sendEmail, remindEnabled, remindDays, remindEmail);

        // 发事件触发调度热重排（Phase 10 AutoExcelExecuteTask 监听）
        eventPublisher.publishEvent(new AutoExcelConfigChangedEvent(this));
    }

    // ── 语义读 ─────────────────────────────────────────────

    public boolean isEnabled() {
        return parseBool(get(SystemConfigConst.AUTO_EXCEL_ENABLED, SystemConfigConst.AUTO_EXCEL_ENABLED_DEFAULT));
    }

    public int getDayOfMonth() {
        return parseInt(get(SystemConfigConst.AUTO_EXCEL_DAY_OF_MONTH, SystemConfigConst.AUTO_EXCEL_DAY_OF_MONTH_DEFAULT), 4);
    }

    public String getTime() {
        return get(SystemConfigConst.AUTO_EXCEL_TIME, SystemConfigConst.AUTO_EXCEL_TIME_DEFAULT);
    }

    public String getTarget() {
        return get(SystemConfigConst.AUTO_EXCEL_TARGET, SystemConfigConst.AUTO_EXCEL_TARGET_DEFAULT);
    }

    public boolean isSendEmail() {
        return parseBool(get(SystemConfigConst.AUTO_EXCEL_SEND_EMAIL, SystemConfigConst.AUTO_EXCEL_SEND_EMAIL_DEFAULT));
    }

    public boolean isRemindEnabled() {
        return parseBool(get(SystemConfigConst.AUTO_EXCEL_REMIND_ENABLED, SystemConfigConst.AUTO_EXCEL_REMIND_ENABLED_DEFAULT));
    }

    public int getRemindBeforeDays() {
        return parseInt(get(SystemConfigConst.AUTO_EXCEL_REMIND_BEFORE_DAYS, SystemConfigConst.AUTO_EXCEL_REMIND_BEFORE_DAYS_DEFAULT), 3);
    }

    public boolean isRemindEmailEnabled() {
        return parseBool(get(SystemConfigConst.AUTO_EXCEL_REMIND_EMAIL_ENABLED, SystemConfigConst.AUTO_EXCEL_REMIND_EMAIL_ENABLED_DEFAULT));
    }

    /** 上次执行日期（YYYY-MM-DD），空表示从未运行 */
    public String getLastRunDate() {
        String v = get(SystemConfigConst.AUTO_EXCEL_LAST_RUN_DATE, "");
        return v == null ? "" : v;
    }

    /** 由 AutoExcelExecuteService 在执行成功后调用，仅作展示，不参与防重 */
    public void setLastRunDate(LocalDate date) {
        set(SystemConfigConst.AUTO_EXCEL_LAST_RUN_DATE, date == null ? "" : date.format(YYYY_MM_DD));
    }

    // ── 计算工具 ──────────────────────────────────────────

    /**
     * 给定 today + 配置 dayOfMonth + runTime，算下次执行日：
     *   - today.day < dom → 本月 dom 日
     *   - today.day == dom：今天 runTime 已过 → 下月 dom；未过 → 今天
     *   - today.day > dom → 下月 dom 日
     * 月份的 dom 若超过该月天数，自动取最后一天（28 之内不会触发，但保留兜底）
     */
    public static LocalDate computeNextRunDate(LocalDate today, int dom, LocalTime runTime) {
        YearMonth ym = YearMonth.from(today);
        int curDay = today.getDayOfMonth();
        if (curDay < dom) {
            return ym.atDay(Math.min(dom, ym.lengthOfMonth()));
        }
        if (curDay == dom) {
            if (runTime == null || LocalTime.now().isBefore(runTime)) {
                return today;
            }
        }
        YearMonth nextYm = ym.plusMonths(1);
        return nextYm.atDay(Math.min(dom, nextYm.lengthOfMonth()));
    }

    /** 给定下次执行日 + target，算将生成的 yyyy-MM */
    public static YearMonth computeTargetYearMonth(LocalDate runDate, String target) {
        YearMonth runMonth = YearMonth.from(runDate);
        if (SystemConfigConst.AUTO_EXCEL_TARGET_LAST_MONTH.equals(target)) {
            return runMonth.minusMonths(1);
        }
        return runMonth;  // CURRENT_MONTH
    }

    private static LocalTime parseTime(String hhmm) {
        try { return LocalTime.parse(hhmm); } catch (Exception e) { return LocalTime.of(21, 0); }
    }

    // ── helpers ────────────────────────────────────────────

    private String get(String key, String defVal) {
        String v = appConfigService.getValue(SystemConfigConst.DOMAIN_AUTO_EXCEL, key);
        return v == null ? defVal : v;
    }

    private void set(String key, String val) {
        appConfigService.setValue(SystemConfigConst.DOMAIN_AUTO_EXCEL, key, val);
    }

    private static boolean parseBool(String v) {
        return "true".equalsIgnoreCase(v);
    }

    private static int parseInt(String v, int def) {
        try { return Integer.parseInt(v); } catch (Exception e) { return def; }
    }
}
