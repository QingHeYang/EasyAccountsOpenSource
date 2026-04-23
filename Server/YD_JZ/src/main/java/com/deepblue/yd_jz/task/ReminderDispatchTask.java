package com.deepblue.yd_jz.task;

import com.deepblue.yd_jz.dao.jpa.ScheduledFlowRuleRepository;
import com.deepblue.yd_jz.entity.ScheduledFlowRule;
import com.deepblue.yd_jz.service.AppConfigService;
import com.deepblue.yd_jz.service.UserNoticeService;
import com.deepblue.yd_jz.utils.NotificationWebHook;
import com.deepblue.yd_jz.utils.ScheduledFlowConst;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;

import java.time.LocalDate;
import java.time.LocalTime;
import java.time.ZoneId;
import java.util.Date;
import java.util.List;

// v2.7.0: 定时记账"事前提醒"分发器
// 每分钟醒来，如果当前分钟等于全局提醒时刻，扫出 N 天后将执行的规则，为每条写一条站内通知（可选邮件）
@Slf4j
@Configuration
@EnableScheduling
public class ReminderDispatchTask {

    @Autowired
    private ScheduledFlowRuleRepository ruleRepo;

    @Autowired
    private AppConfigService appConfigService;

    @Autowired
    private UserNoticeService noticeService;

    @Autowired
    private NotificationWebHook notificationWebHook;

    @Scheduled(cron = "0 * * * * ?")
    public void scan() {
        LocalTime now = LocalTime.now();
        String remindTime = appConfigService.getRemindTime();  // HH:mm
        LocalTime target;
        try {
            target = LocalTime.parse(remindTime);
        } catch (Exception e) {
            log.warn("提醒时间配置格式错误: {}，跳过本次", remindTime);
            return;
        }

        // 只在"全局提醒时刻"那一分钟干活
        if (now.getHour() != target.getHour() || now.getMinute() != target.getMinute()) {
            return;
        }

        int n = appConfigService.getRemindBeforeDays();
        LocalDate targetDate = LocalDate.now().plusDays(n);
        Date targetDateAsDate = toDate(targetDate);

        List<ScheduledFlowRule> rules = ruleRepo.findRulesForReminder(
                ScheduledFlowConst.STATUS_RUNNING, targetDateAsDate);

        for (ScheduledFlowRule rule : rules) {
            try {
                dispatch(rule, targetDate, targetDateAsDate);
            } catch (Exception e) {
                log.error("派发提醒失败 rule={}: {}", rule.getId(), e.getMessage(), e);
            }
        }
    }

    private void dispatch(ScheduledFlowRule rule, LocalDate targetDate, Date targetDateAsDate) {
        // 防重复：同规则同执行日只发一条
        if (noticeService.existsReminderFor(rule.getId(), targetDateAsDate)) {
            return;
        }

        String title = "定时记账提醒：" + rule.getName();
        String content = String.format(
                "规则「%s」将于 %s %s 自动记账：%s 元",
                rule.getName(),
                targetDate,
                rule.getRunTime(),
                rule.getMoney()
        );

        noticeService.create(ScheduledFlowConst.NOTICE_TYPE_PRE_REMIND,
                title, content, rule.getId(), targetDateAsDate);

        if (rule.isEmailEnabled()) {
            notificationWebHook.sendEmail(title, content);
        }

        log.info("reminder dispatched: ruleId={}, runDate={}, email={}",
                rule.getId(), targetDate, rule.isEmailEnabled());
    }

    private static Date toDate(LocalDate localDate) {
        return Date.from(localDate.atStartOfDay(ZoneId.systemDefault()).toInstant());
    }
}
