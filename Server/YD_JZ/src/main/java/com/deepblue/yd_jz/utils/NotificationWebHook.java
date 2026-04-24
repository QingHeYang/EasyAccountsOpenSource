package com.deepblue.yd_jz.utils;

import lombok.extern.slf4j.Slf4j;
import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.nio.charset.StandardCharsets;

// v2.7.0: 薄层封装 —— 通知类邮件推送到 WebHook
// 与 FileMakeWebHook 区别：FileMakeWebHook 发文件附件邮件（备份/Excel），这里发纯文本通知邮件（定时记账提醒）
//
// WebHook 端约定（/webhook multipart/form-data）：
//   file_type  = "scheduled_reminder"
//   file_name  = 邮件主题（subject）
//   file       = 邮件正文的 UTF-8 字节（当作"文件"传上去，WebHook 端解码成文本作为 body）
@Slf4j
@Component
public class NotificationWebHook {

    private static final MediaType TEXT_UTF8 =
            MediaType.parse("text/plain; charset=utf-8");

    @Value("${webhook_url}")
    private String webhookUrl;

    /**
     * 发送通知邮件
     * 失败只记 warn，不抛异常（邮件失败不应影响站内通知）
     */
    public void sendEmail(String subject, String body) {
        if (webhookUrl == null || webhookUrl.trim().isEmpty()) {
            log.debug("webhook_url 未配置，跳过邮件发送");
            return;
        }

        try {
            OkHttpClient client = new OkHttpClient();
            RequestBody fileBody = RequestBody.create(
                    body == null ? new byte[0] : body.getBytes(StandardCharsets.UTF_8),
                    TEXT_UTF8);
            MultipartBody requestBody = new MultipartBody.Builder()
                    .setType(MultipartBody.FORM)
                    .addFormDataPart("file", subject, fileBody)
                    .addFormDataPart("file_name", subject)
                    .addFormDataPart("file_type", "scheduled_reminder")
                    .build();
            Request request = new Request.Builder()
                    .url(webhookUrl)
                    .post(requestBody)
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
