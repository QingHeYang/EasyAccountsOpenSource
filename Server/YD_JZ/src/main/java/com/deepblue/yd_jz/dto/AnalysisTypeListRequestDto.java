package com.deepblue.yd_jz.dto;

import lombok.Data;

@Data
public class AnalysisTypeListRequestDto {
    private String start;
    private String end;
    private Boolean combineSubType;
    private Boolean showDisableAnalysisType;
}
