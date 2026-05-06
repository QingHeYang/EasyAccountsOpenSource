package com.deepblue.yd_jz.controller;

import com.deepblue.yd_jz.dto.AuthConfigResponseDto;
import com.deepblue.yd_jz.dto.AuthConfigUpdateDto;
import com.deepblue.yd_jz.dto.AutoExcelConfigResponseDto;
import com.deepblue.yd_jz.dto.AutoExcelConfigUpdateDto;
import com.deepblue.yd_jz.dto.BackupConfigResponseDto;
import com.deepblue.yd_jz.dto.BackupConfigUpdateDto;
import com.deepblue.yd_jz.dto.BaseDto;
import com.deepblue.yd_jz.dto.MailConfigResponseDto;
import com.deepblue.yd_jz.dto.MailConfigUpdateDto;
import com.deepblue.yd_jz.dto.ReminderConfigDto;
import com.deepblue.yd_jz.dto.SystemConfigOverviewDto;
import com.deepblue.yd_jz.service.AppConfigService;
import com.deepblue.yd_jz.service.AuthConfigService;
import com.deepblue.yd_jz.service.AutoExcelConfigService;
import com.deepblue.yd_jz.service.AutoExcelExecuteService;
import com.deepblue.yd_jz.service.AutoExcelReminderService;
import com.deepblue.yd_jz.service.BackupConfigService;
import com.deepblue.yd_jz.service.MailConfigService;
import com.deepblue.yd_jz.service.MailService;
import com.deepblue.yd_jz.utils.SystemConfigConst;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

// v2.7.0 (config-ui): 系统设置统一 REST 入口
//   GET  /system/config/{mail|backup|auth}  —— 读配置（mail.password 自动脱敏）
//   PUT  /system/config/{mail|backup|auth}  —— 更新配置（partial：null=不动 / 非 null=覆盖；password 空串=清空）
//   POST /system/config/mail/test           —— 测试发邮件，把 SMTP 异常透出给前端
@Slf4j
@RestController
@Tag(name = "系统设置")
@RequestMapping("/system/config")
public class SystemConfigController {

    @Autowired
    private MailConfigService mailConfigService;

    @Autowired
    private BackupConfigService backupConfigService;

    @Autowired
    private AuthConfigService authConfigService;

    @Autowired
    private MailService mailService;

    @Autowired
    private AppConfigService appConfigService;

    @Autowired
    private AutoExcelConfigService autoExcelConfigService;

    @Autowired
    private AutoExcelExecuteService autoExcelExecuteService;

    @Autowired
    private AutoExcelReminderService autoExcelReminderService;

    private static final String[] DOW_CN = {"一", "二", "三", "四", "五", "六", "日"};

    // ────────────── 系统整体概览 ──────────────

