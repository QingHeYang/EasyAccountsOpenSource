package com.deepblue.yd_jz.dao.account;

import lombok.Data;
import lombok.Getter;
import lombok.Setter;

import java.util.Date;

@Data
@Getter
@Setter
public class Account {
    private int id;
    private String money;
    private String exemptMoney;
    private String aName;
    private String card;
    private boolean aDisable;
    private String createTime;

    private String note;

    public String getNote() {
        return note;
    }

    public void setNote(String note) {
        this.note = note;
    }

    public String getCreateTime() {
        return createTime;
    }

    public void setCreateTime(String createTime) {
        this.createTime = createTime;
    }

    public boolean isaDisable() {
        return aDisable;
    }

    public void setaDisable(boolean aDisable) {
        this.aDisable = aDisable;
    }

    public int getId() {
        return id;
    }

    public void setId(int id) {
        this.id = id;
    }

    public String getMoney() {
        return money;
    }

    public void setMoney(String money) {
        this.money = money;
    }

    public String getExemptMoney() {
        return exemptMoney;
    }

    public void setExemptMoney(String exemptMoney) {
        this.exemptMoney = exemptMoney;
    }

    public String getaName() {
        return aName;
    }

    public void setaName(String aName) {
        this.aName = aName;
    }

    public String getCard() {
        return card;
    }

    public void setCard(String card) {
        this.card = card;
    }
}
