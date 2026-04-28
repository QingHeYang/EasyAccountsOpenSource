package com.deepblue.yd_jz.utils;

import com.deepblue.yd_jz.dto.VersionDto;
import com.deepblue.yd_jz.service.AuthConfigService;
import com.deepblue.yd_jz.service.BackupConfigService;
import com.google.gson.Gson;
import com.google.gson.JsonObject;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
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

    @Value("${version.release}")
    private String release;

    @Value("${version.code:0}")
    private Integer versionCode;

    @Value("${version.notice.url:}")
    private String versionNoticeUrl;

    // v2.7.0 (config-ui): auth.* / cron.sqlBackupTime 已下沉到 app_config，改读 ConfigService
    @Autowired
    private AuthConfigService authConfigService;

    @Autowired
    private BackupConfigService backupConfigService;

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
        versions.setRelease(release);
        versions.setVersionCode(versionCode);
        versionDto.setVersions(versions);

        // 登录配置（v2.7.0: 来自 app_config.auth.*）
        VersionDto.Auth auth = new VersionDto.Auth();
        auth.setEnable(authConfigService.isLoginEnable());
        auth.setExpiredMinutes(authConfigService.getTokenExpiredMinutes());
        auth.setSingleLogin(authConfigService.isSingleLogin());
        versionDto.setAuth(auth);

        // 备份配置（v2.7.0: 来自 app_config.backup.*；BackupConfigService.get() 已校验合法性）
        VersionDto.Backup backup = new VersionDto.Backup();
        try {
            String cron = backupConfigService.getCron();
            backup.setCron(cron);
            backup.setValid(backupConfigService.isEnabled());
            backup.setDescription(backupConfigService.isEnabled() ? "已配置自动备份" : "自动备份已关闭");
        } catch (Exception e) {
            backup.setCron("");
            backup.setValid(false);
            backup.setDescription("备份配置非法：" + e.getMessage());
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
