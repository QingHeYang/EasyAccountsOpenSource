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

    // 提醒扫描：找活跃态（未开始/开始）且 reminder_enabled=1
    // next_run_date 在 [lower, upper] 区间内
    // 区间查询覆盖"用户设置 1 天后执行、3 天前提醒"这种"提醒窗口已经开启"的边界情况
    @Query("SELECT r FROM ScheduledFlowRule r " +
           "WHERE r.status IN :statuses AND r.reminderEnabled = true " +
           "AND r.nextRunDate >= :lower AND r.nextRunDate <= :upper")
    List<ScheduledFlowRule> findRulesForReminder(List<Integer> statuses, Date lower, Date upper);

    // 主数据失效挂钩：按账户 id 查所有引用规则（失效后 accountId 已置 null，天然不会再命中）
    @Query("SELECT r FROM ScheduledFlowRule r " +
           "WHERE r.accountId = :accountId OR r.accountToId = :accountId")
    List<ScheduledFlowRule> findRulesByAccountId(Integer accountId);

    // 主数据失效挂钩：按分类 id 查所有引用规则
    @Query("SELECT r FROM ScheduledFlowRule r WHERE r.typeId = :typeId")
    List<ScheduledFlowRule> findRulesByTypeId(Integer typeId);

    // 启动时兜底：所有 status=开始 的规则（启动扫描会顺便推所有过期游标）
    List<ScheduledFlowRule> findByStatus(Integer status);
}
