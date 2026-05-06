package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.dto.AuthDto;
import com.deepblue.yd_jz.entity.Auth;
import com.deepblue.yd_jz.utils.AuthUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

// v2.7.0 (config-ui): auth.expired / auth.single_login 已下沉到 app_config.auth.*，改读 AuthConfigService
@Service
@Slf4j
public class AuthService {
    @Autowired
    private AuthUtils authUtils;

    @Autowired
    private AuthConfigService authConfigService;

    public boolean verfiyAuthFiles() {
        Auth auth = authUtils.getAuth();
        if (auth != null) {
            return true;
        }
        return false;
    }


    public AuthDto login(String username, String password) {
        String token = null;
        Auth auth = authUtils.getAuth();
        if (auth != null) {
            if (auth.getUsername().equals(username)&&auth.getPasswordMD5().equals(password)) {
                long now = System.currentTimeMillis();
                long expired = authConfigService.getTokenExpiredMinutes();
                boolean singleLogin = authConfigService.isSingleLogin();

                if (!singleLogin && auth.getExpireTime() > now) {
                    // 多端模式 + Token未过期：只刷新过期时间，不换Token
                    auth.setExpireTime(now + expired * 60 * 1000);
                    log.info("多端登录模式：复用现有Token，刷新过期时间");
                } else {
                    // 单端模式 或 Token已过期：生成新Token
                    auth.refreshToken(expired);
                    if (!singleLogin) {
                        log.info("多端登录模式：Token已过期，生成新Token");
                    }
                }

                token = auth.getToken();
                AuthDto authDto = new AuthDto();
                authDto.setToken(token);
                auth.encode();
                authUtils.saveAuth(auth);
                log.debug("登录成功 user: {} ,token: {}", username, token);
                return authDto;
            }else {
                return null;
            }
        }
        return null;
    }

    public AuthDto register(String username, String password) {
        //先判断是否已经有了用户名密码
        Auth auth = authUtils.getAuth();
        if (auth != null&&auth.getUsername()!=null&&auth.getPasswordMD5()!=null) {
            return null;
        }
        String token = null;
        auth = new Auth();
        auth.setUsername(username);
        auth.setPasswordMD5(password);
        auth.refreshToken(authConfigService.getTokenExpiredMinutes());
        token = auth.getToken();
        AuthDto authDto = new AuthDto();
        authDto.setToken(token);
        auth.encode();
        authUtils.saveAuth(auth);
        return authDto;
    }


}
