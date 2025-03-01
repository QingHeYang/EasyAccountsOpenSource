package com.deepblue.yd_jz.dto;

import lombok.Data;

@Data
public class FlowAddRequestDto {
    private String money;
    private String fDate;
    private String createDate;
    private int actionId;
    private int accountId;
    private int accountToId;
    private int typeId;
    private boolean isCollect;
    private String note;
    private FlowLinkDto relatedFlow;
    private boolean automatic;

    public String getfDate() {
        return fDate;
    }

    public void setfDate(String fDate) {
        this.fDate = fDate;
    }
}
