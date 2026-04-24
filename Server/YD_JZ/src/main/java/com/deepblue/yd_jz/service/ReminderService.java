package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.dao.jpa.TypeRepository;
import com.deepblue.yd_jz.entity.ScheduledFlowRule;
import com.deepblue.yd_jz.entity.Type;
import com.deepblue.yd_jz.utils.NotificationWebHook;
import com.deepblue.yd_jz.utils.ScheduledFlowConst;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.Date;

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
    private NotificationWebHook notificationWebHook;

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
        String content = buildContent(rule, runDate, today);

        // 站内通知：不带 EasyAccounts 前缀/签名（用户已经在 App 内，自带上下文）
        noticeService.create(ScheduledFlowConst.NOTICE_TYPE_PRE_REMIND,
                title, content, rule.getId(), runDateAsDate);

        // 邮件：加品牌标识（邮箱里要自证身份，否则用户收件箱看不出谁发的）
        if (rule.isEmailEnabled()) {
            String emailSubject = "[EasyAccounts] " + title;
            String emailBody = content + "\n\n—— EasyAccounts 记账助手";
            notificationWebHook.sendEmail(emailSubject, emailBody);
        }

        log.info("reminder dispatched: ruleId={}, runDate={}, email={}",
                rule.getId(), runDate, rule.isEmailEnabled());
    }

    /**
     * 构造提醒正文（同时用于站内通知和邮件）
     * 格式：
     *   您的定时记账规则「房贷」即将自动执行：
     *
     *     执行时间：2026-05-24 09:00（2 天后）
     *     记账金额：3500.00 元
     *     账户：招商银行
     *     分类：贷款支出/房贷
     *
     *   如无异常，系统将按时自动生成这笔流水。
     */
    private String buildContent(ScheduledFlowRule rule, LocalDate runDate, LocalDate today) {
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
