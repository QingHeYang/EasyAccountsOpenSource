package com.deepblue.yd_jz.utils;

import okhttp3.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.File;
import java.io.IOException;

@Component
public class FileMakeWebHook {

    @Value("${webhook_url}")
    private   String WEBHOOK_URL;

    public  void sendFile(File file, String fileType, String fileName) {
        OkHttpClient client = new OkHttpClient();

        // 创建文件的请求体，类型为二进制流
        RequestBody fileBody = RequestBody.create(file, MediaType.parse("application/octet-stream"));

        // 创建请求体的多部分形式
        MultipartBody requestBody = new MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart("file", fileName, fileBody)
                .addFormDataPart("file_type", fileType)
                .addFormDataPart("file_name", fileName)
                .build();

        // 创建请求
        Request request = new Request.Builder()
                .url(WEBHOOK_URL)
                .post(requestBody)
                .build();

        try {
            Response response = client.newCall(request).execute();
            if (response.isSuccessful()) {
                System.out.println("文件上传成功：" + response.body().string());
            } else {
                System.out.println("文件上传失败：" + response.message());
            }
        } catch (IOException e) {
            System.err.println("错误: " + e.getMessage());
        }
    }
}
