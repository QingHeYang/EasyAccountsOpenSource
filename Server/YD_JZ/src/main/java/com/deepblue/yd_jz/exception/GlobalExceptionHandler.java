package com.deepblue.yd_jz.exception;

import com.deepblue.yd_jz.dto.BaseDto;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * 全局异常处理器
 * <p>
 * 统一捕获并处理 Controller 层抛出的异常，返回标准化的 BaseDto 格式
 */
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    /**
     * 处理业务异常
     */
    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<BaseDto<Void>> handleBusinessException(BusinessException e) {
        log.warn("业务异常: code={}, msg={}", e.getCode(), e.getMsg());
        BaseDto<Void> response = BaseDto.setErrorBean(e.getMsg(), e.getCode());
        return ResponseEntity.status(e.getHttpStatus()).body(response);
    }

    /**
     * 处理参数校验异常（配合 @Valid 使用）
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<BaseDto<Void>> handleValidationException(MethodArgumentNotValidException e) {
        String message = e.getBindingResult().getFieldErrors().stream()
                .map(error -> error.getField() + ": " + error.getDefaultMessage())
                .findFirst()
                .orElse("参数校验失败");
        log.warn("参数校验异常: {}", message);
        BaseDto<Void> response = BaseDto.setErrorBean(message, ErrorCode.PARAM_INVALID.getCode());
        return ResponseEntity.ok(response);
    }

    /**
     * 处理非法参数异常
     */
    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<BaseDto<Void>> handleIllegalArgumentException(IllegalArgumentException e) {
        log.warn("非法参数异常: {}", e.getMessage());
        BaseDto<Void> response = BaseDto.setErrorBean(e.getMessage(), ErrorCode.PARAM_INVALID.getCode());
        return ResponseEntity.ok(response);
    }

    /**
     * 处理通用 Exception（兜底）
     * 将未捕获的异常统一转换为系统错误
     */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<BaseDto<Void>> handleException(Exception e) {
        // 从异常消息中提取有意义的信息，避免暴露敏感堆栈
        String userMessage = extractUserFriendlyMessage(e);
        log.error("系统异常: {}", e.getMessage(), e);
        BaseDto<Void> response = BaseDto.setErrorBean(userMessage, ErrorCode.SYSTEM_ERROR.getCode());
        return ResponseEntity.status(500).body(response);
    }

    /**
     * 提取用户友好的错误消息
     * 对于已知的业务异常消息直接返回，未知异常返回通用提示
     */
    private String extractUserFriendlyMessage(Exception e) {
        String message = e.getMessage();
        if (message != null && !message.isEmpty()) {
            // 如果是业务相关的消息（中文），直接返回
            if (containsChinese(message)) {
                return message;
            }
        }
        return "系统内部错误，请稍后重试";
    }

    /**
     * 判断字符串是否包含中文
     */
    private boolean containsChinese(String str) {
        if (str == null) {
            return false;
        }
        for (char c : str.toCharArray()) {
            if (Character.UnicodeScript.of(c) == Character.UnicodeScript.HAN) {
                return true;
            }
        }
        return false;
    }
}
