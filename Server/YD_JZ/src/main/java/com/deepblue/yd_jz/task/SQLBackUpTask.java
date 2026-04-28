package com.deepblue.yd_jz.task;

import com.deepblue.yd_jz.event.BackupConfigChangedEvent;
import com.deepblue.yd_jz.service.BackupConfigService;
import com.deepblue.yd_jz.service.MailService;
import com.deepblue.yd_jz.utils.FileUtils;
import com.deepblue.yd_jz.utils.LogUtils;
import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.TaskScheduler;
import org.springframework.scheduling.support.CronTrigger;
import org.springframework.stereotype.Component;

import java.io.File;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.concurrent.ScheduledFuture;

// v2.7.0 (config-ui): 数据库自动备份任务（动态调度）
//
// 改造前：@Scheduled(cron = "${cron.sqlBackupTime}")，启动期解析，改 cron 必须重启
// 改造后：
//   1. @PostConstruct 时按当前 BackupConfigService 配置首次安排
//   2. 监听 BackupConfigChangedEvent，配置变更后取消旧任务、重排
//   3. backup.enabled=false 时不安排任务
//   4. cron 表达式现读 BackupConfigService.getCron()，不缓存
@Slf4j
@Component
public class SQLBackUpTask {

    @Value("${sqlBackUpFolder}")
    private String sqlBackupFolder;

    @Value("${sqldumpCmd}")
    private String sqldumpCmd;

    @Value("${system.os:ubuntu}")
    private String systemOs;

    @Autowired
    private MailService mailService;

    @Autowired
    private BackupConfigService backupConfigService;

    @Autowired
    private TaskScheduler taskScheduler;

    private ScheduledFuture<?> currentFuture;

    @PostConstruct
    public void init() {
        schedule();
    }

    /**
     * 重排调度。BackupConfigService 改完配置后发事件触发，热生效，无需重启
     */
    @EventListener
    public synchronized void onConfigChanged(BackupConfigChangedEvent event) {
        log.info("backup config changed, rescheduling...");
        schedule();
    }

    private synchronized void schedule() {
        // 取消已有任务
        if (currentFuture != null && !currentFuture.isCancelled()) {
            currentFuture.cancel(false);
            currentFuture = null;
        }

        if (!backupConfigService.isEnabled()) {
            log.info("自动备份已关闭，未安排定时任务");
            return;
        }

        try {
            String cron = backupConfigService.getCron();
            currentFuture = taskScheduler.schedule(this::doBackup, new CronTrigger(cron));
            log.info("自动备份已安排：cron={}", cron);
        } catch (Exception e) {
            log.error("安排自动备份任务失败：{}", e.getMessage());
        }
    }

    /** 备份任务主体；既给定时调度调用，也可手动调用做测试 */
    public void doBackup() {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd_HHmm");
        String fileName = "yd_jz_" + sdf.format(new Date()) + ".sql";
        String filePath = sqlBackupFolder + fileName;
        LogUtils.log_print("开始备份sql\n未生成文件地址--------------- " + filePath);

        String[] cmd = buildCommand(sqldumpCmd + filePath);
        StringBuilder stderrBuf = new StringBuilder();
        int exitCode;
        try {
            Process p = Runtime.getRuntime().exec(cmd);
            // 读 stderr：mysqldump 错误信息走 stderr，必须读，否则 pipe 塞满子进程会挂；
            // 也避免后续判断时拿不到错误原因
            try (java.io.BufferedReader reader = new java.io.BufferedReader(
                    new java.io.InputStreamReader(p.getErrorStream()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    stderrBuf.append(line).append('\n');
                }
            }
            exitCode = p.waitFor();
        } catch (InterruptedException | IOException e) {
            log.error("执行 mysqldump 失败：{}", e.getMessage());
            Thread.currentThread().interrupt();
            return;
        }

        File backupFile = new File(filePath);
        // 三重判断：exit code、文件存在、文件非空
        // mysqldump 失败时（认证 / 网络 / 权限）shell 的 > 重定向已经创建空文件，光看"文件是否存在"会误判
        if (exitCode != 0 || !backupFile.exists() || backupFile.length() == 0) {
            log.error("SQL 备份失败：exitCode={}, fileSize={}, stderr={}",
                    exitCode,
                    backupFile.exists() ? backupFile.length() : -1,
                    stderrBuf.toString().trim());
            // 删掉 0 字节的占位文件，免得用户在备份目录里看到一堆假备份
            if (backupFile.exists() && backupFile.length() == 0) {
                if (!backupFile.delete()) {
                    log.warn("删除空备份文件失败：{}", filePath);
                }
            }
            return;
        }

        log.info("backup file ready: {} ({} bytes)", fileName, backupFile.length());
        mailService.sendSqlBackup(backupFile);
    }

    /** 根据操作系统构建命令 */
    private String[] buildCommand(String command) {
        if ("win".equalsIgnoreCase(systemOs)) {
            return new String[]{"cmd", "/c", command};
        } else {
            return new String[]{"/bin/sh", "-c", command};
        }
    }
}
