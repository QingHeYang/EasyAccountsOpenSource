package com.deepblue.yd_jz.utils;

import com.aliyuncs.DefaultAcsClient;
import com.aliyuncs.IAcsClient;
import com.aliyuncs.dm.model.v20151123.SingleSendMailRequest;
import com.aliyuncs.dm.model.v20151123.SingleSendMailResponse;
import com.aliyuncs.exceptions.ClientException;
import com.aliyuncs.http.MethodType;
import com.aliyuncs.profile.DefaultProfile;
import com.aliyuncs.profile.IClientProfile;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

public class EmailUtils {
    String accessKeyId;

    String accessKeySecret;

    private String title,content;

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getContent() {
        return content;
    }

    public void setContent(String content) {
        this.content = content;
    }

    public void sendEmail(String fileUrl) {
        LogUtils.log_print("开始发送邮件流程");
        LogUtils.log_print(getContent(fileUrl));
       IClientProfile profile = DefaultProfile.getProfile("cn-hangzhou", accessKeyId, accessKeySecret);

        IAcsClient client = new DefaultAcsClient(profile);
        SingleSendMailRequest request = new SingleSendMailRequest();


        request.setAccountName("deep@deep-blue.cloud");
        request.setFromAlias("Deep-Blue");//发信人昵称，长度小于15个字符。
        request.setAddressType(1);//0：为随机账号 1：为发信地址
        request.setTagName("控制台创建的标签");
        request.setReplyToAddress(true);// 是否启用管理控制台中配置好回信地址（状态须验证通过），取值范围是字符串true或者false
        request.setToAddress("294133042@qq.com,775495797@qq.com");
        //可以给多个收件人发送邮件，收件人之间用逗号分开，批量发信建议使用BatchSendMailRequest方式
        //request.setToAddress("邮箱1,邮箱2");
        request.setSubject(getTitle(title));
        //如果采用byte[].toString的方式的话请确保最终转换成utf-8的格式再放入htmlbody和textbody，若编码不一致则会被当成垃圾邮件。
        //注意：文本邮件的大小限制为3M，过大的文本会导致连接超时或413错误
        request.setHtmlBody(getContent(fileUrl));
        //SDK 采用的是http协议的发信方式, 默认是GET方法，有一定的长度限制。
        //若textBody、htmlBody或content的大小不确定，建议采用POST方式提交，避免出现uri is not valid异常
        request.setMethod(MethodType.POST);
        //开启需要备案，0关闭，1开启
        //request.setClickTrace("0");
        //如果调用成功，正常返回httpResponse；如果调用失败则抛出异常，需要在异常中捕获错误异常码；错误异常码请参考对应的API文档;
        try {
            SingleSendMailResponse httpResponse = client.getAcsResponse(request);
        } catch (ClientException e) {
            e.printStackTrace();
        }
    }

    public String getTitle(String title) {
        return title;
    }

    public String getContent(String fileUrl) {
        return content+"<br>" + title + "<br>点击链接下载：<br>" + "<a href=\"" + fileUrl + "\">"+fileUrl+"</a>";
    }
}
