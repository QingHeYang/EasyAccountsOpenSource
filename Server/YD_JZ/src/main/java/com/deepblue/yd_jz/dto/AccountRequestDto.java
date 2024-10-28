package com.deepblue.yd_jz.dto;

import lombok.Data;

@Data
public class AccountRequestDto {

    private String name;
    private String money;
    private String exemptMoney;
    private String card;
    private String note;
}
