package com.deepblue.yd_jz.utils;

public class BasePageBean<T> {
    private int pageSize;
    private int pageNum;
    private int allNum;
    T pageBean;

    public int getPageSize() {
        return pageSize;
    }

    public void setPageSize(int pageSize) {
        this.pageSize = pageSize;
    }

    public int getPageNum() {
        return pageNum;
    }

    public void setPageNum(int pageNum) {
        this.pageNum = pageNum;
    }

    public int getAllNum() {
        return allNum;
    }

    public void setAllNum(int allNum) {
        this.allNum = allNum;
    }

    public T getPageBean() {
        return pageBean;
    }

    public void setPageBean(T pageBean) {
        this.pageBean = pageBean;
    }
}
