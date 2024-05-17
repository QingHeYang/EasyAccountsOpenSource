package com.deepblue.yd_jz.utils;

import com.aliyun.oss.OSS;
import com.aliyun.oss.OSSClientBuilder;
import com.aliyun.oss.event.ProgressEvent;
import com.aliyun.oss.event.ProgressEventType;
import com.aliyun.oss.event.ProgressListener;
import com.aliyun.oss.model.PutObjectRequest;
import lombok.extern.slf4j.Slf4j;
import org.slf4j.Logger;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.stereotype.Component;

import java.io.File;

@Slf4j
public class OssUtils {
    String accessKeyId;

    String accessKeySecret;

    String endpoint;

    String bucketName;

    String folderKey;

    private String fileName;

    private OssUploadCallBack callBack;

    public void doUpload(File file, String folderKey, String name, OssUploadCallBack callBack) {
        this.callBack = callBack;
        this.fileName = name;
        this.folderKey = folderKey;
        OSS ossClient = new OSSClientBuilder().build(endpoint, accessKeyId, accessKeySecret);
        PutObjectRequest putObjectRequest = new PutObjectRequest(bucketName,
                folderKey + name,
                file);
        putObjectRequest.withProgressListener(new PutObjectProgressListener());
        ossClient.putObject(putObjectRequest);
        ossClient.shutdown();
    }

    public class PutObjectProgressListener implements ProgressListener {
        private long bytesWritten = 0;
        private long totalBytes = -1;
        private boolean succeed = false;

        @Override
        public void progressChanged(ProgressEvent progressEvent) {
            long bytes = progressEvent.getBytes();
            ProgressEventType eventType = progressEvent.getEventType();
            int lastpercent = 0;
            switch (eventType) {
                case TRANSFER_STARTED_EVENT:
                    log.info("Start to upload......");
                    break;
                case REQUEST_CONTENT_LENGTH_EVENT:
                    this.totalBytes = bytes;
                    log.info(this.totalBytes + " bytes in total will be uploaded to OSS");
                    break;
                case REQUEST_BYTE_TRANSFER_EVENT:
                    this.bytesWritten += bytes;
                    if (this.totalBytes != -1) {
                        int percent = (int) (this.bytesWritten * 100.0 / this.totalBytes);
                        if (percent != lastpercent) {
                            lastpercent = percent;
                        }
                    } else {
                        log.info(bytes + " bytes have been written at this time, upload ratio: unknown" + "(" + this.bytesWritten + "/...)");
                    }
                    break;
                case TRANSFER_COMPLETED_EVENT:
                    this.succeed = true;
                    log.info("Succeed to upload, " + this.bytesWritten + " bytes have been transferred in total");
                    callBack.onUploadSuccess("https://deep-blue-res.oss-cn-zhangjiakou.aliyuncs.com/" + folderKey + fileName);
                    break;
                case TRANSFER_FAILED_EVENT:
                    log.error("Failed to upload, " + this.bytesWritten + " bytes have been transferred");
                    callBack.onUploadFailed("Failed to upload, " + this.bytesWritten + " bytes have been transferred");
                    break;
                default:
                    break;
            }
        }

        public boolean isSucceed() {
            return succeed;
        }
    }


    public interface OssUploadCallBack {
        void onUploadSuccess(String ossUrl);

        void onUploadFailed(String msg);
    }
}
