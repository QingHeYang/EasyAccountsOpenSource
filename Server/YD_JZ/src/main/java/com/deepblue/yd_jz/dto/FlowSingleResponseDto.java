package com.deepblue.yd_jz.dto;

import com.deepblue.yd_jz.entity.Account;
import com.deepblue.yd_jz.entity.Action;
import lombok.Data;

@Data
public class FlowSingleResponseDto {
    private int id;
    private String money;
    private String fDate;
    private Action action;
    private Account account;
    private Account accountTo;
    private TypeListResponseDto type;
    private boolean isCollect;
    private String note;
    private FlowLinkDto flowLinkDto;
    private boolean automatic;
}
