package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.dto.AuthDto;
import com.deepblue.yd_jz.entity.Auth;
import com.deepblue.yd_jz.utils.AuthUtils;
import lombok.extern.slf4j.Slf4j;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;

@Service
@Slf4j
public class AuthService {
    @Autowired
    private AuthUtils authUtils;
    @Value("${auth.expired}")
    private long expired;

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
                auth.refreshToken(expired);
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
        auth.refreshToken(expired);
        token = auth.getToken();
        AuthDto authDto = new AuthDto();
        authDto.setToken(token);
        auth.encode();
        authUtils.saveAuth(auth);
        return authDto;
    }


}
