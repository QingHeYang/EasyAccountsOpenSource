package com.deepblue.yd_jz.dao.jpa;

import com.deepblue.yd_jz.entity.ScheduledFlowLog;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface ScheduledFlowLogRepository extends JpaRepository<ScheduledFlowLog, Integer> {

    // 按规则 id 倒序查历史（规则详情页）
    Page<ScheduledFlowLog> findByRuleIdOrderByExecuteTimeDesc(Integer ruleId, Pageable pageable);

    // 全量历史倒序（独立历史页）
    Page<ScheduledFlowLog> findAllByOrderByExecuteTimeDesc(Pageable pageable);

    // 规则删除时级联清日志
    void deleteByRuleId(Integer ruleId);
}
