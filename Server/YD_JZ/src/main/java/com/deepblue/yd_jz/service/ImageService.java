package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.entity.FlowImage;
import com.deepblue.yd_jz.dao.jpa.FlowImageRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.transaction.annotation.Transactional;

import java.io.File;
import java.io.IOException;
import java.util.*;

@Service
@Slf4j
public class ImageService {
    
    @Autowired
    private FlowImageRepository flowImageRepository;
    
    @Value("${image.upload.path:/Ledger/images/}")
    private String uploadPath;
    
    /**
     * 上传图片
     */
    public String uploadImage(MultipartFile file) throws IOException {
        // 确保上传目录存在
        File uploadDir = new File(uploadPath);
        if (!uploadDir.exists()) {
            uploadDir.mkdirs();
        }
        
        // 生成唯一文件名
        String originalName = file.getOriginalFilename();
        if (originalName == null || originalName.isEmpty()) {
            throw new IOException("文件名不能为空");
        }
        
        String extension = "";
        int lastDot = originalName.lastIndexOf(".");
        if (lastDot > 0) {
            extension = originalName.substring(lastDot);
        }
        
        String fileName = System.currentTimeMillis() + "_" + 
                         (int)(Math.random() * 10000) + extension;
        
        // 保存文件
        File destFile = new File(uploadPath + fileName);
        file.transferTo(destFile);
        
        log.info("图片上传成功: {}", fileName);
        return fileName;
    }
    
    /**
     * 保存流水图片关联
     */
    @Transactional
    public void saveFlowImages(Integer flowId, List<String> imageNames) {
        if (imageNames == null || imageNames.isEmpty()) {
            return;
        }
        
        for (String imageName : imageNames) {
            if (imageName != null && !imageName.trim().isEmpty()) {
                FlowImage flowImage = new FlowImage();
                flowImage.setFlowId(flowId);
                flowImage.setImageName(imageName);
                flowImage.setUploadTime(new Date());
                flowImageRepository.save(flowImage);
            }
        }
    }
    
    /**
     * 删除流水的图片关联
     */
    @Transactional
    public void deleteFlowImages(Integer flowId) {
        flowImageRepository.deleteByFlowId(flowId);
    }
}