package com.deepblue.yd_jz.entity;

import lombok.Data;
import javax.persistence.*;

@Data
@Entity
@Table(name = "flow_template")
public class FlowTemplate {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "name", nullable = false)
    private String name;

    @Column(name = "date_type", nullable = true)
    private Integer dateType;

    @Column(name = "money", nullable = true)
    private String money;

    @Column(name = "type_id", nullable = true)
    private Integer typeId;

    @Column(name = "action_id", nullable = true)
    private Integer actionId;

    @Column(name = "account_id", nullable = true)
    private Integer accountId;

    @Column(name = "account_to_id", nullable = true)
    private Integer accountToId;


    @Column(name = "tag_id", nullable = true)
    private Integer tagId;

    @ManyToOne(fetch = FetchType.EAGER)
    @JoinColumn(name = "account_id", insertable = false, updatable = false)
    private Account account;

    @ManyToOne(fetch = FetchType.EAGER)
    @JoinColumn(name = "account_to_id", insertable = false, updatable = false)
    private Account accountTo;

    @ManyToOne(fetch = FetchType.EAGER)
    @JoinColumn(name = "action_id", insertable = false, updatable = false)
    private Action action;

    @ManyToOne(fetch = FetchType.EAGER)
    @JoinColumn(name = "type_id", insertable = false, updatable = false)
    private Type type;

    @ManyToOne(fetch = FetchType.EAGER)
    @JoinColumn(name = "tag_id", insertable = false, updatable = false)
    private TemplateTag tag;
}
