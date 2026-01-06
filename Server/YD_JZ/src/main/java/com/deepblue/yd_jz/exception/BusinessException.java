package com.deepblue.yd_jz.exception;

import lombok.Getter;

/**
 * 业务异常类
 * <p>
 * 用于抛出业务层的异常，由 GlobalExceptionHandler 统一捕获处理
 */
@Getter
public class BusinessException extends RuntimeException {

    private final int code;
    private final String msg;

    /**
     * 使用错误码枚举创建异常
     */
    public BusinessException(ErrorCode errorCode) {
        super(errorCode.getMessage());
        this.code = errorCode.getCode();
        this.msg = errorCode.getMessage();
    }

    /**
     * 使用错误码枚举 + 自定义消息创建异常
     */
    public BusinessException(ErrorCode errorCode, String customMessage) {
        super(customMessage);
        this.code = errorCode.getCode();
        this.msg = customMessage;
    }

    /**
     * 获取对应的 HTTP 状态码
     */
    public int getHttpStatus() {
        if (code == 401) {
            return 401;
        } else if (code == 418) {
            return 418;
        } else if (code >= 50000) {
            return 500;
        }
        return 200;
    }
}
