package com.deepblue.yd_jz.utils;

import lombok.extern.slf4j.Slf4j;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.Map;

// v2.7.0: 薄层封装 —— 通知类消息推送到 WebHook
// 与 FileMakeWebHook 区别：FileMakeWebHook 发文件，这里发纯文本通知
@Slf4j
@Component
public class NotificationWebHook {

    private static final MediaType JSON = MediaType.parse("application/json; charset=utf-8");

    @Value("${webhook_url}")
    private String webhookUrl;

    /**
     * 发送邮件通知
     * 失败只记 warn，不抛异常（邮件失败不应影响站内通知）
     */
    public void sendEmail(String subject, String body) {
        if (webhookUrl == null || webhookUrl.trim().isEmpty()) {
            log.debug("webhook_url 未配置，跳过邮件发送");
            return;
        }

        Map<String, String> payload = new HashMap<>();
        payload.put("type", "email");
        payload.put("subject", subject);
        payload.put("body", body);
        String json = GsonUtils.gson.toJson(payload);

        try {
            OkHttpClient client = new OkHttpClient();
            Request request = new Request.Builder()
                    .url(webhookUrl)
                    .post(RequestBody.create(json, JSON))
                    .build();
            try (Response response = client.newCall(request).execute()) {
                if (!response.isSuccessful()) {
                    log.warn("notification webhook 返回非 2xx: {}", response.code());
                }
            }
        } catch (Exception e) {
            log.warn("notification webhook 调用失败: {}", e.getMessage());
        }
    }
}
