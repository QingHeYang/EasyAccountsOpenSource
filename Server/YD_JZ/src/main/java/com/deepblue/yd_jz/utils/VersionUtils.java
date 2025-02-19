package com.deepblue.yd_jz.utils;

import com.deepblue.yd_jz.dto.VersionDto;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class VersionUtils {

    @Value("${version.font_branch}")
    private String fontBranch;

    @Value("${version.backend_branch}")
    private String backendBranch;

    @Value("${version.mysql_branch}")
    private String mysqlBranch;

    @Value("${version.release}")
    private String release;


    public VersionDto getVersion() {
        VersionDto versionDto = new VersionDto();
        versionDto.setFontBranch(fontBranch);
        versionDto.setBackendBranch(backendBranch);
        versionDto.setMysqlBranch(mysqlBranch);
        versionDto.setRelease(release);
        return versionDto;
    }
}
