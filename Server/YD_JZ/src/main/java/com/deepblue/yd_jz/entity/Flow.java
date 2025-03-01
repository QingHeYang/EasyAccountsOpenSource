package com.deepblue.yd_jz.entity;

import lombok.Data;

@Data
public class Flow {
    private int id;
    private String fDate;
    private String money;
    private int typeId;
    private int actionId;
    private boolean exempt;
    private int accountId;
    private int accountToId;
    private String note;
    private boolean collect;
    private String fCreateDate;
    private int linkId;
    private int linkHandle;
    private boolean automatic;
}