    @io.swagger.v3.oas.annotations.Operation(summary = "系统设置整体概览（一处覆盖 mail/backup/auth/scheduled_flow 4 域，password/收件人邮箱不暴露）")
    @GetMapping("/overview")
    public BaseDto<SystemConfigOverviewDto> overview() {
        SystemConfigOverviewDto dto = new SystemConfigOverviewDto();

        // mail
        SystemConfigOverviewDto.MailOverview mail = new SystemConfigOverviewDto.MailOverview();
        mail.setIsConfigured(mailConfigService.isMailConfigured());
        mail.setSmtpServer(mailConfigService.getSmtpServer());
        mail.setFromEmail(mailConfigService.getFromEmail());
        mail.setToListCount(countToList(mailConfigService.getToList()));
        mail.setSendSqlBackup(mailConfigService.isSendSqlBackupEnabled());
        mail.setSendExcel(mailConfigService.isSendExcelEnabled());
        dto.setMail(mail);

        // backup
        BackupConfigResponseDto bc = backupConfigService.get();
        SystemConfigOverviewDto.BackupOverview backup = new SystemConfigOverviewDto.BackupOverview();
        backup.setEnabled(bc.getEnabled());
        backup.setFrequency(bc.getFrequency());
        backup.setTime(bc.getTime());
        backup.setDayOfWeek(bc.getDayOfWeek());
        backup.setDayOfMonth(bc.getDayOfMonth());
        backup.setCron(bc.getCron());
        backup.setHumanReadable(humanReadableBackup(bc));
        dto.setBackup(backup);

        // auth
        AuthConfigResponseDto ac = authConfigService.get();
        SystemConfigOverviewDto.AuthOverview auth = new SystemConfigOverviewDto.AuthOverview();
        auth.setLoginEnable(ac.getLoginEnable());
        auth.setSingleLogin(ac.getSingleLogin());
        auth.setTokenExpiredMinutes(ac.getTokenExpiredMinutes());
        dto.setAuth(auth);

        // scheduled_flow（已有 AppConfigService 提供的语义读）
        SystemConfigOverviewDto.ScheduledFlowOverview sf = new SystemConfigOverviewDto.ScheduledFlowOverview();
        sf.setRemindBeforeDays(appConfigService.getRemindBeforeDays());
        sf.setRemindTime(appConfigService.getRemindTime());
        dto.setScheduledFlow(sf);

        // auto_excel
        AutoExcelConfigResponseDto ae = autoExcelConfigService.get();
        SystemConfigOverviewDto.AutoExcelOverview aex = new SystemConfigOverviewDto.AutoExcelOverview();
        aex.setEnabled(ae.getEnabled());
        aex.setDayOfMonth(ae.getDayOfMonth());
        aex.setTime(ae.getTime());
        aex.setTarget(ae.getTarget());
        aex.setSendEmail(ae.getSendEmail());
        aex.setRemindEnabled(ae.getRemindEnabled());
        aex.setRemindBeforeDays(ae.getRemindBeforeDays());
        aex.setRemindEmailEnabled(ae.getRemindEmailEnabled());
        aex.setLastRunDate(ae.getLastRunDate());
        aex.setNextRunDate(ae.getNextRunDate());
        aex.setTargetYearMonth(ae.getTargetYearMonth());
        aex.setHumanReadable(humanReadableAutoExcel(ae));
        dto.setAutoExcel(aex);

        BaseDto<SystemConfigOverviewDto> res = BaseDto.setSuccessBean();
        res.setData(dto);
        return res;
    }

    /** auto_excel 翻译人话 */
    private static String humanReadableAutoExcel(AutoExcelConfigResponseDto ae) {
        if (Boolean.FALSE.equals(ae.getEnabled())) return "已关闭";
        String targetText = SystemConfigConst.AUTO_EXCEL_TARGET_LAST_MONTH.equals(ae.getTarget())
                ? "生成上月" : "生成本月";
        return "每月 " + ae.getDayOfMonth() + " 日 " + ae.getTime() + "（" + targetText + "）";
    }

    private static int countToList(String toList) {
        if (toList == null || toList.trim().isEmpty()) return 0;
        return toList.split(",").length;
    }

    /** cron 翻译人话 */
    private static String humanReadableBackup(BackupConfigResponseDto bc) {
        if (Boolean.FALSE.equals(bc.getEnabled())) return "已关闭";
        String time = bc.getTime() != null ? bc.getTime() : "—";
        String freq = bc.getFrequency();
        if (SystemConfigConst.FREQ_DAILY.equals(freq)) {
            return "每天 " + time;
        }
        if (SystemConfigConst.FREQ_WEEKLY.equals(freq)) {
            int dow = bc.getDayOfWeek() != null ? bc.getDayOfWeek() : 1;
            int idx = (dow >= 1 && dow <= 7) ? dow - 1 : 0;
            return "每周" + DOW_CN[idx] + " " + time;
        }
        if (SystemConfigConst.FREQ_MONTHLY.equals(freq)) {
            int dom = bc.getDayOfMonth() != null ? bc.getDayOfMonth() : 1;
            return "每月 " + dom + " 日 " + time;
        }
        return "未知调度";
    }

    // ────────────── 邮件 SMTP ──────────────

    @Operation(summary = "读取邮件配置（password 字段始终为空，前端用 isPasswordSet 判断是否已设置）")
    @GetMapping("/mail")
    public BaseDto<MailConfigResponseDto> getMail() {
        BaseDto<MailConfigResponseDto> res = BaseDto.setSuccessBean();
        res.setData(mailConfigService.getMaskedConfig());
        return res;
    }

    @Operation(summary = "更新邮件配置（partial：未传字段不修改；password 空串=清空）")
    @PutMapping("/mail")
    public BaseDto<MailConfigResponseDto> updateMail(@RequestBody MailConfigUpdateDto dto) {
        mailConfigService.update(dto);
        BaseDto<MailConfigResponseDto> res = BaseDto.setSuccessBean();
        res.setData(mailConfigService.getMaskedConfig());
        return res;
    }

