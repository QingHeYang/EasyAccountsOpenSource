package com.deepblue.yd_jz.entity;

import lombok.Data;
import javax.persistence.*;

@Data
@Entity
@Table(name = "tag")
public class TemplateTag {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "name", nullable = false, length = 30)
    private String name;

    @Column(name = "color", nullable = false, length = 15)
    private String color;

}
