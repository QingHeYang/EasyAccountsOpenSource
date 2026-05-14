package com.deepblue.yd_jz.entity;

import lombok.Data;

import jakarta.persistence.*;
import java.util.Date;

// v2.7.0: 用户信息通知（本地生成，区别于云端公告 NoticeService）
@Data
@Entity
@Table(name = "user_notice")
public class UserNotice {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    // 通知类型：1=定时记账事前提醒（预留扩展）
    @Column(name = "type", nullable = false)
    private Integer type;

    @Column(name = "title", nullable = false, length = 100)
    private String title;

    @Column(name = "content", nullable = false, length = 500)
    private String content;

    @Column(name = "related_rule_id")
    private Integer relatedRuleId;

    @Column(name = "related_run_date")
    @Temporal(TemporalType.DATE)
    private Date relatedRunDate;

    @Column(name = "is_read", nullable = false)
    private boolean isRead = false;

    @Column(name = "create_time", nullable = false)
    @Temporal(TemporalType.TIMESTAMP)
    private Date createTime;
}
