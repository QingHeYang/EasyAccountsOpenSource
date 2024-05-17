package com.deepblue.yd_jz.dao.excel;

public class Excel {
    private int id;
    private String eDate;
    private String eName;
    private String ePath;
    private String eCondition;
    private int success;

    public int getId() {
        return id;
    }

    public void setId(int id) {
        this.id = id;
    }

    public String geteDate() {
        return eDate;
    }

    public void seteDate(String eDate) {
        this.eDate = eDate;
    }

    public String geteName() {
        return eName;
    }

    public void seteName(String eName) {
        this.eName = eName;
    }

    public String getePath() {
        return ePath;
    }

    public void setePath(String ePath) {
        this.ePath = ePath;
    }

    public String geteCondition() {
        return eCondition;
    }

    public void seteCondition(String eCondition) {
        this.eCondition = eCondition;
    }

    public int getSuccess() {
        return success;
    }

    public void setSuccess(int success) {
        this.success = success;
    }
}
