package com.deepblue.yd_jz.controller;

import com.deepblue.yd_jz.dto.BaseDto;
import com.deepblue.yd_jz.service.ImageService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/image")
@Slf4j
@Tag(name = "图片管理")
public class ImageController {
    
    @Autowired
    private ImageService imageService;
    
    @Value("${image.upload.path:/Ledger/images/}")
    private String uploadPath;
    
    @Operation(summary = "上传图片")
    @PostMapping("/upload")
    public BaseDto<Map<String, String>> uploadImage(@RequestParam("file") MultipartFile file) {
        try {
            // 参数校验
            if (file == null || file.isEmpty()) {
                BaseDto<Map<String, String>> errorDto = new BaseDto<>();
                errorDto.setCode(400);
                errorDto.setMsg("文件不能为空");
                return errorDto;
            }
            
            // 限制文件大小 (10MB)
            if (file.getSize() > 10 * 1024 * 1024) {
                BaseDto<Map<String, String>> errorDto = new BaseDto<>();
                errorDto.setCode(400);
                errorDto.setMsg("文件大小不能超过10MB");
                return errorDto;
            }
            
            // 检查文件类型
            String contentType = file.getContentType();
            if (contentType == null || !contentType.startsWith("image/")) {
                BaseDto<Map<String, String>> errorDto = new BaseDto<>();
                errorDto.setCode(400);
                errorDto.setMsg("只能上传图片文件");
                return errorDto;
            }
            
            String fileName = imageService.uploadImage(file);
            
            Map<String, String> result = new HashMap<>();
            result.put("fileName", fileName);
            
            BaseDto<Map<String, String>> response = BaseDto.setSuccessBean();
            response.setData(result);
            return response;
            
        } catch (Exception e) {
            log.error("上传图片失败", e);
            BaseDto<Map<String, String>> errorDto = new BaseDto<>();
            errorDto.setCode(500);
            errorDto.setMsg("上传失败: " + e.getMessage());
            return errorDto;
        }
    }
    
    @Operation(summary = "获取图片")
    @GetMapping("/{fileName}")
    public ResponseEntity<Resource> getImage(@PathVariable String fileName) {
        try {
            File file = new File(uploadPath + fileName);
            if (!file.exists()) {
                return ResponseEntity.notFound().build();
            }
            
            Resource resource = new FileSystemResource(file);
            
            // 根据文件扩展名设置Content-Type
            String contentType = "image/jpeg";
            if (fileName.toLowerCase().endsWith(".png")) {
                contentType = "image/png";
            } else if (fileName.toLowerCase().endsWith(".gif")) {
                contentType = "image/gif";
            } else if (fileName.toLowerCase().endsWith(".webp")) {
                contentType = "image/webp";
            }
            
            return ResponseEntity.ok()
                    .contentType(MediaType.parseMediaType(contentType))
                    .header(HttpHeaders.CONTENT_DISPOSITION, 
                           "inline; filename=\"" + fileName + "\"")
                    .body(resource);
                    
        } catch (Exception e) {
            log.error("获取图片失败: " + fileName, e);
            return ResponseEntity.notFound().build();
        }
    }
}