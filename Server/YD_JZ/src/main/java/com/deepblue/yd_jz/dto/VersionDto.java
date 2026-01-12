package com.deepblue.yd_jz.dto;

import lombok.Data;

@Data
public class VersionDto {
    private Versions versions;
    private Auth auth;
    private Backup backup;
    private Update update;  // v2.6.0: 版本更新信息

    @Data
    public static class Versions {
        private String fontBranch;
        private String backendBranch;
        private String mysqlBranch;
        private String agentBranch;
        private String webhookBranch;
        private String release;
        private Integer versionCode;  // v2.6.0: 版本码
    }

    // v2.6.0: 版本更新信息
    @Data
    public static class Update {
        private String version;
        private Integer versionCode;
        private String releaseDate;
        private String changelog;
    }

    @Data
    public static class Auth {
        private Boolean enable;
        private Integer expiredMinutes;
        private Boolean singleLogin;
    }

    @Data
    public static class Backup {
        private String cron;
        private Boolean valid;
        private String description;
    }
}
