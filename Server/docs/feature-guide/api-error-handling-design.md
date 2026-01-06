# API 错误处理体系设计方案

## 1. 现状分析

### 1.1 当前问题

| 问题 | 描述 | 影响 |
|------|------|------|
| 无全局异常处理器 | 没有 @ControllerAdvice | 未捕获异常返回 Spring Boot 默认 500 错误页 |
| 直接 throws Exception | Controller 方法声明 `throws Exception` | 异常响应格式不统一，全部变成 HTTP 500 |
| 无自定义异常类 | 所有异常都是 `new Exception(msg)` | 无法区分业务异常和系统异常 |
| 状态码混乱 | code 字段和 HTTP status 混用 | 客户端难以判断错误类型 |

### 1.2 当前异常处理方式

**Controller 层：**
```java
// 模式 A: 直接 throws（最常见，问题最大）
@PostMapping("/addFlow")
public BaseDto<FlowIdResponseDto> addFlow(...) throws Exception {
    int id = flowService.doAddFlow(flowAddRequestDto);  // 异常未处理
    return baseDto;
}

// 模式 B: 手动返回错误（AuthController）
if (authDto == null) {
    return BaseDto.setErrorBean("用户名或密码错误", 401);
}

// 模式 C: try-catch（ImageController，较规范）
try {
    // 业务逻辑
} catch (Exception e) {
    log.error("上传图片失败", e);
    return BaseDto.setErrorBean("上传失败: " + e.getMessage(), 500);
}
```

**Service 层：**
```java
// 业务校验抛出异常
if (subTypes != null && !subTypes.isEmpty()) {
    throw new Exception("该分类有子分类，请选择子分类记账");
}
```

### 1.3 现有状态码（保留不变）

| 状态码 | 含义 | 使用场景 |
|--------|------|----------|
| **401** | 未授权/登录失败 | Token 过期、用户名密码错误 |
| **418** | 需要注册 | 未找到认证文件 |

---

## 2. 设计目标

1. **统一响应格式**：所有 API 返回 `BaseDto` 格式
2. **HTTP 状态码规范**：业务异常返回 HTTP 200，系统异常返回对应 HTTP 状态码
3. **业务错误码规范**：通过 `code` 字段区分具体错误类型
4. **向后兼容**：保留现有 401、418 认证状态码
5. **最小改动**：复用现有 `BaseDto`，新增异常处理层

---

## 3. 错误码规范

### 3.1 错误码分层设计

```
┌─────────────────────────────────────────────────────────┐
│  HTTP Status Code（传输层）                              │
│  - 200: 请求成功（包括业务失败）                          │
│  - 401: 未认证                                          │
│  - 418: 需要注册                                        │
│  - 500: 系统异常                                        │
├─────────────────────────────────────────────────────────┤
│  BaseDto.code（业务层）                                  │
│  - 0: 成功                                              │
│  - 4xxxx: 客户端错误（参数、权限、资源）                  │
│  - 5xxxx: 服务端错误                                    │
└─────────────────────────────────────────────────────────┘
```

### 3.2 业务错误码定义

#### 成功

| code | 说明 |
|------|------|
| 0 | 操作成功 |

#### 参数校验错误 (40xxx)

| code | 说明 | 示例 |
|------|------|------|
| 40001 | 参数不能为空 | 必填字段未传 |
| 40002 | 参数格式错误 | 日期格式不正确 |
| 40003 | 参数值非法 | 金额为负数 |
| 40004 | 文件校验失败 | 文件为空、格式不支持 |

#### 认证授权错误 (41xxx)

| code | 说明 | HTTP Status |
|------|------|-------------|
| 41001 | 未登录/Token 过期 | **401** |
| 41002 | 用户名或密码错误 | **401** |
| 41008 | 需要注册 | **418** |

> 注：41001、41002 对应 HTTP 401，41008 对应 HTTP 418

#### 业务规则错误 (42xxx)

| code | 说明 | 示例 |
|------|------|------|
| 42001 | 余额不足 | 支出金额 > 账户余额 |
| 42002 | 分类校验失败 | 父分类有子分类，不允许直接记账 |
| 42003 | 操作不允许 | 删除有子分类的父分类 |
| 42004 | 数据冲突 | 名称重复 |
| 42005 | 状态不正确 | 账户已禁用 |

#### 资源不存在错误 (44xxx)

| code | 说明 | 示例 |
|------|------|------|
| 44001 | 账户不存在 | accountId 无效 |
| 44002 | 分类不存在 | typeId 无效 |
| 44003 | 流水不存在 | flowId 无效 |
| 44004 | 模板不存在 | templateId 无效 |
| 44005 | 文件不存在 | 图片/Excel 文件不存在 |

#### 系统错误 (50xxx)

| code | 说明 | HTTP Status |
|------|------|-------------|
| 50001 | 系统内部错误 | **500** |
| 50002 | 数据库错误 | **500** |
| 50003 | 文件操作错误 | **500** |
| 50004 | 外部服务调用失败 | **500** |

