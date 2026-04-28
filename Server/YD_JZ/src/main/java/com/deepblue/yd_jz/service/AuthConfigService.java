package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.dto.AuthConfigResponseDto;
import com.deepblue.yd_jz.dto.AuthConfigUpdateDto;
import com.deepblue.yd_jz.exception.BusinessException;
import com.deepblue.yd_jz.exception.ErrorCode;
import com.deepblue.yd_jz.utils.SystemConfigConst;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

// v2.7.0 (config-ui): 认证配置语义层
// - 给 AuthService / AuthUtils / VersionUtils / TokenInterceptor 现读
// - 不缓存，每次走 DB（Phase 5 实测延迟，再考虑 Caffeine 短缓存）
@Slf4j
@Service
public class AuthConfigService {

    @Autowired
    private AppConfigService appConfigService;

    public AuthConfigResponseDto get() {
        AuthConfigResponseDto dto = new AuthConfigResponseDto();
        dto.setLoginEnable(isLoginEnable());
        dto.setSingleLogin(isSingleLogin());
        dto.setTokenExpiredMinutes(getTokenExpiredMinutes());
        return dto;
    }

    @Transactional(rollbackFor = Exception.class)
    public void update(AuthConfigUpdateDto dto) {
        if (dto == null) return;

        if (dto.getLoginEnable() != null) {
            set(SystemConfigConst.AUTH_LOGIN_ENABLE, String.valueOf(dto.getLoginEnable()));
        }
        if (dto.getSingleLogin() != null) {
            set(SystemConfigConst.AUTH_SINGLE_LOGIN, String.valueOf(dto.getSingleLogin()));
        }
        if (dto.getTokenExpiredMinutes() != null) {
            if (dto.getTokenExpiredMinutes() <= 0) {
                throw new BusinessException(ErrorCode.PARAM_INVALID,
                        "token_expired_minutes 必须为正整数");
            }
            set(SystemConfigConst.AUTH_TOKEN_EXPIRED_MINUTES, String.valueOf(dto.getTokenExpiredMinutes()));
        }
        log.info("auth config updated: loginEnable={}, singleLogin={}, expiredMinutes={}",
                dto.getLoginEnable(), dto.getSingleLogin(), dto.getTokenExpiredMinutes());
    }

    // ── 语义读 ─────────────────────────────────────────────

    public boolean isLoginEnable() {
        return parseBool(get(SystemConfigConst.AUTH_LOGIN_ENABLE,
                SystemConfigConst.AUTH_LOGIN_ENABLE_DEFAULT));
    }

    public boolean isSingleLogin() {
        return parseBool(get(SystemConfigConst.AUTH_SINGLE_LOGIN,
                SystemConfigConst.AUTH_SINGLE_LOGIN_DEFAULT));
    }

    public int getTokenExpiredMinutes() {
        return parseInt(get(SystemConfigConst.AUTH_TOKEN_EXPIRED_MINUTES,
                SystemConfigConst.AUTH_TOKEN_EXPIRED_MINUTES_DEFAULT), 30);
    }

    // ── helpers ────────────────────────────────────────────

    private String get(String key, String defVal) {
        String v = appConfigService.getValue(SystemConfigConst.DOMAIN_AUTH, key);
        return v == null ? defVal : v;
    }

    private void set(String key, String val) {
        appConfigService.setValue(SystemConfigConst.DOMAIN_AUTH, key, val);
    }

    private static boolean parseBool(String v) {
        return "true".equalsIgnoreCase(v);
    }

    private static int parseInt(String v, int def) {
        try { return Integer.parseInt(v); } catch (Exception e) { return def; }
    }
}
