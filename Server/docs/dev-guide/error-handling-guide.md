# API 错误处理开发指南

## 概述

本项目使用统一的异常处理机制，通过 `GlobalExceptionHandler` 捕获所有异常并返回标准化的 `BaseDto` 格式。

---

## 核心组件

| 组件 | 路径 | 说明 |
|------|------|------|
| ErrorCode | `exception/ErrorCode.java` | 错误码枚举 |
| BusinessException | `exception/BusinessException.java` | 业务异常类 |
| GlobalExceptionHandler | `exception/GlobalExceptionHandler.java` | 全局异常处理器 |

---

## 错误码规范

```
0       - 成功
40xxx   - 参数校验错误
401     - 未登录/Token过期（HTTP 401）
418     - 需要注册（HTTP 418）
42xxx   - 业务规则错误
44xxx   - 资源不存在
50xxx   - 系统错误（HTTP 500）
```

### 常用错误码

| 错误码 | 枚举名 | 说明 |
|--------|--------|------|
| 40001 | PARAM_REQUIRED | 参数不能为空 |
| 40002 | PARAM_FORMAT_ERROR | 参数格式错误 |
| 40003 | PARAM_INVALID | 参数值非法 |
| 42001 | INSUFFICIENT_BALANCE | 余额不足 |
| 42002 | TYPE_HAS_CHILDREN | 分类有子分类 |
| 42003 | OPERATION_NOT_ALLOWED | 操作不允许 |
| 42006 | TYPE_CANNOT_DELETE | 分类有流水，无法删除 |
| 42007 | ACCOUNT_CANNOT_DELETE | 账户有流水，无法删除 |
| 44001 | ACCOUNT_NOT_FOUND | 账户不存在 |
| 44002 | TYPE_NOT_FOUND | 分类不存在 |
| 44003 | FLOW_NOT_FOUND | 流水不存在 |
| 50001 | SYSTEM_ERROR | 系统内部错误 |

---

## 使用方法

### 1. Service 层抛出业务异常

```java
import com.deepblue.yd_jz.exception.BusinessException;
import com.deepblue.yd_jz.exception.ErrorCode;

// 使用预定义消息
throw new BusinessException(ErrorCode.INSUFFICIENT_BALANCE);

// 使用自定义消息
throw new BusinessException(ErrorCode.INSUFFICIENT_BALANCE, "支出金额不能大于账户余额");
```

### 2. Controller 层（无需改动）

Controller 不需要 try-catch，异常会被 `GlobalExceptionHandler` 自动捕获：

```java
@PostMapping("/addFlow")
public BaseDto<FlowIdResponseDto> addFlow(@RequestBody FlowAddRequestDto dto) throws Exception {
    int id = flowService.doAddFlow(dto);  // 异常自动被全局处理器捕获
    BaseDto<FlowIdResponseDto> baseDto = BaseDto.setSuccessBean();
    baseDto.setData(new FlowIdResponseDto(id));
    return baseDto;
}
```

### 3. 手动返回错误响应（可选）

如果需要在 Controller 中手动返回错误：

```java
// 方式一：使用 ErrorCode
return BaseDto.error(ErrorCode.PARAM_REQUIRED);

// 方式二：使用 ErrorCode + 自定义消息
return BaseDto.error(ErrorCode.PARAM_INVALID, "金额必须大于0");

// 方式三：传统方式（仍然支持）
return BaseDto.setErrorBean("错误消息", 40001);
```

---

## 响应格式

### 成功响应

```json
{
    "code": 0,
    "msg": "Success",
    "data": { ... }
}
```

### 业务错误响应（HTTP 200）

```json
{
    "code": 42001,
    "msg": "余额不足",
    "data": null
}
```

### 认证错误响应（HTTP 401/418）

```json
{
    "code": 401,
    "msg": "未登录或Token已过期",
    "data": null
}
```

### 系统错误响应（HTTP 500）

```json
{
    "code": 50001,
    "msg": "系统内部错误，请稍后重试",
    "data": null
}
```

---

## 添加新错误码

在 `ErrorCode.java` 中添加新的枚举值：

```java
// 在对应分类下添加
// 业务规则错误 42xxx
INSUFFICIENT_BALANCE(42001, "余额不足"),
TYPE_HAS_CHILDREN(42002, "该分类有子分类，请选择子分类"),
YOUR_NEW_ERROR(42008, "你的新错误描述"),  // 新增
```

---

## HTTP 状态码映射

| 错误码范围 | HTTP Status | 说明 |
|------------|-------------|------|
| 0 | 200 | 成功 |
| 40xxx | 200 | 参数错误（业务层面） |
| 401 | 401 | 未认证 |
| 418 | 418 | 需要注册 |
| 42xxx | 200 | 业务规则错误 |
| 44xxx | 200 | 资源不存在 |
| 50xxx | 500 | 系统错误 |

---

## 最佳实践

### 1. 优先使用 BusinessException

```java
// 推荐
throw new BusinessException(ErrorCode.INSUFFICIENT_BALANCE);

// 不推荐
throw new Exception("余额不足");
```

### 2. 选择合适的错误码

```java
// 参数校验失败
throw new BusinessException(ErrorCode.PARAM_INVALID, "金额必须大于0");

// 业务规则校验失败
throw new BusinessException(ErrorCode.INSUFFICIENT_BALANCE);

// 资源不存在
throw new BusinessException(ErrorCode.ACCOUNT_NOT_FOUND);
```

### 3. 自定义消息要清晰

```java
// 好的消息
throw new BusinessException(ErrorCode.INSUFFICIENT_BALANCE, "账户余额 100.00，支出金额 200.00，余额不足");

// 不好的消息
throw new BusinessException(ErrorCode.INSUFFICIENT_BALANCE, "error");
```

---

## 注意事项

1. **BusinessException 是 RuntimeException**：不需要在方法签名中声明 `throws`
2. **保留 throws Exception**：现有的 `throws Exception` 声明可以保留，不影响功能
3. **中文消息会透传**：GlobalExceptionHandler 会检测中文消息并直接返回给前端
4. **敏感信息过滤**：英文/系统异常消息会被替换为通用提示，避免暴露堆栈
