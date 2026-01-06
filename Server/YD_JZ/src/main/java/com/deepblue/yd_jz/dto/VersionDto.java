package com.deepblue.yd_jz.dto;

import lombok.Data;

@Data
public class VersionDto {
    private Versions versions;
    private Auth auth;
    private Backup backup;

    @Data
    public static class Versions {
        private String fontBranch;
        private String backendBranch;
        private String mysqlBranch;
        private String agentBranch;
        private String webhookBranch;
        private String release;
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
