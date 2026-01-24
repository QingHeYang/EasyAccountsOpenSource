package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.exception.BusinessException;
import com.deepblue.yd_jz.exception.ErrorCode;
import com.deepblue.yd_jz.utils.LogUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;

/**
 * 数据库备份恢复服务
 * 用于重新部署时恢复数据
 */
@Slf4j
@Service
public class BackupService {

    @Value("${sqlBackUpFolder}")
    private String backupFolder;

    @Value("${sqlRestoreCmd}")
    private String restoreCmd;

    /**
     * 上传并恢复数据库
     * @param file 用户上传的 SQL 备份文件
     */
    public void uploadAndRestore(MultipartFile file) {
        // 1. 校验文件
        if (file == null || file.isEmpty()) {
            throw new BusinessException(ErrorCode.PARAM_ERROR, "请上传备份文件");
        }

        String originalName = file.getOriginalFilename();
        if (originalName == null || !originalName.endsWith(".sql")) {
            throw new BusinessException(ErrorCode.PARAM_ERROR, "请上传 .sql 格式的备份文件");
        }

        // 2. 保存文件到备份目录
        File folder = new File(backupFolder);
        if (!folder.exists()) {
            folder.mkdirs();
        }

        String filePath = backupFolder + originalName;
        File destFile = new File(filePath);

        try {
            file.transferTo(destFile);
            LogUtils.log_print("备份文件已上传: " + filePath);
        } catch (IOException e) {
            log.error("文件保存失败", e);
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "文件保存失败: " + e.getMessage());
        }

        // 3. 执行恢复命令
        LogUtils.log_print("开始恢复数据库\n文件: " + filePath);
        String[] cmd = new String[]{"/bin/sh", "-c", restoreCmd + filePath};

        try {
            Process process = Runtime.getRuntime().exec(cmd);
            int exitCode = process.waitFor();

            if (exitCode != 0) {
                log.error("数据库恢复失败，退出码: {}", exitCode);
                throw new BusinessException(ErrorCode.SYSTEM_ERROR, "恢复失败，退出码: " + exitCode);
            }

            LogUtils.log_print("数据库恢复成功: " + originalName);
            log.info("数据库恢复成功: {}", originalName);

        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            log.error("数据库恢复异常", e);
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "恢复失败: " + e.getMessage());
        }
    }
}
