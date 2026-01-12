package com.deepblue.yd_jz.utils;

import com.deepblue.yd_jz.dto.VersionDto;
import com.google.gson.Gson;
import com.google.gson.JsonObject;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.support.CronExpression;
import org.springframework.stereotype.Component;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

@Slf4j
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

    @Value("${version.code:0}")
    private Integer versionCode;

    @Value("${version.notice.url:}")
    private String versionNoticeUrl;

    @Value("${auth.enable:false}")
    private Boolean authEnable;

    @Value("${auth.expired:30}")
    private Integer authExpired;

    @Value("${auth.single_login:true}")
    private Boolean authSingleLogin;

    @Value("${cron.sqlBackupTime:}")
    private String cronSqlBackupTime;

    private static final Gson GSON = new Gson();
    private static final HttpClient HTTP_CLIENT = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(5))
            .build();

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
        versions.setVersionCode(versionCode);
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

        // v2.6.0: 检查云端版本更新
        VersionDto.Update update = checkUpdate();
        versionDto.setUpdate(update);

        return versionDto;
    }

    /**
     * 检查云端版本更新
     * @return 如果有新版本返回更新信息，否则返回 null
     */
    private VersionDto.Update checkUpdate() {
        if (versionNoticeUrl == null || versionNoticeUrl.trim().isEmpty()) {
            return null;
        }

        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(versionNoticeUrl))
                    .timeout(Duration.ofSeconds(5))
                    .GET()
                    .build();

            HttpResponse<String> response = HTTP_CLIENT.send(request, HttpResponse.BodyHandlers.ofString());

            if (response.statusCode() == 200) {
                JsonObject json = GSON.fromJson(response.body(), JsonObject.class);
                int remoteVersionCode = json.get("versionCode").getAsInt();

                // 本地版本码 < 云端版本码，有更新
                if (versionCode < remoteVersionCode) {
                    VersionDto.Update update = new VersionDto.Update();
                    update.setVersion(json.get("version").getAsString());
                    update.setVersionCode(remoteVersionCode);
                    update.setReleaseDate(json.get("releaseDate").getAsString());
                    update.setChangelog(json.get("changelog").getAsString());
                    return update;
                }
            }
        } catch (Exception e) {
            log.warn("检查版本更新失败: {}", e.getMessage());
        }

        return null;
    }
}
