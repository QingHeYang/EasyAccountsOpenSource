package com.deepblue.yd_jz.utils;

import com.deepblue.yd_jz.dto.VersionDto;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.support.CronExpression;
import org.springframework.stereotype.Component;

@Component
public class VersionUtils {

    @Value("${version.font_branch}")
    private String fontBranch;

    @Value("${version.backend_branch}")
    private String backendBranch;

    @Value("${version.mysql_branch}")
    private String mysqlBranch;

    @Value("${version.agent_branch}")
    private String agentBranch;

    @Value("${version.webhook_branch}")
    private String webhookBranch;

    @Value("${version.release}")
    private String release;

    @Value("${auth.enable:false}")
    private Boolean authEnable;

    @Value("${auth.expired:30}")
    private Integer authExpired;

    @Value("${auth.single_login:true}")
    private Boolean authSingleLogin;

    @Value("${cron.sqlBackupTime:}")
    private String cronSqlBackupTime;

    public VersionDto getVersion() {
        VersionDto versionDto = new VersionDto();

        // 版本信息
        VersionDto.Versions versions = new VersionDto.Versions();
        versions.setFontBranch(fontBranch);
        versions.setBackendBranch(backendBranch);
        versions.setMysqlBranch(mysqlBranch);
        versions.setAgentBranch(agentBranch);
        versions.setWebhookBranch(webhookBranch);
        versions.setRelease(release);
        versionDto.setVersions(versions);

        // 登录配置
        VersionDto.Auth auth = new VersionDto.Auth();
        auth.setEnable(authEnable);
        auth.setExpiredMinutes(authExpired);
        auth.setSingleLogin(authSingleLogin);
        versionDto.setAuth(auth);

        // 备份配置
        VersionDto.Backup backup = new VersionDto.Backup();
        backup.setCron(cronSqlBackupTime);
        if (cronSqlBackupTime == null || cronSqlBackupTime.trim().isEmpty()) {
            backup.setValid(false);
            backup.setDescription("未配置备份时间");
        } else {
            try {
                CronExpression.parse(cronSqlBackupTime);
                backup.setValid(true);
                backup.setDescription("已配置自动备份");
            } catch (IllegalArgumentException e) {
                backup.setValid(false);
                backup.setDescription("cron表达式无效: " + e.getMessage());
            }
        }
        versionDto.setBackup(backup);

        return versionDto;
    }
}
