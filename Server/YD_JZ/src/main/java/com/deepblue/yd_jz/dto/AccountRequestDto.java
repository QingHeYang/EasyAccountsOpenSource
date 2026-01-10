package com.deepblue.yd_jz.dto;

import lombok.Data;

@Data
public class AccountRequestDto {

    private String name;
    private String money;
    private String exemptMoney;
    private String card;
    private String note;
    // v2.6.0: 账户类型，0=资产账户，1=负债账户
    private Integer accountType;
}
