package com.deepblue.yd_jz.dao.jpa;

import com.deepblue.yd_jz.entity.ScheduledFlowRule;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.Date;
import java.util.List;

@Repository
public interface ScheduledFlowRuleRepository extends JpaRepository<ScheduledFlowRule, Integer> {

    // 扫描器：找 status=开始 且 next_run_date <= 指定日期 的规则
    @Query("SELECT r FROM ScheduledFlowRule r " +
           "WHERE r.status = :status AND r.nextRunDate <= :date")
    List<ScheduledFlowRule> findDueRules(Integer status, Date date);

    // 提醒扫描：找 status=开始、reminder_enabled=1、next_run_date = 指定日期
    @Query("SELECT r FROM ScheduledFlowRule r " +
           "WHERE r.status = :status AND r.reminderEnabled = true AND r.nextRunDate = :date")
    List<ScheduledFlowRule> findRulesForReminder(Integer status, Date date);

    // 主数据失效挂钩：按账户 id 查引用规则（含 account_to_id）
    @Query("SELECT r FROM ScheduledFlowRule r " +
           "WHERE r.status = :status AND (r.accountId = :accountId OR r.accountToId = :accountId)")
    List<ScheduledFlowRule> findActiveRulesByAccountId(Integer status, Integer accountId);

    // 主数据失效挂钩：按分类 id 查引用规则
    @Query("SELECT r FROM ScheduledFlowRule r " +
           "WHERE r.status = :status AND r.typeId = :typeId")
    List<ScheduledFlowRule> findActiveRulesByTypeId(Integer status, Integer typeId);

    // 启动时兜底：所有 status=开始 的规则（启动扫描会顺便推所有过期游标）
    List<ScheduledFlowRule> findByStatus(Integer status);
}
