package com.deepblue.yd_jz.dto;

import lombok.Data;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

@Data
public class AnalysisTypeListResponseDto {
    private String totalIn;
    private String totalOut;
    private List<TypeBean> showInTypeList;
    private List<TypeBean> showOutTypeList;

    private List<TypeBean> allInTypeList;
    private List<TypeBean> allOutTypeList;

    @Data
    public static class TypeBean{
        private int id;
        private int parentId;
        private String name;
        private String money;
        private float percent;

    }

}
