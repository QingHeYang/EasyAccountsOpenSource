package com.deepblue.yd_jz.dao.action;

import lombok.Data;

public class Action {
    private int id;
    private String hName;
    private boolean exempt;
    private int handle;

    public int getId() {
        return id;
    }

    public void setId(int id) {
        this.id = id;
    }

    public String gethName() {
        return hName;
    }

    public void sethName(String hName) {
        this.hName = hName;
    }

    public boolean isExempt() {
        return exempt;
    }

    public void setExempt(boolean exempt) {
        this.exempt = exempt;
    }

    public int getHandle() {
        return handle;
    }

    public void setHandle(int handle) {
        this.handle = handle;
    }
}
