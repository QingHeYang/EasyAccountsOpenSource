package com.deepblue.yd_jz.service;
import com.deepblue.yd_jz.entity.TemplateTag;
import com.deepblue.yd_jz.dao.jpa.TemplateTagRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class TagService {
    @Autowired
    private FlowTemplateService flowTemplateService;

    @Autowired
    private TemplateTagRepository templateTagRepository;

    @Transactional(rollbackFor = Exception.class)
    public TemplateTag addTag(TemplateTag templateTag) {
        templateTag.setId(null);
        return templateTagRepository.save(templateTag);
    }

    @Transactional(rollbackFor = Exception.class)
    public TemplateTag getTagById(Integer id) {
        return templateTagRepository.findById(id).orElse(null);
    }

    @Transactional(rollbackFor = Exception.class)
    public List<TemplateTag> getAllTags() {
        return templateTagRepository.findAll();
    }

    @Transactional(rollbackFor = Exception.class)
    public TemplateTag updateTag(TemplateTag templateTag) {
        return templateTagRepository.save(templateTag); // save 方法同时用于插入和更新
    }

    @Transactional(rollbackFor = Exception.class)
    public void deleteTag(Integer id) {
        templateTagRepository.deleteById(id);
        flowTemplateService.clearTag(id);
    }
}
