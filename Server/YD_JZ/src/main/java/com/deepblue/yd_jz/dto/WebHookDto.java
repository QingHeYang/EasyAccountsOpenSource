package com.deepblue.yd_jz.dto;

import lombok.Data;

@Data
public class WebHookDto {
    private String status;
    private String result;
    private String message;
}
