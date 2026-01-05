package com.deepblue.yd_jz.utils;

import com.deepblue.yd_jz.entity.Auth;
import lombok.extern.slf4j.Slf4j;
import okio.Okio;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;

@Slf4j
@Component
public class AuthUtils {

    private static final Object FILE_LOCK = new Object();

    @Value("${auth.enable}")
    private boolean authEnable;

    @Value("${auth.folder}")
    private String authFolder;

    @Value("${auth.expired}")
    private long expired;

    public int isAuth(String token) {
        if (!authEnable) {
            return 200;
        }else {
            if(token == null) {
                if (!isFileExist()) {
                    return 418;
                }else {
                    return 401;
                }
            }else {
                return isTokenValid(token);
            }
        }
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
                //使用OKIO读取文件成为字符串
                String key = Okio.buffer(Okio.source(file)).readUtf8();
                Auth auth = Auth.decode(key);
                if (auth == null) {
                    return 418;
                }
                long currentTime = System.currentTimeMillis();
                if (auth.getToken().equals(token) && auth.getExpireTime() > currentTime) {
                    // 滑动刷新：只在剩余时间 < 50% 时才刷新
                    long totalDuration = expired * 60 * 1000;
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
            //使用OKIO读取文件成为字符串
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
            //使用OKIO写入文件
            Okio.buffer(Okio.sink(file)).writeUtf8(auth.encode()).close();
        } catch (FileNotFoundException e) {
            log.error("Error writing key file: {}", e.getMessage());
        } catch (IOException e) {
            log.error("Error writing key file: {}", e.getMessage());
        }
    }
}
