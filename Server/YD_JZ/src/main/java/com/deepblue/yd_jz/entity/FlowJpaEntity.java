package com.deepblue.yd_jz.entity;

import lombok.Data;

import javax.persistence.*;

@Data
@Entity
@Table(name = "flow")
public class FlowJpaEntity {
    @Id
    @GeneratedValue(strategy = javax.persistence.GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "f_date", nullable = false)
    private String fDate;

    @Column(name = "money", nullable = false)
    private String money;

    @Column(name = "type_id", nullable = false)
    private int typeId;

    @Column(name = "action_id", nullable = false)
    private int actionId;

    @Column(name = "exempt", nullable = true)
    private boolean exempt;

    @Column(name = "account_id", nullable = true)
    private int accountId;

    @Column(name = "account_to_id", nullable = true)
    private int accountToId;

    @Column(name = "note", nullable = true)
    private String note;

    @Column(name = "collect", nullable = true)
    private boolean collect;

    @Column(name = "f_create_date", nullable = true)
    private String fCreateDate;

    @Column(name = "f_disable", nullable = true)
    private boolean fDisable;

    @ManyToOne(fetch = FetchType.EAGER)
    @JoinColumn(name = "account_id", insertable = false, updatable = false)
    private Account account;

    @ManyToOne(fetch = FetchType.LAZY, optional = true)  // 设置 optional = true 允许为空，fetch 设置为 LAZY
    @JoinColumn(name = "account_to_id", insertable = false, updatable = false)
    private Account accountTo;


    @ManyToOne(fetch = FetchType.EAGER)
    @JoinColumn(name = "action_id", insertable = false, updatable = false)
    private Action action;

    @ManyToOne(fetch = FetchType.EAGER)
    @JoinColumn(name = "type_id", insertable = false, updatable = false)
    private Type type;
}
