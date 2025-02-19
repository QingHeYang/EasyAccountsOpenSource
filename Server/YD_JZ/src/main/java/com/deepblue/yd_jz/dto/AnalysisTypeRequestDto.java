package com.deepblue.yd_jz.dto;

import lombok.Data;

@Data
public class AnalysisTypeRequestDto {
    private String start;
    private String end;
    private int typeId;
}
