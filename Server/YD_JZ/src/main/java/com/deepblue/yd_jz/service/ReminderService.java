package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.dao.jpa.TypeRepository;
import com.deepblue.yd_jz.entity.ScheduledFlowRule;
import com.deepblue.yd_jz.entity.Type;
import com.deepblue.yd_jz.utils.ScheduledFlowConst;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.Date;
import java.util.LinkedHashMap;

// v2.7.0: 定时记账事前提醒派发服务
// 单一入口 checkAndDispatch：判断资格 + 防重复 + 发送（站内 + 可选邮件）
// 被 ReminderDispatchTask（每天 remind_time 扫一批）和 ScheduledFlowRuleService（create/update/start 后立即补发）共用
@Slf4j
@Service
public class ReminderService {

    @Autowired
    private AppConfigService appConfigService;

    @Autowired
    private UserNoticeService noticeService;

    @Autowired
    private MailService mailService;

    @Autowired
    private TypeRepository typeRepository;

    /**
     * 对单条规则做"资格判断 + 防重复 + 派发"
     * 不符合条件静默返回，不抛异常
     */
    public void checkAndDispatch(ScheduledFlowRule rule) {
        if (rule == null) return;
        if (!rule.isReminderEnabled()) return;
        int s = rule.getStatus();
        if (s != ScheduledFlowConst.STATUS_NOT_START && s != ScheduledFlowConst.STATUS_RUNNING) return;
        if (rule.getNextRunDate() == null) return;

        int n = appConfigService.getRemindBeforeDays();
        LocalDate today = LocalDate.now();
        LocalDate runDate = toLocalDate(rule.getNextRunDate());
        if (runDate == null) return;

        // 只在 [today, today+N] 窗口内才应提醒
        if (runDate.isBefore(today) || runDate.isAfter(today.plusDays(n))) return;

        Date runDateAsDate = rule.getNextRunDate();
        if (noticeService.existsReminderFor(rule.getId(), runDateAsDate)) return;

        String title = "定时记账提醒：" + rule.getName();

        // 站内通知用纯文本（用户在 App 内，自带上下文，不需要品牌外壳）
        String plainContent = buildPlainContent(rule, runDate, today);
        noticeService.create(ScheduledFlowConst.NOTICE_TYPE_PRE_REMIND,
                title, plainContent, rule.getId(), runDateAsDate);

        // 邮件用 envelope 结构化，由 MailService 渲染 HTML
        if (rule.isEmailEnabled()) {
            String summary = "您的定时记账规则「" + rule.getName() + "」即将自动执行：";
            LinkedHashMap<String, String> fields = buildEmailFields(rule, runDate, today);
            String advice = "如无异常，系统将按时自动生成这笔流水。";
            mailService.sendScheduledReminder(rule.getName(), summary, fields, advice);
        }

        log.info("reminder dispatched: ruleId={}, runDate={}, email={}",
                rule.getId(), runDate, rule.isEmailEnabled());
    }

    /**
     * 站内通知正文（纯文本）。在 App 内展示，不需要品牌外壳。
     */
    private String buildPlainContent(ScheduledFlowRule rule, LocalDate runDate, LocalDate today) {
        String runTimeShort = shortenRunTime(rule.getRunTime());
        String daysText = relativeDayText(today, runDate);
        String accountName = rule.getAccount() != null ? rule.getAccount().getAName() : "—";
        String typeName = formatTypeName(rule);

        return "您的定时记账规则「" + rule.getName() + "」即将自动执行：\n\n" +
               "  执行时间：" + runDate + " " + runTimeShort + "（" + daysText + "）\n" +
               "  记账金额：" + rule.getMoney() + " 元\n" +
               "  账户：" + accountName + "\n" +
               "  分类：" + typeName + "\n\n" +
               "如无异常，系统将按时自动生成这笔流水。";
    }

    /**
     * 邮件结构化字段（给 MailService HTML 模板用）。
     */
    private LinkedHashMap<String, String> buildEmailFields(ScheduledFlowRule rule, LocalDate runDate, LocalDate today) {
        String runTimeShort = shortenRunTime(rule.getRunTime());
        String daysText = relativeDayText(today, runDate);
        String accountName = rule.getAccount() != null ? rule.getAccount().getAName() : "—";
        String typeName = formatTypeName(rule);

        LinkedHashMap<String, String> fields = new LinkedHashMap<>();
        fields.put("执行时间", runDate + " " + runTimeShort + "（" + daysText + "）");
        fields.put("记账金额", rule.getMoney() + " 元");
        fields.put("账户", accountName);
        fields.put("分类", typeName);
        return fields;
    }

    /** HH:mm:ss → HH:mm */
    private static String shortenRunTime(String runTime) {
        if (runTime == null || runTime.length() < 5) return runTime;
        return runTime.substring(0, 5);
    }

    /** today→runDate 天差转文字 */
    private static String relativeDayText(LocalDate today, LocalDate runDate) {
        long days = ChronoUnit.DAYS.between(today, runDate);
        if (days == 0) return "今天";
        if (days == 1) return "明天";
        return days + " 天后";
    }

    /** 分类展开：顶级只显示名字；子分类显示 "父/子" */
    private String formatTypeName(ScheduledFlowRule rule) {
        if (rule.getType() == null) return "—";
        String name = rule.getType().getTName();
        Integer parent = rule.getType().getParent();
        if (parent != null && parent != -1) {
            Type parentType = typeRepository.findById(parent).orElse(null);
            if (parentType != null) {
                return parentType.getTName() + "/" + name;
            }
        }
        return name;
    }

    private static LocalDate toLocalDate(Date date) {
        if (date == null) return null;
        return new java.sql.Date(date.getTime()).toLocalDate();
    }
}
