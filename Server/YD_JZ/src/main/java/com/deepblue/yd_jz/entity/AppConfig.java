package com.deepblue.yd_jz.entity;

import lombok.Data;

import jakarta.persistence.*;
import java.util.Date;

// v2.7.0: 全局应用配置 k-v 表，按 domain 区分业务域
@Data
@Entity
@Table(name = "app_config")
public class AppConfig {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    // 业务域，例：scheduled_flow
    @Column(name = "domain", nullable = false, length = 50)
    private String domain;

    // 配置键，在同一 domain 下唯一
    @Column(name = "config_key", nullable = false, length = 50)
    private String configKey;

    @Column(name = "config_value", nullable = false, length = 255)
    private String configValue;

    @Column(name = "updated_at", nullable = false)
    @Temporal(TemporalType.TIMESTAMP)
    private Date updatedAt;
}
