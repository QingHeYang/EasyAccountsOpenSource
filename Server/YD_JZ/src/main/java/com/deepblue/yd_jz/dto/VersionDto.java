package com.deepblue.yd_jz.dto;

import lombok.Data;

@Data
public class VersionDto {
    private String fontBranch;
    private String backendBranch;
    private String mysqlBranch;
    private String release;
}
