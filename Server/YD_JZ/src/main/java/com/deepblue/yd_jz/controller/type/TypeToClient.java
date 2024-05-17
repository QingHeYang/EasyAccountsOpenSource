package com.deepblue.yd_jz.controller.type;

import com.deepblue.yd_jz.dao.type.Type;

import java.util.List;

public class TypeToClient {
    private int id;
    private String tName;
    private Integer parent;
    private List<TypeToClient> childrenTypes;

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

    public Integer getParent() {
        return parent;
    }

    public void setParent(Integer parent) {
        this.parent = parent;
    }

    public List<TypeToClient> getChildrenTypes() {
        return childrenTypes;
    }

    public void setChildrenTypes(List<TypeToClient> childrenTypes) {
        this.childrenTypes = childrenTypes;
    }
}
