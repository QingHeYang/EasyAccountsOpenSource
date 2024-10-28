package com.deepblue.yd_jz.entity;

import com.deepblue.yd_jz.entity.Action;
import javax.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "type")
@Data       // Lombok annotation to generate getters, setters, toString, equals, and hashCode methods
@NoArgsConstructor  // Generates no-args constructor
public class Type {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private int id;

    @Column(name = "t_name", nullable = false, length = 50)
    private String tName;

    @Column(name = "parent", nullable = true)
    private Integer parent = -1;  // Default is -1

    @Column(name = "t_disable", nullable = true)
    private boolean disable = false;  // Default is false

    @Column(name = "has_child", nullable = true)
    private boolean hasChild = false;  // Default is false

    @Column(name = "archive", nullable = true)
    private Boolean archive = false;  // Nullable Boolean field

    @Column(name = "action_id", nullable = true)
    private Integer actionId;  // Foreign key relation, could link to an 'Action' entity

    // If there is a foreign key relation to 'Action' entity
    @ManyToOne(fetch = FetchType.EAGER)
    @JoinColumn(name = "action_id", insertable = false, updatable = false)
    private Action action;  // Entity relationship
}

