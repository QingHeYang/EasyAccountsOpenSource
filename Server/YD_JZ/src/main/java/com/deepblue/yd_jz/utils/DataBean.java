package com.deepblue.yd_jz.utils;

public class DataBean<T> {
    private int code;
    private String msg;
    private T data;

    public int getCode() {
        return code;
    }

    public void setCode(int code) {
        this.code = code;
    }

    public String getMsg() {
        return msg;
    }

    public void setMsg(String msg) {
        this.msg = msg;
    }

    public T getData() {
        return data;
    }

    public void setData(T data) {
        this.data = data;
    }

    public static DataBean setSuccessBean(){
        DataBean dataBean = new DataBean();
        dataBean.setMsg("success");
        dataBean.setCode(ContentValues.SUCCESS);
        return dataBean;
    }
}
