package com.deepblue.yd_jz.entity;

import lombok.Data;

import jakarta.persistence.*;
import java.util.Date;

// v2.7.0: 定时记账规则
@Data
@Entity
@Table(name = "scheduled_flow_rule")
public class ScheduledFlowRule {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "name", nullable = false, length = 50)
    private String name;

    // 记账字段（与 flow 对齐）
    @Column(name = "money", nullable = false, length = 20)
    private String money;

    // v2.7.0: nullable 允许为 null，失效时引用被清空
    @Column(name = "type_id", nullable = true)
    private Integer typeId;

    @Column(name = "action_id", nullable = false)
    private Integer actionId;

    // v2.7.0: nullable 允许为 null，失效时引用被清空
    @Column(name = "account_id", nullable = true)
    private Integer accountId;

    @Column(name = "account_to_id")
    private Integer accountToId;

    @Column(name = "note", length = 200)
    private String note;

    // 周期类型：1=每日 2=每周 3=每月 4=每年
    @Column(name = "cycle_type", nullable = false)
    private Integer cycleType;

    // 周期内具体日期 JSON：每日=null；每周=[1-7]；每月=[1-31]；每年=["MM-DD"]
    @Column(name = "cycle_dates", length = 255)
    private String cycleDates;

    // 执行时间 HH:mm:ss
    @Column(name = "run_time", nullable = false, length = 8)
    private String runTime;

    @Column(name = "start_date", nullable = false)
    @Temporal(TemporalType.DATE)
    private Date startDate;

    @Column(name = "end_date")
    @Temporal(TemporalType.DATE)
    private Date endDate;

    @Column(name = "is_permanent", nullable = false)
    private boolean isPermanent = false;

    // 状态：1=未开始 2=开始 3=暂停 4=完成 5=失效
    @Column(name = "status", nullable = false)
    private Integer status = 1;

    @Column(name = "next_run_date")
    @Temporal(TemporalType.DATE)
    private Date nextRunDate;

    @Column(name = "last_run_date")
    @Temporal(TemporalType.DATE)
    private Date lastRunDate;

    @Column(name = "reminder_enabled", nullable = false)
    private boolean reminderEnabled = false;

    @Column(name = "email_enabled", nullable = false)
    private boolean emailEnabled = false;

    @Column(name = "create_time", nullable = false)
    @Temporal(TemporalType.TIMESTAMP)
    private Date createTime;

    @ManyToOne(fetch = FetchType.EAGER)
    @JoinColumn(name = "account_id", insertable = false, updatable = false)
    private Account account;

    @ManyToOne(fetch = FetchType.LAZY, optional = true)
    @JoinColumn(name = "account_to_id", insertable = false, updatable = false)
    private Account accountTo;

    @ManyToOne(fetch = FetchType.EAGER)
    @JoinColumn(name = "action_id", insertable = false, updatable = false)
    private Action action;

    @ManyToOne(fetch = FetchType.EAGER)
    @JoinColumn(name = "type_id", insertable = false, updatable = false)
    private Type type;
}
