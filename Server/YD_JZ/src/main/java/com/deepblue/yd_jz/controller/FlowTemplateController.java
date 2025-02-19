package com.deepblue.yd_jz.controller;

import com.deepblue.yd_jz.dto.BaseDto;
import com.deepblue.yd_jz.dto.FlowTemplateRequestDto;
import com.deepblue.yd_jz.dto.FlowTemplateResponseDto;
import com.deepblue.yd_jz.service.FlowTemplateService;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Slf4j
@RestController
@Api(value = "FlowTemplateController", tags = {"快记模板"})
@RequestMapping("/template")
public class FlowTemplateController {
    @Autowired
    private FlowTemplateService flowTemplateService;

    @ApiOperation(value = "添加模板", notes = "添加模板")
    @PostMapping("/addTemplate")
    public BaseDto addTemplate(@RequestBody FlowTemplateRequestDto flowTemplateRequestDto) {
        log.info("addTemplate");
        flowTemplateService.addTemplate(flowTemplateRequestDto);
        log.info("flowTemplateRequestDto:{}", flowTemplateRequestDto);
        return BaseDto.setSuccessBean();
    }

    @ApiOperation(value = "更新模板", notes = "更新模板")
    @PutMapping("/updateTemplate")
    public BaseDto updateTemplate(@RequestBody FlowTemplateRequestDto flowTemplateRequestDto) {
        log.info("updateTemplate");
        flowTemplateService.updateTemplate(flowTemplateRequestDto);
        log.info("flowTemplateRequestDto:{}", flowTemplateRequestDto);
        return BaseDto.setSuccessBean();
    }

    @ApiOperation(value = "获取全部模板", notes = "获取全部模板")
    @GetMapping("/getAllTemplates")
    public BaseDto<List<FlowTemplateResponseDto>> getAllTemplates() {
        log.info("getAllTemplates");
        List<FlowTemplateResponseDto> flowTemplateResponseList = flowTemplateService.getAllTemplates();
        log.info("flowTemplateResponseList:{}", flowTemplateResponseList);
        BaseDto<List<FlowTemplateResponseDto>> baseDto = new BaseDto<>();
        baseDto.setData(flowTemplateResponseList);
        return baseDto;
    }

    @ApiOperation(value = "根据TagId获取全部模板", notes = "根据TagId获取全部模板")
    @GetMapping("/getAllTemplatesByTag/{tagId}")
    public BaseDto<List<FlowTemplateResponseDto>> getAllTemplatesByTag( @PathVariable("tagId") Integer tagId) {
        log.info("getAllTemplatesByTag");
        List<FlowTemplateResponseDto> flowTemplateResponseList = flowTemplateService.getAllTemplatesByTag(tagId);
        log.info("flowTemplateResponseList:{}", flowTemplateResponseList);
        BaseDto<List<FlowTemplateResponseDto>> baseDto = new BaseDto<>();
        baseDto.setData(flowTemplateResponseList);
        return baseDto;
    }

    @ApiOperation(value = "获取单个模板", notes = "获取单个模板")
    @GetMapping("/getTemplateById/{id}")
    public BaseDto<FlowTemplateResponseDto> getTemplateById(@PathVariable("id") Integer id) {
        log.info("getTemplateById");
        FlowTemplateResponseDto flowTemplateResponseDto = flowTemplateService.getTemplateById(id);
        BaseDto<FlowTemplateResponseDto> baseDto = new BaseDto<>();
        baseDto.setData(flowTemplateResponseDto);
        return baseDto;
    }

    @ApiOperation(value = "删除模板", notes = "删除模板")
    @DeleteMapping("/deleteTemplate/{id}")
    public BaseDto deleteTemplate(@PathVariable("id") Integer id) {
        log.info("deleteTemplate");
        flowTemplateService.deleteTemplate(id);
        return BaseDto.setSuccessBean();
    }
}
