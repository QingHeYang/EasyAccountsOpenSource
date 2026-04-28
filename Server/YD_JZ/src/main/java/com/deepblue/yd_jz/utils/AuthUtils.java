package com.deepblue.yd_jz.utils;

import com.deepblue.yd_jz.entity.Auth;
import com.deepblue.yd_jz.service.AuthConfigService;
import lombok.extern.slf4j.Slf4j;
import okio.Okio;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;

// v2.7.0 (config-ui): auth.enable / auth.expired 已下沉到 app_config.auth.*，改读 AuthConfigService
// auth.folder 仍走 env（部署级路径常量）
@Slf4j
@Component
public class AuthUtils {

    private static final Object FILE_LOCK = new Object();

    @Value("${auth.folder}")
    private String authFolder;

    @Autowired
    private AuthConfigService authConfigService;

    public int isAuth(String token) {
        if (!authConfigService.isLoginEnable()) {
            return 200;
        }
        if (token == null) {
            return isFileExist() ? 401 : 418;
        }
        return isTokenValid(token);
    }

    private boolean isFileExist() {
        String keyFile = authFolder + "/secret.key";
        File file = new File(keyFile);
        return file.exists();
    }

    private int isTokenValid(String token) {
        File file = new File(authFolder + "/secret.key");
        synchronized (FILE_LOCK) {
            try {
                String key = Okio.buffer(Okio.source(file)).readUtf8();
                Auth auth = Auth.decode(key);
                if (auth == null) {
                    return 418;
                }
                long currentTime = System.currentTimeMillis();
                if (auth.getToken().equals(token) && auth.getExpireTime() > currentTime) {
                    // 滑动刷新：只在剩余时间 < 50% 时才刷新
                    long expiredMinutes = authConfigService.getTokenExpiredMinutes();
                    long totalDuration = expiredMinutes * 60 * 1000;
                    long remainingTime = auth.getExpireTime() - currentTime;
                    if (remainingTime < totalDuration / 2) {
                        long newExpireTime = currentTime + totalDuration;
                        auth.setExpireTime(newExpireTime);
                        saveAuth(auth);
                        log.info("Token 滑动刷新: 剩余{}分钟, 新过期时间 {}",
                                remainingTime / 60000, new java.util.Date(newExpireTime));
                    }
                    return 200;
                } else {
                    return 401;
                }
            } catch (IOException e) {
                log.error("Error reading key file: {}", e.getMessage());
                return 418;
            }
        }
    }

    public Auth getAuth() {
        File file = new File(authFolder + "/secret.key");
        try {
            String key = Okio.buffer(Okio.source(file)).readUtf8();
            return Auth.decode(key);
        } catch (IOException e) {
            log.error("Error reading key file: {}", e.getMessage());
            return null;
        }
    }

    public void saveAuth(Auth auth) {
        File file = new File(authFolder + "/secret.key");
        try {
            Okio.buffer(Okio.sink(file)).writeUtf8(auth.encode()).close();
        } catch (FileNotFoundException e) {
            log.error("Error writing key file: {}", e.getMessage());
        } catch (IOException e) {
            log.error("Error writing key file: {}", e.getMessage());
        }
    }
}
