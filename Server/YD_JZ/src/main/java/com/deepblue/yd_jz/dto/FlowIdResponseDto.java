package com.deepblue.yd_jz.dto;

import lombok.Data;

@Data
public class FlowIdResponseDto {
    private int id;

    public FlowIdResponseDto(int id) {
        this.id = id;
    }
}
