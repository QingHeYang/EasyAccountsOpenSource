package com.deepblue.yd_jz.controller;

import com.deepblue.yd_jz.dto.BaseDto;
import com.deepblue.yd_jz.service.BackupService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

/**
 * 数据库备份恢复接口
 * 用于重新部署时恢复数据
 */
@RestController
@RequestMapping("/backup")
@Slf4j
@Tag(name = "数据库备份恢复")
public class BackupController {

    @Autowired
    private BackupService backupService;

    @Operation(summary = "上传并恢复数据库")
    @PostMapping("/restore")
    public BaseDto restore(@RequestParam("file") MultipartFile file) {
        backupService.uploadAndRestore(file);
        return BaseDto.setSuccessBean();
    }
}
