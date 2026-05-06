package com.deepblue.yd_jz.dto;

import lombok.Data;

// v2.7.0 (config-ui): 认证配置更新请求；null=不修改
@Data
public class AuthConfigUpdateDto {
    private Boolean loginEnable;             // 是否启用登录功能
    private Boolean singleLogin;             // true=单端，false=多端
    private Integer tokenExpiredMinutes;     // Token 过期分钟数
}
