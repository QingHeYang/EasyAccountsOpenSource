package com.deepblue.yd_jz.controller.account;

import lombok.Data;

import java.util.Date;

@Data
public class AccountToClient {
    private int id;
    private String name;
    private String money;
    private String exemptMoney;
    private String card;
    private String createTime;
    private String note;

}
