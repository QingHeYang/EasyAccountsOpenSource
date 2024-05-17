package com.deepblue.yd_jz.controller.flow;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

public class FlowBaseBean {
    private String totalIn;
    private String totalOut;
    private String totalEarn;
    private List<TypeBean> typeList;

    private List<FlowInnerBean> flows;

    public String getTotalIn() {
        return totalIn;
    }

    public String getTotalEarn() {
        return totalEarn;
    }

    public void setTotalEarn(String totalEarn) {
        this.totalEarn = totalEarn;
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

    public List<FlowInnerBean> getFlows() {
        return flows;
    }

    public void setFlows(List<FlowInnerBean> flows) {
        this.flows = flows;
    }

    public List<TypeBean> getTypeList() {
        return typeList;
    }

    public void setTypeList(List<TypeBean> typeList) {
        this.typeList = typeList;
    }

    public static class FlowInnerBean {
        private int id;
        private String tName;
        private String money;
        private boolean exempt;
        private boolean collect;
        private int handle;
        private String hName;
        private String note;
        private String aName;
        private String toAName;
        private String fDate;

        public String getNote() {
            return note;
        }

        public void setNote(String note) {
            this.note = note;
        }

        public boolean isCollect() {
            return collect;
        }

        public void setCollect(boolean collect) {
            this.collect = collect;
        }



        public int getId() {
            return id;
        }

        public void setId(int id) {
            this.id = id;
        }

        public String gettName() {
            return tName;
        }

        public void settName(String tName) {
            this.tName = tName;
        }

        public String getMoney() {
            return money;
        }

        public void setMoney(String money) {
            this.money = money;
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

        public String gethName() {
            return hName;
        }

        public void sethName(String hName) {
            this.hName = hName;
        }

        public String getaName() {
            return aName;
        }

        public void setaName(String aName) {
            this.aName = aName;
        }

        public String getToAName() {
            return toAName;
        }

        public void setToAName(String toAName) {
            this.toAName = toAName;
        }

        public String getfDate() {
            return fDate;
        }

        public void setfDate(String fDate) {
            this.fDate = fDate;
        }
    }


    public static class TypeBean{
        private String typeName;
        private String money;
        private int typeId;
        private boolean parent;
        private List<TypeBean> children;

        public String getTypeName() {
            return typeName;
        }

        public void setTypeName(String typeName) {
            this.typeName = typeName;
        }

        public String getMoney() {
            return money;
        }

        public void setMoney(String money) {
            this.money = money;
        }

        public int getTypeId() {
            return typeId;
        }

        public void setTypeId(int typeId) {
            this.typeId = typeId;
        }

        public boolean isParent() {
            return parent;
        }

        public void setParent(boolean parent) {
            this.parent = parent;
        }

        public List<TypeBean> getChildren() {
            return children;
        }

        public void setChildren(List<TypeBean> children) {
            this.children = children;
        }
    }
}
