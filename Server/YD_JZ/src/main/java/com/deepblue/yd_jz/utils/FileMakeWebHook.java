package com.deepblue.yd_jz.utils;

import com.deepblue.yd_jz.dto.WebHookDto;
import okhttp3.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.File;
import java.io.IOException;

@Component
public class FileMakeWebHook {

    @Value("${webhook_url}")
    private   String WEBHOOK_URL;

    public  String sendFile(File file, String fileType, String fileName) {
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
                String result = response.body().string();
                WebHookDto webHookDto = GsonUtils.gson.fromJson(result, WebHookDto.class);
                if (!"ok".equals(webHookDto.getStatus())) {
                    return "\n调用webhook失败：\n" + webHookDto.getMessage()+"|1";
                }else {
                    return "\n调用webhook成功\n"+webHookDto.getResult()+"|0";
                }
            } else {
                System.out.println("文件上传失败：" + response.message());
                return "\n调用webhook失败：\n" + response.message()+"|1";
            }
        } catch (IOException e) {
            return "\n上传文件失败：\n" + e.getMessage()+"|1";
        }
    }
}
