package com.deepblue.yd_jz.data;

import com.deepblue.yd_jz.data.MonthExcelData;

import java.util.ArrayList;
import java.util.List;

public class ScreenExcelData {

    private String date;
    private String totalIn;
    private String totalOut;
    private String totalEarn;
    private String name;

    private List<MonthExcelData.Flow> flow;

    public String getDate() {
        return date;
    }

    public void setDate(String date) {
        this.date = date;
    }

    public String getTotalIn() {
        return totalIn;
    }

    public void setTotalIn(String totalIn) {
        this.totalIn = totalIn;
    }

    public String getTotalOut() {
        return totalOut;
    }

    public void setTotalOut(String totalOut) {
        this.totalOut = totalOut;
    }

    public String getTotalEarn() {
        return totalEarn;
    }

    public void setTotalEarn(String totalEarn) {
        this.totalEarn = totalEarn;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public List<MonthExcelData.Flow> getFlow() {
        return flow==null?new ArrayList<>():flow;
    }

    public void setFlow(List<MonthExcelData.Flow> flow) {
        this.flow = flow;
    }
}
