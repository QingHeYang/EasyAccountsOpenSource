package com.deepblue.yd_jz.dto;

import lombok.Data;

// v2.7.0 (config-ui): 认证配置回显
@Data
public class AuthConfigResponseDto {
    private Boolean loginEnable;
    private Boolean singleLogin;
    private Integer tokenExpiredMinutes;
}
