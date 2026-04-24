package com.deepblue.yd_jz.task;

import com.deepblue.yd_jz.dao.jpa.ScheduledFlowRuleRepository;
import com.deepblue.yd_jz.entity.ScheduledFlowRule;
import com.deepblue.yd_jz.service.AppConfigService;
import com.deepblue.yd_jz.service.ReminderService;
import com.deepblue.yd_jz.utils.ScheduledFlowConst;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;

import java.time.LocalDate;
import java.time.LocalTime;
import java.time.ZoneId;
import java.util.Arrays;
import java.util.Date;
import java.util.List;

// v2.7.0: 定时记账事前提醒分发器
// 每分钟醒来；当前分钟 == 全局 remind_time 时，扫出 [today, today+N] 窗口内的规则，逐条交给 ReminderService 处理
// 即时性补发（create/update/start 场景）由 ScheduledFlowRuleService 直接调用 ReminderService
@Slf4j
@Configuration
@EnableScheduling
public class ReminderDispatchTask {

    @Autowired
    private ScheduledFlowRuleRepository ruleRepo;

    @Autowired
    private AppConfigService appConfigService;

    @Autowired
    private ReminderService reminderService;

    @Scheduled(cron = "0 * * * * ?")
    public void scan() {
        LocalTime now = LocalTime.now();
        String remindTime = appConfigService.getRemindTime();
        LocalTime target;
        try {
            target = LocalTime.parse(remindTime);
        } catch (Exception e) {
            log.warn("提醒时间配置格式错误: {}，跳过本次", remindTime);
            return;
        }

        // 只在"全局提醒时刻"那一分钟做常规扫描
        if (now.getHour() != target.getHour() || now.getMinute() != target.getMinute()) {
            return;
        }

        int n = appConfigService.getRemindBeforeDays();
        LocalDate today = LocalDate.now();
        Date lower = toDate(today);
        Date upper = toDate(today.plusDays(n));

        List<ScheduledFlowRule> rules = ruleRepo.findRulesForReminder(
                Arrays.asList(ScheduledFlowConst.STATUS_NOT_START, ScheduledFlowConst.STATUS_RUNNING),
                lower, upper);

        for (ScheduledFlowRule rule : rules) {
            try {
                reminderService.checkAndDispatch(rule);
            } catch (Exception e) {
                log.error("派发提醒失败 rule={}: {}", rule.getId(), e.getMessage(), e);
            }
        }
    }

    private static Date toDate(LocalDate localDate) {
        return Date.from(localDate.atStartOfDay(ZoneId.systemDefault()).toInstant());
    }
}
