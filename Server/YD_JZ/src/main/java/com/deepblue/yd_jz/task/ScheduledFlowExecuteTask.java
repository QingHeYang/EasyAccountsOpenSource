package com.deepblue.yd_jz.task;

import com.deepblue.yd_jz.dao.jpa.ScheduledFlowRuleRepository;
import com.deepblue.yd_jz.entity.ScheduledFlowRule;
import com.deepblue.yd_jz.exception.BusinessException;
import com.deepblue.yd_jz.exception.ErrorCode;
import com.deepblue.yd_jz.service.ScheduledFlowRuleService;
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

// v2.7.0: 定时记账执行扫描器
// 每分钟醒来扫规则，按"执行 / 只推游标 / 跳过"四分支决策
@Slf4j
@Configuration
@EnableScheduling
public class ScheduledFlowExecuteTask {

    @Autowired
    private ScheduledFlowRuleService ruleService;

    @Autowired
    private ScheduledFlowRuleRepository ruleRepo;

    @Scheduled(cron = "0 * * * * ?")
    public void scan() {
        LocalDate today = LocalDate.now();
        LocalTime nowTime = LocalTime.now();
        Date todayAsDate = toDate(today);

        // 步骤 1：NOT_START 到达 start_date → 自动切 RUNNING
        List<ScheduledFlowRule> starting = ruleRepo.findDueRules(
                ScheduledFlowConst.STATUS_NOT_START, todayAsDate);
        for (ScheduledFlowRule r : starting) {
            try {
                ruleService.markRunning(r);
                log.info("scheduled rule {} auto started", r.getId());
            } catch (Exception e) {
                log.error("failed to auto-start rule {}: {}", r.getId(), e.getMessage());
            }
        }

        // 步骤 2：RUNNING 规则的四分支决策
        List<ScheduledFlowRule> running = ruleRepo.findDueRules(
                ScheduledFlowConst.STATUS_RUNNING, todayAsDate);
        for (ScheduledFlowRule r : running) {
            try {
                processRule(r, today, nowTime);
            } catch (Exception e) {
                log.error("scan error on rule {}: {}", r.getId(), e.getMessage(), e);
            }
        }
    }

    private void processRule(ScheduledFlowRule rule, LocalDate today, LocalTime nowTime) {
        // 分支 A：今天已执行过
        if (rule.getLastRunDate() != null
                && toLocalDate(rule.getLastRunDate()).equals(today)) {
            return;
        }

        LocalDate nextRun = toLocalDate(rule.getNextRunDate());

        // 分支 B：游标在过去（历史遗留 / 停机期间错过）→ 只推游标
        if (nextRun.isBefore(today)) {
            ruleService.advanceCursor(rule, today, false);
            log.info("rule {} cursor advanced from past date {}", rule.getId(), nextRun);
            return;
        }

        // nextRun == today，进入分钟级判断
        LocalTime runTime = parseRunTime(rule.getRunTime());

        // 分支 C：今天还没到点 → 等这分钟到来
        if (nowTime.isBefore(runTime)) {
            return;
        }

        // 分支 D：正好到点（同分钟）→ 执行
        if (nowTime.getHour() == runTime.getHour()
                && nowTime.getMinute() == runTime.getMinute()) {
            executeRule(rule, today);
            return;
        }

        // 分支 E：今天已过点 → 只推游标
        ruleService.advanceCursor(rule, today, false);
        log.info("rule {} missed today's run_time {}, cursor advanced", rule.getId(), rule.getRunTime());
    }

    private void executeRule(ScheduledFlowRule rule, LocalDate today) {
        Integer flowId = null;
        boolean success = false;
        int failCategory = 0;
        String failReason = null;
        boolean masterDataFailure = false;

        try {
            flowId = ruleService.executeRuleOrThrow(rule, today);
            success = true;
        } catch (BusinessException be) {
            failReason = be.getMsg();
            if (isMasterDataError(be.getCode())) {
                failCategory = ScheduledFlowConst.FAIL_MASTER_DATA;
                masterDataFailure = true;
            } else {
                failCategory = ScheduledFlowConst.FAIL_OTHER;
            }
        } catch (Exception e) {
            failCategory = ScheduledFlowConst.FAIL_OTHER;
            failReason = e.getMessage() == null ? e.getClass().getSimpleName() : e.getMessage();
        }

        if (success) {
            ruleService.recordSuccess(rule.getId(), flowId);
            ruleService.advanceCursor(rule, today, true);
            log.info("rule {} executed successfully, flowId={}", rule.getId(), flowId);
            return;
        }

        // 失败路径
        ruleService.recordFailure(rule.getId(), failCategory, failReason);
        if (masterDataFailure) {
            // 重查一次规则，避免状态已被别处改（比如主数据事件挂钩并发触发）
            ScheduledFlowRule fresh = ruleRepo.findById(rule.getId()).orElse(null);
            if (fresh != null && fresh.getStatus() == ScheduledFlowConst.STATUS_RUNNING) {
                ruleService.markInvalid(fresh);
            }
            log.warn("rule {} failed (master data), reason={}, marked INVALID", rule.getId(), failReason);
        } else {
            ruleService.advanceCursor(rule, today, false);
            log.warn("rule {} failed (other), reason={}, cursor advanced", rule.getId(), failReason);
        }
    }

    // =====================================================================
    // 辅助
    // =====================================================================

    private static boolean isMasterDataError(int code) {
        return code == ErrorCode.ACCOUNT_DISABLED.getCode()
                || code == ErrorCode.TYPE_DISABLED.getCode()
                || code == ErrorCode.TYPE_ARCHIVED.getCode()
                || code == ErrorCode.TYPE_HAS_CHILDREN.getCode()
                || code == ErrorCode.ACCOUNT_NOT_FOUND.getCode()
                || code == ErrorCode.TYPE_NOT_FOUND.getCode()
                || code == ErrorCode.ACTION_NOT_FOUND.getCode();
    }

    private static LocalTime parseRunTime(String s) {
        // HH:mm 或 HH:mm:ss
        String[] parts = s.split(":");
        int h = Integer.parseInt(parts[0]);
        int m = Integer.parseInt(parts[1]);
        int sec = parts.length > 2 ? Integer.parseInt(parts[2]) : 0;
        return LocalTime.of(h, m, sec);
    }

    private static LocalDate toLocalDate(Date date) {
        if (date == null) return null;
        // 用 getTime() 兼容 java.sql.Date（Hibernate 从 DATE 列读回的就是 java.sql.Date，
        // 它重写了 toInstant() 抛 UnsupportedOperationException）
        return new java.sql.Date(date.getTime()).toLocalDate();
    }

    private static Date toDate(LocalDate localDate) {
        if (localDate == null) return null;
        return Date.from(localDate.atStartOfDay(ZoneId.systemDefault()).toInstant());
    }
}
