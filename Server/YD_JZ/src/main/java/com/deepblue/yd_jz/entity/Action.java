package com.deepblue.yd_jz.entity;

import lombok.Data;

import jakarta.persistence.*;


@Entity
@Data
@Table(name = "action")
public class Action {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private int id;

    @Column(name = "h_name", nullable = false, length = 50)
    private String hName;

    @Column(name = "exempt", nullable = true)
    private boolean exempt;

    @Column(name = "handle", nullable = false)
    private int handle;

    // v2.6.0: 内部转账exempt模式
    // 0=都不exempt，1=转出账户exempt，2=转入账户exempt，3=都exempt
    @Column(name = "exempt_mode", nullable = false)
    private Integer exemptMode = 0;

}