### 3.3 HTTP 状态码与业务码映射

| HTTP Status | 使用场景 | BaseDto.code |
|-------------|----------|--------------|
| **200** | 业务成功或业务失败 | 0 或 4xxxx |
| **401** | 认证失败 | 41001, 41002 |
| **418** | 需要注册 | 41008 |
| **500** | 系统异常 | 50xxx |

**设计原则：**
- 业务异常（参数错误、规则校验失败、资源不存在）→ HTTP 200 + 业务错误码
- 认证异常 → HTTP 401/418 + 业务错误码
- 系统异常（数据库错误、未知异常）→ HTTP 500 + 业务错误码

---

## 4. 实现方案

### 4.1 新增文件清单

| 文件 | 说明 |
|------|------|
| `exception/ErrorCode.java` | 错误码枚举 |
| `exception/BusinessException.java` | 业务异常类 |
| `exception/GlobalExceptionHandler.java` | 全局异常处理器 |

### 4.2 ErrorCode 枚举

```java
package com.deepblue.yd_jz.exception;

import lombok.Getter;

@Getter
public enum ErrorCode {

    // 成功
    SUCCESS(0, "操作成功"),

    // 参数校验错误 40xxx
    PARAM_REQUIRED(40001, "参数不能为空"),
    PARAM_FORMAT_ERROR(40002, "参数格式错误"),
    PARAM_INVALID(40003, "参数值非法"),
    FILE_VALIDATION_ERROR(40004, "文件校验失败"),

    // 认证授权错误 41xxx
    UNAUTHORIZED(41001, "未登录或Token已过期"),
    LOGIN_FAILED(41002, "用户名或密码错误"),
    NEED_REGISTER(41008, "需要注册"),

    // 业务规则错误 42xxx
    INSUFFICIENT_BALANCE(42001, "余额不足"),
    TYPE_HAS_CHILDREN(42002, "该分类有子分类，请选择子分类"),
    OPERATION_NOT_ALLOWED(42003, "操作不允许"),
    DATA_CONFLICT(42004, "数据冲突"),
    INVALID_STATE(42005, "状态不正确"),

    // 资源不存在错误 44xxx
    ACCOUNT_NOT_FOUND(44001, "账户不存在"),
    TYPE_NOT_FOUND(44002, "分类不存在"),
    FLOW_NOT_FOUND(44003, "流水不存在"),
    TEMPLATE_NOT_FOUND(44004, "模板不存在"),
    FILE_NOT_FOUND(44005, "文件不存在"),

    // 系统错误 50xxx
    SYSTEM_ERROR(50001, "系统内部错误"),
    DATABASE_ERROR(50002, "数据库错误"),
    FILE_OPERATION_ERROR(50003, "文件操作错误"),
    EXTERNAL_SERVICE_ERROR(50004, "外部服务调用失败");

    private final int code;
    private final String message;

    ErrorCode(int code, String message) {
        this.code = code;
        this.message = message;
    }

    /**
     * 获取对应的 HTTP 状态码
     */
    public int getHttpStatus() {
        if (code == 41001 || code == 41002) {
            return 401;
        } else if (code == 41008) {
            return 418;
        } else if (code >= 50000) {
            return 500;
        }
        return 200;
    }
}
```

### 4.3 BusinessException 业务异常类

```java
package com.deepblue.yd_jz.exception;

import lombok.Getter;

@Getter
public class BusinessException extends RuntimeException {

    private final int code;
    private final String msg;

    public BusinessException(ErrorCode errorCode) {
        super(errorCode.getMessage());
        this.code = errorCode.getCode();
        this.msg = errorCode.getMessage();
    }

    public BusinessException(ErrorCode errorCode, String customMessage) {
        super(customMessage);
        this.code = errorCode.getCode();
        this.msg = customMessage;
    }

    /**
     * 获取对应的 HTTP 状态码
     */
    public int getHttpStatus() {
        if (code == 41001 || code == 41002) {
            return 401;
        } else if (code == 41008) {
            return 418;
        } else if (code >= 50000) {
            return 500;
        }
        return 200;
    }
}
```

### 4.4 GlobalExceptionHandler 全局异常处理器

```java
package com.deepblue.yd_jz.exception;

import com.deepblue.yd_jz.dto.BaseDto;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

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
     * 处理通用 Exception（兜底）
     * 将未捕获的异常统一转换为系统错误
     */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<BaseDto<Void>> handleException(Exception e) {
        log.error("系统异常: ", e);
        BaseDto<Void> response = BaseDto.setErrorBean(
            "系统内部错误，请稍后重试",
            ErrorCode.SYSTEM_ERROR.getCode()
        );
        return ResponseEntity.status(500).body(response);
    }

    /**
     * 处理参数校验异常（配合 @Valid 使用）
     */
    @ExceptionHandler(org.springframework.web.bind.MethodArgumentNotValidException.class)
    public ResponseEntity<BaseDto<Void>> handleValidationException(
            org.springframework.web.bind.MethodArgumentNotValidException e) {
        String message = e.getBindingResult().getFieldErrors().stream()
            .map(error -> error.getField() + ": " + error.getDefaultMessage())
            .findFirst()
            .orElse("参数校验失败");
        log.warn("参数校验异常: {}", message);
        BaseDto<Void> response = BaseDto.setErrorBean(message, ErrorCode.PARAM_INVALID.getCode());
        return ResponseEntity.ok(response);
    }
}
```