    @Operation(summary = "测试发邮件：用当前配置发一封测试邮件给收件人列表，把 SMTP 异常文本返回给前端")
    @PostMapping("/mail/test")
    public BaseDto<MailService.SendResult> testMail() {
        MailService.SendResult result = mailService.sendTestMail();
        BaseDto<MailService.SendResult> res = BaseDto.setSuccessBean();
        res.setData(result);
        return res;
    }

    @Operation(summary = "一键测试所有 8 类邮件（验证 HTML 模板渲染）—— 注意：mail.send_sql_backup / send_excel 都需为 true")
    @PostMapping("/mail/testAll")
    public BaseDto<java.util.List<java.util.Map<String, Object>>> testAllMails() {
        if (!mailConfigService.isMailConfigured()) {
            return BaseDto.setErrorBean("SMTP 配置不完整，请先填写", 40000);
        }

        // 生成一个临时小附件供需要附件的邮件使用
        java.io.File dummy;
        try {
            dummy = java.io.File.createTempFile("easy_accounts_test_attach_", ".txt");
            try (java.io.FileWriter w = new java.io.FileWriter(dummy)) {
                w.write("EasyAccounts 测试附件\n生成时间：" + new java.util.Date());
            }
        } catch (java.io.IOException e) {
            return BaseDto.setErrorBean("生成测试附件失败：" + e.getMessage(), 50001);
        }

        java.util.List<java.util.Map<String, Object>> results = new java.util.ArrayList<>();

        // 1. SQL 备份
        results.add(safeRun("1. SQL 备份完成", () -> mailService.sendSqlBackup(dummy)));

        // 2. 月度账单 Excel
        results.add(safeRun("2. 2026-04 月度账单",
                () -> mailService.sendMonthExcel(dummy, "2026-04")));

        // 3. 财务分析 Excel
        results.add(safeRun("3. 财务分析导出",
                () -> mailService.sendAnalysisExcel(dummy, "2026-01 至 2026-04")));

        // 4. 筛选账单 Excel
        results.add(safeRun("4. 筛选账单导出",
                () -> mailService.sendScreenExcel(dummy)));

        // 5. 定时记账提醒
        results.add(safeRun("5. 定时记账提醒：房贷", () -> {
            java.util.LinkedHashMap<String, String> fields = new java.util.LinkedHashMap<>();
            fields.put("执行时间", "2026-05-04 21:00（7 天后）");
            fields.put("记账金额", "3500.00 元");
            fields.put("账户", "招商银行");
            fields.put("分类", "贷款支出/房贷");
            mailService.sendScheduledReminder("房贷",
                    "您的定时记账规则「房贷」即将自动执行：",
                    fields,
                    "如无异常，系统将按时自动生成这笔流水。");
        }));

        // 6. 自动月度 Excel · 无流水
        results.add(safeRun("6. 月度账单：本月无流水",
                () -> mailService.sendAutoExcelNoFlow("2026-04")));

        // 7. 自动月度 Excel · 提前提醒
        results.add(safeRun("7. 自动生成账单提醒：2026-04", () -> {
            java.util.LinkedHashMap<String, String> fields = new java.util.LinkedHashMap<>();
            fields.put("执行时间", "2026-05-04 21:00（7 天后）");
            fields.put("生成对象", "2026-04 月账单");
            fields.put("发送方式", "邮件 + 站内通知");
            mailService.sendAutoExcelReminder("2026-04",
                    "您的自动月度账单 Excel 即将生成。",
                    fields,
                    "如需调整生成时间或取消，请前往「系统设置 - 自动账单」修改配置。");
        }));

        // 8. 邮件配置测试
        results.add(safeRun("8. 邮件配置测试",
                () -> mailService.sendTestMail()));

        // 清理临时附件
        try { dummy.delete(); } catch (Exception ignore) {}

        BaseDto<java.util.List<java.util.Map<String, Object>>> res = BaseDto.setSuccessBean();
        res.setData(results);
        return res;
    }

    private static java.util.Map<String, Object> safeRun(String name, Runnable task) {
        java.util.Map<String, Object> r = new java.util.LinkedHashMap<>();
        r.put("name", name);
        try {
            task.run();
            r.put("status", "ok");
        } catch (Exception e) {
            r.put("status", "fail");
            r.put("error", e.getMessage());
        }
        return r;
    }

    // ────────────── 备份调度 ──────────────

