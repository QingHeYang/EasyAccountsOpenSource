package com.deepblue.yd_jz.dto;

import lombok.Data;

@Data
public class TypeSingleDto {
    private int id;
    private String tName;
    private Integer parent = -1;  // Default is -1
    private boolean disable = false;  // Default is false
    private Boolean archive;  // Nullable Boolean field
    private Integer actionId;  // Foreign key relation, could link to an 'Action' entity
    private Boolean analysisDisable;  // Default is false
}
