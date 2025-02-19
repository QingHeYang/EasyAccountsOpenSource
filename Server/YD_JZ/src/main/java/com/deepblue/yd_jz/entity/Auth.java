package com.deepblue.yd_jz.entity;

import com.deepblue.yd_jz.utils.GsonUtils;
import lombok.Data;

import java.util.Base64;
import java.util.UUID;

@Data
public class Auth {
    private String token;
    private String username;
    private String passwordMD5;
    private long expireTime;
    private long createTime;

    public static Auth decode(String secretKey) {
        Base64.Decoder decoder = Base64.getDecoder();
        String authStr = new String(decoder.decode(secretKey));
        Auth auth = GsonUtils.gson.fromJson(authStr, Auth.class);
        return auth;
    }

    public String encode() {
        String authStr = GsonUtils.gson.toJson(this);
        Base64.Encoder encoder = Base64.getEncoder();
        String secretKey = encoder.encodeToString(authStr.getBytes());
        return secretKey;
    }

    public void refreshToken(long expireTime) {
        this.expireTime = System.currentTimeMillis() + expireTime*1000*60;
        this.createTime = System.currentTimeMillis();
        String token = UUID.randomUUID().toString();
        this.token = token;
    }
}