    @Operation(summary = "读取备份配置（含拼出的 cron，前端展示 / 调试用）")
    @GetMapping("/backup")
    public BaseDto<BackupConfigResponseDto> getBackup() {
        BaseDto<BackupConfigResponseDto> res = BaseDto.setSuccessBean();
        res.setData(backupConfigService.get());
        return res;
    }

    @Operation(summary = "更新备份配置（变更后自动重排调度，无需重启）")
    @PutMapping("/backup")
    public BaseDto<BackupConfigResponseDto> updateBackup(@RequestBody BackupConfigUpdateDto dto) {
        backupConfigService.update(dto);
        BaseDto<BackupConfigResponseDto> res = BaseDto.setSuccessBean();
        res.setData(backupConfigService.get());
        return res;
    }

    // ────────────── 认证 ──────────────

    @Operation(summary = "读取认证配置")
    @GetMapping("/auth")
    public BaseDto<AuthConfigResponseDto> getAuth() {
        BaseDto<AuthConfigResponseDto> res = BaseDto.setSuccessBean();
        res.setData(authConfigService.get());
        return res;
    }

    @Operation(summary = "更新认证配置（变更后下一个请求即生效，无需重启）")
    @PutMapping("/auth")
    public BaseDto<AuthConfigResponseDto> updateAuth(@RequestBody AuthConfigUpdateDto dto) {
        authConfigService.update(dto);
        BaseDto<AuthConfigResponseDto> res = BaseDto.setSuccessBean();
        res.setData(authConfigService.get());
        return res;
    }

    // ────────────── 定时记账提醒（聚合到系统设置） ──────────────
    // 与 /scheduledFlow/config/reminder 同源（都走 AppConfigService），统一系统设置入口

    @Operation(summary = "读取定时记账全局提醒配置")
    @GetMapping("/scheduledFlow")
    public BaseDto<ReminderConfigDto> getScheduledFlow() {
        ReminderConfigDto dto = new ReminderConfigDto();
        dto.setRemindBeforeDays(appConfigService.getRemindBeforeDays());
        dto.setRemindTime(appConfigService.getRemindTime());
        BaseDto<ReminderConfigDto> res = BaseDto.setSuccessBean();
        res.setData(dto);
        return res;
    }

    @Operation(summary = "更新定时记账全局提醒配置（remindBeforeDays 1-5；remindTime HH:mm）")
    @PutMapping("/scheduledFlow")
    public BaseDto<ReminderConfigDto> updateScheduledFlow(@RequestBody ReminderConfigDto dto) {
        appConfigService.updateReminderConfig(dto.getRemindBeforeDays(), dto.getRemindTime());
        ReminderConfigDto out = new ReminderConfigDto();
        out.setRemindBeforeDays(appConfigService.getRemindBeforeDays());
        out.setRemindTime(appConfigService.getRemindTime());
        BaseDto<ReminderConfigDto> res = BaseDto.setSuccessBean();
        res.setData(out);
        return res;
    }

    // ────────────── 自动月度 Excel ──────────────

    @Operation(summary = "读取自动月度 Excel 配置（含计算出的 nextRunDate / targetYearMonth）")
    @GetMapping("/autoExcel")
    public BaseDto<AutoExcelConfigResponseDto> getAutoExcel() {
        BaseDto<AutoExcelConfigResponseDto> res = BaseDto.setSuccessBean();
        res.setData(autoExcelConfigService.get());
        return res;
    }

    @Operation(summary = "更新自动月度 Excel 配置（变更后自动重排调度，无需重启）")
    @PutMapping("/autoExcel")
    public BaseDto<AutoExcelConfigResponseDto> updateAutoExcel(@RequestBody AutoExcelConfigUpdateDto dto) {
        autoExcelConfigService.update(dto);
        BaseDto<AutoExcelConfigResponseDto> res = BaseDto.setSuccessBean();
        res.setData(autoExcelConfigService.get());
        return res;
    }

    @Operation(summary = "立即触发一次自动生成（不等下次 cron），方便测试 / 用户手动补发")
    @PostMapping("/autoExcel/runNow")
    public BaseDto<Void> runAutoExcelNow() {
        autoExcelExecuteService.runOnce();
        return BaseDto.setSuccessBean();
    }

    @Operation(summary = "立即派发一次提醒（用于测试；走防重逻辑，已发过则不重发）")
    @PostMapping("/autoExcel/sendReminder")
    public BaseDto<Void> sendAutoExcelReminderNow() {
        autoExcelReminderService.checkAndDispatch();
        return BaseDto.setSuccessBean();
    }
}
