package com.deepblue.yd_jz.entity;

import lombok.Data;
import org.hibernate.annotations.NotFound;
import org.hibernate.annotations.NotFoundAction;

import jakarta.persistence.*;
import java.util.Date;

// v2.7.0: 定时记账执行日志（每次调度写一条）
@Data
@Entity
@Table(name = "scheduled_flow_log")
public class ScheduledFlowLog {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "rule_id", nullable = false)
    private Integer ruleId;

    @Column(name = "execute_time", nullable = false)
    @Temporal(TemporalType.TIMESTAMP)
    private Date executeTime;

    @Column(name = "success", nullable = false)
    private boolean success;

    // 成功时关联 flow.id
    @Column(name = "flow_id")
    private Integer flowId;

    // 失败分类：1=主数据类（账户停用/分类停用或归档）2=其他类；成功为 null
    @Column(name = "fail_category")
    private Integer failCategory;

    @Column(name = "fail_reason", length = 500)
    private String failReason;

    // v2.7.0: 规则删除后日志保留，此时 rule_id 指向已不存在的记录，@NotFound IGNORE 让关联返回 null 而非抛异常
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "rule_id", insertable = false, updatable = false)
    @NotFound(action = NotFoundAction.IGNORE)
    private ScheduledFlowRule rule;

    @ManyToOne(fetch = FetchType.LAZY, optional = true)
    @JoinColumn(name = "flow_id", insertable = false, updatable = false)
    @NotFound(action = NotFoundAction.IGNORE)
    private FlowJpaEntity flow;
}
