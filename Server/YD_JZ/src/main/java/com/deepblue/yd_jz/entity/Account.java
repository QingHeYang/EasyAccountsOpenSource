package com.deepblue.yd_jz.entity;

import lombok.Data;
import lombok.Getter;
import lombok.Setter;

import java.util.Date;
import jakarta.persistence.*;
import lombok.Data;

@Entity
@Table(name = "account")
@Data
public class Account {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private int id;

    @Column(name = "money", nullable = false)
    private String money;

    @Column(name = "exempt_money", nullable = false)
    private String exemptMoney;

    @Column(name = "a_name", nullable = false)
    private String aName;

    @Column(name = "card")
    private String card;

    @Column(name = "disable")
    private Boolean disable;

    @Column(name = "create_time")
    private Date createTime;

    @Column(name = "note", length = 100)
    private String note;

    // v2.6.0: 账户类型，0=资产账户，1=负债账户
    @Column(name = "account_type", nullable = false)
    private Integer accountType = 0;
}