### 4.5 BaseDto 扩展（可选）

```java
// 新增便捷方法
public static <T> BaseDto<T> error(ErrorCode errorCode) {
    return setErrorBean(errorCode.getMessage(), errorCode.getCode());
}

public static <T> BaseDto<T> error(ErrorCode errorCode, String customMessage) {
    return setErrorBean(customMessage, errorCode.getCode());
}
```

---

## 5. 使用示例

### 5.1 Service 层抛出业务异常

**改造前：**
```java
if (subTypes != null && !subTypes.isEmpty()) {
    throw new Exception("该分类有子分类，请选择子分类记账");
}
```

**改造后：**
```java
if (subTypes != null && !subTypes.isEmpty()) {
    throw new BusinessException(ErrorCode.TYPE_HAS_CHILDREN, "该分类有子分类，请选择子分类记账");
}
```

### 5.2 Controller 层简化

**改造前：**
```java
@PostMapping("/addFlow")
public BaseDto<FlowIdResponseDto> addFlow(@RequestBody FlowAddRequestDto dto) throws Exception {
    int id = flowService.doAddFlow(dto);
    BaseDto<FlowIdResponseDto> baseDto = BaseDto.setSuccessBean();
    baseDto.setData(new FlowIdResponseDto(id));
    return baseDto;
}
```

**改造后：**
```java
@PostMapping("/addFlow")
public BaseDto<FlowIdResponseDto> addFlow(@RequestBody FlowAddRequestDto dto) {
    // 移除 throws Exception，异常由全局处理器捕获
    int id = flowService.doAddFlow(dto);
    BaseDto<FlowIdResponseDto> baseDto = BaseDto.setSuccessBean();
    baseDto.setData(new FlowIdResponseDto(id));
    return baseDto;
}
```

### 5.3 API 响应示例

**成功响应：**
```json
{
    "code": 0,
    "msg": "Success",
    "data": { "id": 123 }
}
```

**业务错误（余额不足）：**
```
HTTP/1.1 200 OK

{
    "code": 42001,
    "msg": "余额不足，支出金额不能大于账户余额",
    "data": null
}
```

**认证失败：**
```
HTTP/1.1 401 Unauthorized

{
    "code": 41001,
    "msg": "未登录或Token已过期",
    "data": null
}
```

**系统错误：**
```
HTTP/1.1 500 Internal Server Error

{
    "code": 50001,
    "msg": "系统内部错误，请稍后重试",
    "data": null
}
```

---

## 6. 迁移计划

### 6.1 阶段一：基础设施（优先级：高）

1. 创建 `ErrorCode` 枚举
2. 创建 `BusinessException` 类
3. 创建 `GlobalExceptionHandler` 全局异常处理器
4. 扩展 `BaseDto` 便捷方法

### 6.2 阶段二：核心业务改造（优先级：高）

优先改造高频使用的 Service：

| 文件 | 改造内容 |
|------|----------|
| `FlowService.java` | 余额校验、分类校验异常 |
| `AccountService.java` | 账户不存在异常 |
| `TypeService.java` | 分类不存在、删除校验异常 |

### 6.3 阶段三：Controller 简化（优先级：中）

移除 Controller 方法的 `throws Exception` 声明。

### 6.4 阶段四：其他 Service 改造（优先级：低）

逐步改造其他 Service，替换 `throw new Exception()` 为 `throw new BusinessException()`。

---

## 7. 文件变更清单

| 操作 | 文件路径 |
|------|----------|
| 新增 | `exception/ErrorCode.java` |
| 新增 | `exception/BusinessException.java` |
| 新增 | `exception/GlobalExceptionHandler.java` |
| 修改 | `dto/BaseDto.java` |
| 修改 | `service/FlowService.java` |
| 修改 | `service/AccountService.java` |
| 修改 | `service/TypeService.java` |
| 修改 | `controller/FlowController.java` |
| ... | 其他 Controller 和 Service |

---

## 8. 注意事项

1. **保持 401/418 不变**：TokenInterceptor 的认证逻辑保持现状
2. **渐进式迁移**：不需要一次性改完所有代码，可以逐步替换
3. **日志规范**：业务异常用 `log.warn`，系统异常用 `log.error`
4. **敏感信息**：错误消息不要暴露敏感信息（如 SQL、堆栈）

---

## 9. 参考资料

- [Spring Boot 异常处理最佳实践](https://spring.io/blog/2013/11/01/exception-handling-in-spring-mvc)
- [RESTful API 错误处理规范](https://www.rfc-editor.org/rfc/rfc7807)
