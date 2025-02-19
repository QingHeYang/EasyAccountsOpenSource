package com.deepblue.yd_jz.dto;

import com.deepblue.yd_jz.entity.FlowTemplate;
import lombok.Data;

@Data
public class FlowTemplateRequestDto {
    private Integer id;
    private String name;
    private Integer dateType;
    private String money;
    private Integer typeId;
    private Integer actionId;
    private Integer accountId;
    private Integer accountToId;
    private Integer tagId;

    public FlowTemplate convertToEntity() {
        FlowTemplate flowTemplate = new FlowTemplate();
        flowTemplate.setId(this.id);
        flowTemplate.setName(this.name);
        flowTemplate.setDateType(this.dateType);
        flowTemplate.setMoney(this.money);
        flowTemplate.setTypeId(this.typeId);
        flowTemplate.setActionId(this.actionId);
        flowTemplate.setAccountId(this.accountId);
        flowTemplate.setAccountToId(this.accountToId);
        flowTemplate.setTagId(this.tagId);
        return flowTemplate;
    }
}
