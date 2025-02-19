package com.deepblue.yd_jz.service;

import com.deepblue.yd_jz.dao.jpa.FlowTemplateRepository;
import com.deepblue.yd_jz.dto.FlowTemplateRequestDto;
import com.deepblue.yd_jz.dto.FlowTemplateResponseDto;
import com.deepblue.yd_jz.dto.TypeSingleDto;
import com.deepblue.yd_jz.entity.FlowTemplate;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;

@Service
@Slf4j
public class FlowTemplateService {
    @Autowired
    private FlowTemplateRepository flowTemplateRepository;

    @Autowired
    private TypeService typeService;

    @Transactional(rollbackFor = Exception.class)
    public List<FlowTemplateResponseDto> getAllTemplates() {
        List<FlowTemplate> templates= flowTemplateRepository.findAll();
        ArrayList<FlowTemplateResponseDto> flowTemplateResponseList= new ArrayList<>();
        for (FlowTemplate template: templates) {
            FlowTemplateResponseDto flowTemplateResponseDto = new FlowTemplateResponseDto();
            flowTemplateResponseDto = flowTemplateResponseDto.convertToDto(template);
            if (template.getType()!=null&&template.getType().getParent()!=-1){
                String parentName =  typeService.queryTypeParent(template.getTypeId()).getTName();
                flowTemplateResponseDto.getType().setTName(parentName+"/"+flowTemplateResponseDto.getType().getTName());
            }
            flowTemplateResponseList.add(flowTemplateResponseDto);
        }
        return flowTemplateResponseList;
    }

    @Transactional(rollbackFor = Exception.class)
    public List<FlowTemplateResponseDto> getAllTemplatesByTag(Integer tagId) {
        List<FlowTemplate> templates= flowTemplateRepository.findFlowTemplateByTagId(tagId);
        ArrayList<FlowTemplateResponseDto> flowTemplateResponseList= new ArrayList<>();
        for (FlowTemplate template: templates) {
            FlowTemplateResponseDto flowTemplateResponseDto = new FlowTemplateResponseDto();
            flowTemplateResponseDto = flowTemplateResponseDto.convertToDto(template);
            if (template.getType()!=null&&template.getType().getParent()!=-1){
                String parentName =  typeService.queryTypeParent(template.getTypeId()).getTName();
                flowTemplateResponseDto.getType().setTName(parentName+"/"+flowTemplateResponseDto.getType().getTName());
            }
            flowTemplateResponseList.add(flowTemplateResponseDto);
        }
        return flowTemplateResponseList;
    }

    @Transactional(rollbackFor = Exception.class)
    public FlowTemplateResponseDto getTemplateById(Integer id) {
        FlowTemplate template = flowTemplateRepository.findById(id).get();
        FlowTemplateResponseDto flowTemplateResponseDto = new FlowTemplateResponseDto();
        flowTemplateResponseDto = flowTemplateResponseDto.convertToDto(template);
        if (template.getType()!=null&&template.getType().getParent()!=-1){
            String parentName =  typeService.queryTypeParent(template.getTypeId()).getTName();
            flowTemplateResponseDto.getType().setTName(parentName+"/"+flowTemplateResponseDto.getType().getTName());
        }
        return flowTemplateResponseDto;
    }

    @Transactional(rollbackFor = Exception.class)
    public void addTemplate(FlowTemplateRequestDto flowTemplateRequestDto) {
        flowTemplateRequestDto.setId(null);
        FlowTemplate flowTemplate = flowTemplateRequestDto.convertToEntity();
        flowTemplateRepository.save(flowTemplate);
    }

    @Transactional(rollbackFor = Exception.class)
    public void updateTemplate(FlowTemplateRequestDto flowTemplateRequestDto) {
        FlowTemplate flowTemplate = flowTemplateRequestDto.convertToEntity();
        if (flowTemplate.getId() == null) {
            throw new RuntimeException("id is null");
        }else {
            FlowTemplate existingFlowTemplate = flowTemplateRepository.findById(flowTemplate.getId()).get();
            if (existingFlowTemplate == null) {
                throw new RuntimeException("FlowTemplate not found");
            }else {
                flowTemplateRepository.save(flowTemplate);
            }
        }
    }

    @Transactional(rollbackFor = Exception.class)
    public void deleteTemplate(Integer id) {
        if (!flowTemplateRepository.existsById(id)) {
            throw new RuntimeException("FlowTemplate not found");
        }
        flowTemplateRepository.deleteById(id);
    }

    @Transactional(rollbackFor = Exception.class)
    public void clearTag(Integer tagId) {
        List<FlowTemplate> templates = flowTemplateRepository.findFlowTemplateByTagId(tagId);
        for (FlowTemplate template: templates) {
            template.setTagId(null);
            flowTemplateRepository.save(template);
        }
    }

    @Transactional(rollbackFor = Exception.class)
    public void clearAction(Integer actionId) {
        List<FlowTemplate> templates = flowTemplateRepository.findFlowTemplatesByActionId(actionId);
        for (FlowTemplate template: templates) {
            template.setActionId(null);
            template.setTypeId(null);
            template.setAccountTo(null);
            flowTemplateRepository.save(template);
        }
    }

    @Transactional(rollbackFor = Exception.class)
    public void clearType(Integer typeId) {
        List<FlowTemplate> templates = flowTemplateRepository.findFlowTemplatesByTypeId(typeId);
        for (FlowTemplate template: templates) {
            template.setTypeId(null);
            flowTemplateRepository.save(template);
        }
    }

    @Transactional(rollbackFor = Exception.class)
    public void clearAccount(Integer accountId) {
        List<FlowTemplate> templates = flowTemplateRepository.findFlowTemplatesByAccountId(accountId);
        for (FlowTemplate template: templates) {
            template.setAccountId(null);
            template.setAccountTo(null);
            flowTemplateRepository.save(template);
        }
    }
}
