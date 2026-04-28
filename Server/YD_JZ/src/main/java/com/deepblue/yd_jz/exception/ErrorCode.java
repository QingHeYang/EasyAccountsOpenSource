package com.deepblue.yd_jz.exception;

import lombok.Getter;

/**
 * 统一错误码枚举
 * <p>
 * 错误码规范：
 * - 0: 成功
 * - 40xxx: 参数校验错误
 * - 41xxx: 认证授权错误（401/418 保持不变）
 * - 42xxx: 业务规则错误
 * - 44xxx: 资源不存在错误
 * - 50xxx: 系统错误
 */
@Getter
public enum ErrorCode {

    // ==================== 成功 ====================
    SUCCESS(0, "操作成功"),

    // ==================== 参数校验错误 40xxx ====================
    PARAM_ERROR(40000, "参数错误"),
    PARAM_REQUIRED(40001, "参数不能为空"),
    PARAM_FORMAT_ERROR(40002, "参数格式错误"),
    PARAM_INVALID(40003, "参数值非法"),
    FILE_VALIDATION_ERROR(40004, "文件校验失败"),

    // ==================== 认证授权错误 41xxx ====================
    // 注意：HTTP 状态码保持 401/418 不变
    UNAUTHORIZED(401, "未登录或Token已过期"),
    LOGIN_FAILED(401, "用户名或密码错误"),
    NEED_REGISTER(418, "需要注册"),

    // ==================== 业务规则错误 42xxx ====================
    INSUFFICIENT_BALANCE(42001, "余额不足"),
    TYPE_HAS_CHILDREN(42002, "该分类有子分类，请选择子分类"),
    OPERATION_NOT_ALLOWED(42003, "操作不允许"),
    DATA_CONFLICT(42004, "数据冲突"),
    INVALID_STATE(42005, "状态不正确"),
    TYPE_CANNOT_DELETE(42006, "该分类下有流水记录，无法删除"),
    ACCOUNT_CANNOT_DELETE(42007, "该账户下有流水记录，无法删除"),
    // v2.7.0: 定时记账相关业务错误
    ACCOUNT_DISABLED(42008, "账户已停用"),
    TYPE_DISABLED(42009, "分类已停用"),
    TYPE_ARCHIVED(42010, "分类已归档"),
    ILLEGAL_STATE_TRANSITION(42011, "当前状态不允许此操作"),
    INVALID_START_DATE(42012, "开始日期必须晚于今天"),
    INVALID_END_DATE(42013, "结束日期必须不早于开始日期"),
    INVALID_CYCLE_CONFIG(42014, "周期配置非法"),
    RULE_EXPIRED(42015, "规则已过结束日期，无法启动"),
    TRANSFER_ACCOUNT_REQUIRED(42016, "转账场景下必须指定目标账户"),

    // ==================== 资源不存在错误 44xxx ====================
    ACCOUNT_NOT_FOUND(44001, "账户不存在"),
    TYPE_NOT_FOUND(44002, "分类不存在"),
    FLOW_NOT_FOUND(44003, "流水不存在"),
    TEMPLATE_NOT_FOUND(44004, "模板不存在"),
    FILE_NOT_FOUND(44005, "文件不存在"),
    ACTION_NOT_FOUND(44006, "操作类型不存在"),
    // v2.7.0:
    SCHEDULED_RULE_NOT_FOUND(44007, "定时记账规则不存在"),
    NOTICE_NOT_FOUND(44008, "通知不存在"),

    // ==================== 系统错误 50xxx ====================
    SYSTEM_ERROR(50001, "系统内部错误"),
    DATABASE_ERROR(50002, "数据库错误"),
    FILE_OPERATION_ERROR(50003, "文件操作错误"),
    EXTERNAL_SERVICE_ERROR(50004, "外部服务调用失败"),
    // v2.7.0 (config-ui): 加解密相关
    CRYPTO_FAILED(50005, "加解密失败"),
    // v2.7.0 (config-ui): 启用邮件类功能时 SMTP 必须先配置完整
    MAIL_NOT_CONFIGURED(42017, "邮件 SMTP 未配置完整，无法启用邮件功能；请先在「系统设置 - 邮件」中填写服务器、发件邮箱、密码、收件人");

    private final int code;
    private final String message;

    ErrorCode(int code, String message) {
        this.code = code;
        this.message = message;
    }

    /**
     * 获取对应的 HTTP 状态码
     * - 401: 认证失败
     * - 418: 需要注册
     * - 500: 系统错误
     * - 200: 其他（业务错误）
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
