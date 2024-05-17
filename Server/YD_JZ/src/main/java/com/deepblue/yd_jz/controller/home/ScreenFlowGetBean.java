package com.deepblue.yd_jz.controller.home;

import java.util.ArrayList;

public class ScreenFlowGetBean {
    private int chooseHandle;
    private int accountId;
    private String startDate;
    private String endDate;
    private boolean isSingleMonth;
    private boolean collect;

    public boolean isCollect() {
        return collect;
    }

    public void setCollect(boolean collect) {
        this.collect = collect;
    }

    private ArrayList<Integer> actions;
    private ArrayList<Integer> types;

    public int getAccountId() {
        return accountId;
    }

    public void setAccountId(int accountId) {
        this.accountId = accountId;
    }

    public boolean isSingleMonth() {
        return isSingleMonth;
    }

    public void setSingleMonth(boolean singleMonth) {
        isSingleMonth = singleMonth;
    }

    public ArrayList<Integer> getActions() {
        return actions==null?new ArrayList<>():actions;
    }

    public void setActions(ArrayList<Integer> actions) {
        this.actions = actions;
    }

    public ArrayList<Integer> getTypes() {
        return types==null?new ArrayList<>():types;
    }

    public void setTypes(ArrayList<Integer> types) {
        this.types = types;
    }

    public int getChooseHandle() {
        return chooseHandle;
    }

    public void setChooseHandle(int chooseHandle) {
        this.chooseHandle = chooseHandle;
    }

    public String getStartDate() {
        return startDate==null?"":startDate;
    }

    public void setStartDate(String startDate) {
        this.startDate = startDate;
    }

    public String getEndDate() {
        return endDate==null?"":endDate;
    }

    public void setEndDate(String endDate) {
        this.endDate = endDate;
    }

    public boolean useTypeScreen(){
        return getTypes().size()!=0;
    }

    public boolean useActionScreen(){
        return getActions().size()!=0;
    }
}
