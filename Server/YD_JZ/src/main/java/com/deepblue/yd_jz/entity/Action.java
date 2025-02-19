package com.deepblue.yd_jz.entity;

import lombok.Data;

import javax.persistence.*;


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

}
