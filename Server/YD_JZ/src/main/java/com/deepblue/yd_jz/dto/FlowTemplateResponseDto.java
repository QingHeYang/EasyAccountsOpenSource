package com.deepblue.yd_jz.dto;

import com.deepblue.yd_jz.entity.Action;
import com.deepblue.yd_jz.entity.FlowTemplate;
import com.deepblue.yd_jz.entity.TemplateTag;
import com.deepblue.yd_jz.service.TypeService;
import lombok.Data;
import org.springframework.beans.factory.annotation.Autowired;

@Data
public class FlowTemplateResponseDto {

    private Integer id;
    private String name;
    private Integer dateType;
    private String money;
    private Integer typeId;
    private Integer actionId;
    private Integer accountId;
    private Integer accountToId;
    private Integer tagId;

    private TypeListResponseDto type;
    private Action action;
    private AccountResponseDto account;
    private AccountResponseDto accountTo;
    private TemplateTag tag;

    public FlowTemplateResponseDto convertToDto(FlowTemplate flowTemplate) {
        FlowTemplateResponseDto flowTemplateResponseDto = this;
        flowTemplateResponseDto.setId(flowTemplate.getId());
        flowTemplateResponseDto.setName(flowTemplate.getName());
        flowTemplateResponseDto.setDateType(flowTemplate.getDateType());
        flowTemplateResponseDto.setMoney(flowTemplate.getMoney());
        flowTemplateResponseDto.setTypeId(flowTemplate.getTypeId());
        flowTemplateResponseDto.setActionId(flowTemplate.getActionId());
        flowTemplateResponseDto.setAccountId(flowTemplate.getAccountId());
        flowTemplateResponseDto.setAccountToId(flowTemplate.getAccountToId());
        flowTemplateResponseDto.setTagId(flowTemplate.getTagId());
        TypeListResponseDto typeListResponseDto = new TypeListResponseDto();
        flowTemplateResponseDto.setType(typeListResponseDto.convertToDto(flowTemplate.getType()));

        if (flowTemplate.getAction() == null) {
            flowTemplateResponseDto.setAction(new Action());
        }else {
            flowTemplateResponseDto.setAction(flowTemplate.getAction());
        }
        AccountResponseDto accountResponseDto = new AccountResponseDto();
        flowTemplateResponseDto.setAccount(accountResponseDto.convertToDto(flowTemplate.getAccount()));
        AccountResponseDto accountToResponseDto = new AccountResponseDto();
        flowTemplateResponseDto.setAccountTo(accountToResponseDto.convertToDto(flowTemplate.getAccountTo()));
        if (flowTemplate.getTag() == null) {
            flowTemplateResponseDto.setTag(new TemplateTag());
        }else {
            flowTemplateResponseDto.setTag(flowTemplate.getTag());
        }
        return flowTemplateResponseDto;
    }
}
