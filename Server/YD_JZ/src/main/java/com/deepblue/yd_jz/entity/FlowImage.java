package com.deepblue.yd_jz.entity;

import lombok.Data;
import javax.persistence.*;
import java.util.Date;

@Data
@Entity
@Table(name = "flow_image")
public class FlowImage {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;
    
    @Column(name = "flow_id", nullable = false)
    private Integer flowId;
    
    @Column(name = "image_name", nullable = false, length = 100)
    private String imageName;
    
    @Column(name = "upload_time")
    @Temporal(TemporalType.TIMESTAMP)
    private Date uploadTime;
}