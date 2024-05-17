package com.deepblue.yd_jz.dao.flow;

import lombok.Data;

import java.math.BigDecimal;

@Data
public class FlowType {
    private int id;
    private String tName;
    private int parent;
    private BigDecimal money;  // 考虑到money处理，更改为BigDecimal
    private String parentName; // 新增父类别名称字段
}
