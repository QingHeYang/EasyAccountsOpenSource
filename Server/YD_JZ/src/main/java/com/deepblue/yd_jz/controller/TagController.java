package com.deepblue.yd_jz.controller;

import com.deepblue.yd_jz.entity.TemplateTag;
import com.deepblue.yd_jz.service.TagService;
import com.deepblue.yd_jz.dto.BaseDto;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Slf4j
@RestController
@Api(value = "TagController", tags = {"模板标签管理"})
@RequestMapping("/tag")
public class TagController {
    @Autowired
    TagService tagService;

    @ApiOperation(value = "添加标签")
    @PostMapping("/addTag")
    public BaseDto addTag(@RequestBody TemplateTag templateTag) {
        tagService.addTag(templateTag);
        return BaseDto.setSuccessBean();
    }

    @ApiOperation(value = "更新标签")
    @PutMapping("/updateTag")
    public BaseDto updateTag( @RequestBody TemplateTag templateTagDetails) {
        TemplateTag existingTemplateTag = tagService.getTagById(templateTagDetails.getId());
        if (existingTemplateTag != null) {
            existingTemplateTag.setName(templateTagDetails.getName());
            existingTemplateTag.setColor(templateTagDetails.getColor());
            tagService.updateTag(existingTemplateTag);
            return BaseDto.setSuccessBean();
        }
        return BaseDto.setErrorBean("Tag not found", BaseDto.NOT_FOUND);
    }

    @ApiOperation(value = "获取全部标签")
    @GetMapping("/getTags")
    public BaseDto<List<TemplateTag>> getTags() {
        List<TemplateTag> templateTags = tagService.getAllTags();
        BaseDto<List<TemplateTag>> baseDto = BaseDto.setSuccessBean();
        baseDto.setData(templateTags);
        return baseDto;
    }

    @ApiOperation(value = "获取指定标签")
    @GetMapping("/getTag/{id}")
    public BaseDto<TemplateTag> getTag(@PathVariable int id) {
        TemplateTag templateTag = tagService.getTagById(id);
        if (templateTag != null) {
            BaseDto<TemplateTag> baseDto = BaseDto.setSuccessBean();
            baseDto.setData(templateTag);
            return baseDto;
        }
        return BaseDto.setErrorBean("Tag not found", BaseDto.NOT_FOUND);
    }

    @ApiOperation(value = "停用标签")
    @DeleteMapping("/deleteTag/{id}")
    public BaseDto deleteTag(@PathVariable int id) {
        TemplateTag existingTemplateTag = tagService.getTagById(id);
        if (existingTemplateTag != null) {
            tagService.deleteTag(id);
            return BaseDto.setSuccessBean();
        }
        return BaseDto.setErrorBean("Tag not found", BaseDto.NOT_FOUND);
    }
}
