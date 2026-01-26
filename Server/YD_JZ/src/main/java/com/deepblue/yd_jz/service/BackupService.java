package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.exception.BusinessException;
import com.deepblue.yd_jz.exception.ErrorCode;
import com.deepblue.yd_jz.utils.LogUtils;
import com.deepblue.yd_jz.utils.FileMakeWebHook;
import com.deepblue.yd_jz.utils.FileUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.text.SimpleDateFormat;
import java.util.Date;

/**
 * 数据库备份恢复服务
 * 用于重新部署时恢复数据
 */
@Slf4j
@Service
public class BackupService {

    @Value("${sqlBackUpFolder}")
    private String backupFolder;

    @Value("${sqldumpCmd}")
    private String dumpCmd;

    @Value("${sqlRestoreCmd}")
    private String restoreCmd;

    @Value("${sqlDropCreateCmd:}")
    private String dropCreateCmd;

    @Value("${system.os:ubuntu}")
    private String systemOs;

    @Autowired
    private FileMakeWebHook fileMakeWebHook;

    /**
     * 根据操作系统构建命令
     * win: cmd /c command
     * ubuntu: /bin/sh -c command
     */
    private String[] buildCommand(String command) {
        if ("win".equalsIgnoreCase(systemOs)) {
            return new String[]{"cmd", "/c", command};
        } else {
            return new String[]{"/bin/sh", "-c", command};
        }
    }

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

        // 3. 先删除并重建数据库（确保清空所有表，包括新版本添加的表）
        if (dropCreateCmd != null && !dropCreateCmd.isEmpty()) {
            LogUtils.log_print("清空数据库...");
            String[] dropCmd = buildCommand(dropCreateCmd);

            try {
                Process dropProcess = Runtime.getRuntime().exec(dropCmd);

                // 捕获错误输出
                StringBuilder dropError = new StringBuilder();
                try (BufferedReader reader = new BufferedReader(new InputStreamReader(dropProcess.getErrorStream()))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        dropError.append(line).append("\n");
                    }
                }

                int dropExitCode = dropProcess.waitFor();
                if (dropExitCode != 0) {
                    String errorMsg = dropError.toString().trim();
                    log.error("清空数据库失败，退出码: {}, 错误: {}", dropExitCode, errorMsg);
                    throw new BusinessException(ErrorCode.SYSTEM_ERROR, "清空数据库失败: " + (errorMsg.isEmpty() ? "退出码 " + dropExitCode : errorMsg));
                }
                LogUtils.log_print("数据库已清空");
            } catch (BusinessException e) {
                throw e;
            } catch (Exception e) {
                log.error("清空数据库异常", e);
                throw new BusinessException(ErrorCode.SYSTEM_ERROR, "清空数据库失败: " + e.getMessage());
            }
        }

        // 4. 执行恢复命令
        LogUtils.log_print("开始恢复数据库\n文件: " + filePath);
        // 文件路径可能包含空格，需要用引号包裹
        String[] cmd = buildCommand(restoreCmd + "\"" + filePath + "\"");

        try {
            Process process = Runtime.getRuntime().exec(cmd);

            // 捕获错误输出
            StringBuilder errorOutput = new StringBuilder();
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getErrorStream()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    errorOutput.append(line).append("\n");
                }
            }

            int exitCode = process.waitFor();

            if (exitCode != 0) {
                String errorMsg = errorOutput.toString().trim();
                log.error("数据库恢复失败，退出码: {}, 错误: {}", exitCode, errorMsg);
                throw new BusinessException(ErrorCode.SYSTEM_ERROR, "恢复失败: " + (errorMsg.isEmpty() ? "退出码 " + exitCode : errorMsg));
            }

            LogUtils.log_print("数据库恢复成功: " + originalName);
            log.info("数据库恢复成功: {}", originalName);

            // 5. 延迟重启服务，让 Liquibase 补齐表结构
            LogUtils.log_print("服务将在 3 秒后重启，Liquibase 将自动补齐表结构...");
            new Thread(() -> {
                try {
                    Thread.sleep(3000);
                    log.info("正在重启服务...");
                    System.exit(0);  // Docker restart: always 会自动重启
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            }).start();

        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            log.error("数据库恢复异常", e);
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "恢复失败: " + e.getMessage());
        }
    }

    /**
     * 手动备份数据库
     * @return 备份文件名
     */
    public String backup() {
        // 1. 生成文件名（manual 标识手动备份）
        SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd_HHmm");
        String fileName = "yd_jz_manual_" + sdf.format(new Date()) + ".sql";

        // 2. 确保目录存在
        File folder = new File(backupFolder);
        if (!folder.exists()) {
            folder.mkdirs();
        }

        String filePath = backupFolder + fileName;

        // 3. 执行备份命令
        LogUtils.log_print("开始手动备份数据库\n文件: " + filePath);
        // 文件路径可能包含空格，需要用引号包裹
        String[] cmd = buildCommand(dumpCmd + "\"" + filePath + "\"");

        try {
            Process process = Runtime.getRuntime().exec(cmd);

            // 捕获错误输出
            StringBuilder errorOutput = new StringBuilder();
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getErrorStream()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    errorOutput.append(line).append("\n");
                }
            }

            int exitCode = process.waitFor();

            if (exitCode != 0) {
                String errorMsg = errorOutput.toString().trim();
                log.error("数据库备份失败，退出码: {}, 错误: {}", exitCode, errorMsg);
                throw new BusinessException(ErrorCode.SYSTEM_ERROR, "备份失败: " + (errorMsg.isEmpty() ? "退出码 " + exitCode : errorMsg));
            }

            // 4. 检查文件是否生成并发送 WebHook
            if (FileUtils.isExist(filePath)) {
                fileMakeWebHook.sendFile(new File(filePath), "sql", fileName);
                LogUtils.log_print("数据库备份成功: " + fileName);
                log.info("数据库备份成功: {}", fileName);
            } else {
                throw new BusinessException(ErrorCode.SYSTEM_ERROR, "备份失败，文件未生成");
            }

            return fileName;

        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            log.error("数据库备份异常", e);
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "备份失败: " + e.getMessage());
        }
    }
}
