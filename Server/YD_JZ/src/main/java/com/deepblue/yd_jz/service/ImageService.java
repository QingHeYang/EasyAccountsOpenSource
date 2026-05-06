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
     * 删除流水的图片关联（仅 DB，不删磁盘文件）
     * 给 updateFlow 的"先删后加"使用：删掉旧关联但保留磁盘文件，
     * 因为新关联可能复用同一批 fileName（用户编辑时未改图片）
     */
    @Transactional
    public void deleteFlowImages(Integer flowId) {
        flowImageRepository.deleteByFlowId(flowId);
    }

    /**
     * 删除流水关联 + 物理清理被遗弃的磁盘文件
     * 给 doDeleteFlow 使用：流水彻底删除时，关联的图片也不再有任何引用
     */
    @Transactional
    public void deleteFlowImagesAndFiles(Integer flowId) {
        List<FlowImage> existing = flowImageRepository.findByFlowId(flowId);
        flowImageRepository.deleteByFlowId(flowId);
        for (FlowImage img : existing) {
            deleteImageFileQuietly(img.getImageName());
        }
    }

    /**
     * updateFlow 时按 diff 清理被移除的图片：
     * - 旧关联里有但新关联里没有 → DB + 磁盘都清
     * - 都有的（复用）→ 不动
     */
    @Transactional
    public void replaceFlowImages(Integer flowId, List<String> newImageNames) {
        List<FlowImage> oldImages = flowImageRepository.findByFlowId(flowId);
        Set<String> retained = (newImageNames == null) ? Collections.emptySet()
                : new HashSet<>(newImageNames);

        flowImageRepository.deleteByFlowId(flowId);

        // 旧的 - 新的 = 被移除的，删磁盘
        for (FlowImage img : oldImages) {
            if (!retained.contains(img.getImageName())) {
                deleteImageFileQuietly(img.getImageName());
            }
        }

        if (newImageNames != null) {
            saveFlowImages(flowId, newImageNames);
        }
    }

    /**
     * 物理删除单个图片文件，失败仅记日志
     * 仅允许在 uploadPath 之下，防止异常 fileName 造成误删
     */
    private void deleteImageFileQuietly(String fileName) {
        if (fileName == null || fileName.isEmpty()) {
            return;
        }
        try {
            File baseDir = new File(uploadPath).getCanonicalFile();
            File target = new File(baseDir, fileName).getCanonicalFile();
            if (!target.toPath().startsWith(baseDir.toPath())) {
                log.warn("拒绝删除越界路径文件: {}", fileName);
                return;
            }
            if (target.exists() && target.isFile() && !target.delete()) {
                log.warn("图片文件删除失败: {}", target.getAbsolutePath());
            }
        } catch (IOException e) {
            log.warn("图片文件删除异常 fileName={}: {}", fileName, e.getMessage());
        }
    }

    /**
     * 获取流水的图片列表
     */
    public List<FlowImage> getFlowImages(Integer flowId) {
        return flowImageRepository.findByFlowId(flowId);
    }
}