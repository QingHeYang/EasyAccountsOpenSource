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
    
    // v2.7.0: 文件名白名单：字母数字 + . _ -，长度 ≤ 100（与 DB 列长度一致）
    // 后端生成的 fileName 形如 "1714123456_8923.jpg"，不会含 / \ : ..
    // 此正则用于挡住任何客户端构造的恶意 fileName
    private static final java.util.regex.Pattern SAFE_FILENAME =
            java.util.regex.Pattern.compile("^[A-Za-z0-9._-]{1,100}$");

    @Operation(summary = "获取图片")
    @GetMapping("/{fileName}")
    public ResponseEntity<Resource> getImage(@PathVariable String fileName) {
        try {
            // 1. 字符白名单：禁止任何路径分隔符 / .. 等
            if (fileName == null || !SAFE_FILENAME.matcher(fileName).matches()) {
                log.warn("拒绝非法 fileName: {}", fileName);
                return ResponseEntity.notFound().build();
            }

            // 2. 路径规范化：确保最终路径在 uploadPath 之下，挡住 URL 解码后的越界
            File baseDir = new File(uploadPath).getCanonicalFile();
            File target = new File(baseDir, fileName).getCanonicalFile();
            if (!target.toPath().startsWith(baseDir.toPath())) {
                log.warn("拒绝越界路径访问: {} -> {}", fileName, target.getAbsolutePath());
                return ResponseEntity.notFound().build();
            }
            if (!target.exists() || !target.isFile()) {
                return ResponseEntity.notFound().build();
            }

            Resource resource = new FileSystemResource(target);

            // 根据文件扩展名设置Content-Type
            String contentType = "image/jpeg";
            String lower = fileName.toLowerCase();
            if (lower.endsWith(".png")) {
                contentType = "image/png";
            } else if (lower.endsWith(".gif")) {
                contentType = "image/gif";
            } else if (lower.endsWith(".webp")) {
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