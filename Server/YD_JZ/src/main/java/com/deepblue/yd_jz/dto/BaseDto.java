package com.deepblue.yd_jz.dto;

import lombok.Data;

@Data
public class BaseDto<T> {
    private int code;
    private String msg;
    private T data;

    // 定义一些常用的状态码，如成功的状态码
    public static final int SUCCESS = 0;
    public static final int NOT_FOUND = 404;
    public static final int SERVER_ERROR = 500;

    // 成功时设置 DataBean
    public static <T> BaseDto<T> setSuccessBean() {
        BaseDto<T> baseDto = new BaseDto<>();
        baseDto.setMsg("Success");
        baseDto.setCode(SUCCESS);
        return baseDto;
    }

    // 错误时设置 DataBean，需要传入错误信息和错误码
    public static <T> BaseDto<T> setErrorBean(String errorMessage, int errorCode) {
        BaseDto<T> baseDto = new BaseDto<>();
        baseDto.setMsg(errorMessage);
        baseDto.setCode(errorCode);
        return baseDto;
    }
}
