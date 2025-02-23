package com.deepblue.yd_jz.dto;

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

    public String getMoney() {
        return money;
    }

    public void setMoney(String money) {
        this.money = money;
    }

    public String getfDate() {
        return fDate;
    }

    public void setfDate(String fDate) {
        this.fDate = fDate;
    }

    public String getCreateDate() {
        return createDate;
    }

    public void setCreateDate(String createDate) {
        this.createDate = createDate;
    }

    public int getActionId() {
        return actionId;
    }

    public void setActionId(int actionId) {
        this.actionId = actionId;
    }

    public int getAccountId() {
        return accountId;
    }

    public void setAccountId(int accountId) {
        this.accountId = accountId;
    }

    public int getAccountToId() {
        return accountToId;
    }

    public void setAccountToId(int accountToId) {
        this.accountToId = accountToId;
    }

    public int getTypeId() {
        return typeId;
    }

    public void setTypeId(int typeId) {
        this.typeId = typeId;
    }

    public boolean isCollect() {
        return isCollect;
    }

    public void setCollect(boolean collect) {
        isCollect = collect;
    }

    public String getNote() {
        return note;
    }

    public void setNote(String note) {
        this.note = note;
    }

    @Override
    public String toString() {
        return "FlowAddRequestDto{" +
                "money='" + money + '\'' +
                ", fDate='" + fDate + '\'' +
                ", createDate='" + createDate + '\'' +
                ", actionId=" + actionId +
                ", accountId=" + accountId +
                ", accountToId=" + accountToId +
                ", typeId=" + typeId +
                ", isCollect=" + isCollect +
                ", note='" + note + '\'' +
                '}';
    }
}
