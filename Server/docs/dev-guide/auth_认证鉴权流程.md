# 认证鉴权流程

本文档详细介绍 EasyAccounts Server 模块的认证鉴权系统，包括注册、登录、Token 验证的完整流程，环境变量配置，以及设计理念说明。

---

## 目录

1. [认证模式概述](#认证模式概述)
2. [环境变量配置](#环境变量配置)
3. [核心组件](#核心组件)
4. [注册流程](#注册流程)
5. [登录流程](#登录流程)
6. [Token 验证流程](#token-验证流程)
7. [拦截器工作机制](#拦截器工作机制)
8. [数据存储格式](#数据存储格式)
9. [单端多端登录模式](#单端多端登录模式)
10. [设计选择与权衡](#设计选择与权衡)
11. [可选扩展方向](#可选扩展方向)

---

## 认证模式概述

### 当前模式：文件存储 + UUID Token

EasyAccounts 采用**单用户文件存储认证模式**：

| 特性 | 说明 |
|------|------|
| 用户数量 | 仅支持单用户 |
| 存储方式 | 文件存储 (`secret.key`) |
| Token 类型 | UUID |
| Token 传递 | HTTP Header (`Authorization`) |
| 密码存储 | MD5 哈希（前端传输） |
| 认证开关 | 可通过环境变量关闭 |

### 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         客户端请求                               │
│                    Authorization: {token}                        │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      TokenInterceptor                            │
│                                                                  │
│  1. 检查 auth.enable 是否开启                                    │
│  2. 检查请求路径是否在排除列表                                    │
│  3. 调用 AuthUtils.isAuth(token) 验证                            │
└─────────────────────────────┬───────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
         ┌────────┐     ┌────────┐     ┌────────┐
         │ 200 OK │     │  401   │     │  418   │
         │  放行   │     │需要登录 │     │需要注册│
         └────────┘     └────────┘     └────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Controller                                │
│                      处理业务逻辑                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 环境变量配置

### 配置项说明

| 环境变量 | 配置键 | 默认值 | 说明 |
|----------|--------|--------|------|
| `ENABLE_LOGIN` | `auth.enable` | `false` | 是否启用认证 |
| `EXPIRED_TIME` | `auth.expired` | `30` | Token 过期时间（分钟） |
| `SINGLE_LOGIN` | `auth.single_login` | `true` | 是否单端登录 |
| - | `auth.folder` | `/Ledger/auth/` | 认证文件存储目录 |

### 配置文件

**application-server.properties（生产环境）：**
```properties
# 认证开关（环境变量覆盖）
auth.enable=${ENABLE_LOGIN:false}

# 认证文件存储目录
auth.folder=/Ledger/auth/

# Token 过期时间（分钟）
auth.expired=${EXPIRED_TIME:30}

# 是否单端登录：true=单端(新登录踢掉旧设备)，false=多端(共享Token)
auth.single_login=${SINGLE_LOGIN:true}
```

**application-windows.properties（本地开发）：**
```properties
auth.enable=false
auth.folder=G:\\Temp\\auth
auth.expired=30
auth.single_login=true
```

### Docker 环境配置

```yaml
services:
  server:
    image: easyaccounts-server
    environment:
      - ENABLE_LOGIN=true        # 启用认证
      - EXPIRED_TIME=60          # Token 60分钟过期
      - SINGLE_LOGIN=false       # 多端登录模式
    volumes:
      - auth_data:/Ledger/auth   # 持久化认证文件
```

### 配置说明

**1. auth.enable = false（默认）**
- 所有请求直接放行，无需认证
- 适用于个人本地部署，无安全需求场景

**2. auth.enable = true**
- 启用 Token 认证
- 首次访问需要注册用户名密码
- 后续访问需要登录获取 Token

**3. auth.expired**
- Token 过期时间，单位：分钟
- 每次请求验证成功会自动延长过期时间（滑动刷新）
- 过期后需要重新登录

**4. auth.single_login = true（默认）**
- **单端模式**：每次登录生成新 Token，旧设备的 Token 失效被踢下线
- 适用于安全性要求高的场景

**5. auth.single_login = false**
- **多端模式**：登录时复用现有 Token（未过期时），多设备共享同一个 Token
- 适用于需要多设备同时在线的场景

---

## 核心组件

### 文件结构

```
com.deepblue.yd_jz/
├── config/
│   ├── TokenInterceptor.java    # Token 验证拦截器
│   └── WebConfig.java           # 拦截器注册配置
├── controller/
│   └── AuthController.java      # 登录注册接口
├── service/
│   └── AuthService.java         # 认证业务逻辑
├── entity/
│   └── Auth.java                # 认证数据实体
├── dto/
│   ├── AuthRequestDto.java      # 登录注册请求
│   └── AuthDto.java             # 登录响应（Token）
└── utils/
    └── AuthUtils.java           # 认证工具类（文件读写）
```

### 组件职责

| 组件 | 职责 |
|------|------|
| TokenInterceptor | 拦截请求，验证 Token |
| WebConfig | 注册拦截器，配置排除路径 |
| AuthController | 提供登录/注册 REST 接口 |
| AuthService | 处理登录/注册业务逻辑 |
| Auth | 认证数据实体（Token、用户名、密码、过期时间） |
| AuthUtils | 文件读写、Token 验证 |

---

## 注册流程

### 接口定义

```
POST /auth/register

请求体：
{
    "username": "admin",
    "password": "e10adc3949ba59abbe56e057f20f883e"  // MD5 哈希
}

成功响应：
{
    "code": 0,
    "msg": "Success",
    "data": {
        "token": "550e8400-e29b-41d4-a716-446655440000"
    }
}

失败响应（已存在用户）：
{
    "code": 401,
    "msg": "已存在用户名和密码，忘记密码请重置",
    "data": null
}
```

### 流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                     POST /auth/register                          │
│                   { username, password }                         │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AuthController                               │
│                     register()                                   │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AuthService                                  │
│                     register()                                   │
│                                                                  │
│  1. 调用 authUtils.getAuth() 检查是否已有用户                     │
│                                                                  │
│  2. 如果已存在用户 → 返回 null (失败)                             │
│                                                                  │
│  3. 创建新 Auth 对象：                                            │
│     - 设置 username                                              │
│     - 设置 passwordMD5                                           │
│     - 调用 refreshToken() 生成 Token                             │
│                                                                  │
│  4. 调用 authUtils.saveAuth() 保存到文件                          │
│                                                                  │
│  5. 返回 AuthDto { token }                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AuthUtils                                    │
│                     saveAuth()                                   │
│                                                                  │
│  1. 调用 auth.encode() 将对象转为 Base64 字符串                   │
│  2. 使用 Okio 写入 {auth.folder}/secret.key                      │
└─────────────────────────────────────────────────────────────────┘
```

### 代码详解

**AuthService.register()：**
```java
public AuthDto register(String username, String password) {
    // 1. 检查是否已有用户
    Auth auth = authUtils.getAuth();
    if (auth != null && auth.getUsername() != null && auth.getPasswordMD5() != null) {
        return null;  // 已存在用户，注册失败
    }

    // 2. 创建新用户
    auth = new Auth();
    auth.setUsername(username);
    auth.setPasswordMD5(password);  // 前端已 MD5 加密

    // 3. 生成 Token
    auth.refreshToken(expired);  // expired 从配置读取
    String token = auth.getToken();

    // 4. 保存到文件
    authUtils.saveAuth(auth);

    // 5. 返回 Token
    AuthDto authDto = new AuthDto();
    authDto.setToken(token);
    return authDto;
}
```

**Auth.refreshToken()：**
```java
public void refreshToken(long expireTime) {
    // expireTime 单位：分钟
    this.expireTime = System.currentTimeMillis() + expireTime * 1000 * 60;
    this.createTime = System.currentTimeMillis();
    this.token = UUID.randomUUID().toString();  // 生成新 UUID Token
}
```

---

## 登录流程

### 接口定义

```
POST /auth/login

请求体：
{
    "username": "admin",
    "password": "e10adc3949ba59abbe56e057f20f883e"  // MD5 哈希
}

成功响应：
{
    "code": 0,
    "msg": "Success",
    "data": {
        "token": "550e8400-e29b-41d4-a716-446655440000"
    }
}

失败响应（用户不存在）：
{
    "code": 418,
    "msg": "用户名密码不存在，请注册",
    "data": null
}

失败响应（密码错误）：
{
    "code": 401,
    "msg": "用户名或密码错误",
    "data": null
}
```

### 流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                      POST /auth/login                            │
│                   { username, password }                         │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AuthController                               │
│                        login()                                   │
│                                                                  │
│  1. 调用 authService.verfiyAuthFiles() 检查用户是否存在          │
│     - 不存在 → 返回 418 "需要注册"                               │
│                                                                  │
│  2. 调用 authService.login() 验证用户名密码                      │
│     - 验证失败 → 返回 401 "用户名或密码错误"                     │
│     - 验证成功 → 返回 Token                                      │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AuthService                                  │
│                        login()                                   │
│                                                                  │
│  1. 读取 secret.key 获取存储的 Auth 对象                         │
│                                                                  │
│  2. 比对用户名和密码（MD5）                                       │
│                                                                  │
│  3. 匹配成功，根据登录模式处理 Token：                            │
│     ┌─────────────────────────────────────────────────────────┐ │
│     │  单端模式 (SINGLE_LOGIN=true)                           │ │
│     │  → 生成新 Token，旧设备失效                              │ │
│     ├─────────────────────────────────────────────────────────┤ │
│     │  多端模式 (SINGLE_LOGIN=false)                          │ │
│     │  ├─ Token 未过期 → 复用现有 Token，刷新过期时间          │ │
│     │  └─ Token 已过期 → 生成新 Token                         │ │
│     └─────────────────────────────────────────────────────────┘ │
│                                                                  │
│  4. 保存更新后的 Auth 到文件                                     │
│                                                                  │
│  5. 返回 Token                                                   │
│                                                                  │
│  6. 匹配失败：返回 null                                          │
└─────────────────────────────────────────────────────────────────┘
```

### 单端/多端模式详细流程图

```
                    ┌─────────────────┐
                    │  POST /login    │
                    │ 用户名 + 密码   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ 用户名密码正确？ │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │ 否                          │ 是
              ▼                             ▼
         ┌────────┐              ┌─────────────────┐
         │  401   │              │  单端模式？      │
         │密码错误│              │ SINGLE_LOGIN    │
         └────────┘              └────────┬────────┘
                                          │
                          ┌───────────────┴───────────────┐
                          │ true (单端)                   │ false (多端)
                          ▼                               ▼
                 ┌─────────────────┐           ┌─────────────────┐
                 │ 生成新 UUID      │           │ Token 未过期？   │
                 │ 覆盖旧的        │           └────────┬────────┘
                 │ 旧设备被踢      │                    │
                 └────────┬────────┘         ┌─────────┴─────────┐
                          │                  │ 是                │ 否
                          │                  ▼                   ▼
                          │         ┌─────────────────┐  ┌─────────────────┐
                          │         │ 复用旧 UUID      │  │ 生成新 UUID     │
                          │         │ 只刷新过期时间   │  │ (旧的已没用)    │
                          │         └────────┬────────┘  └────────┬────────┘
                          │                  │                    │
                          └──────────────────┴────────────────────┘
                                             │
                                             ▼
                                    ┌─────────────────┐
                                    │  返回 Token     │
                                    │  保存到文件     │
                                    └─────────────────┘
```

### 多端场景示意

```
┌─────────────────────────────────────────────────────────────────┐
│                     多端模式 (SINGLE_LOGIN=false)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   服务端存储: { token: "abc-123", expireTime: 10:30 }           │
│                                                                 │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐               │
│   │  手机端   │     │  电脑端   │     │  平板端   │               │
│   │ abc-123  │     │ abc-123  │     │ abc-123  │               │
│   └────┬─────┘     └────┬─────┘     └────┬─────┘               │
│        │                │                │                      │
│        └────────────────┴────────────────┘                      │
│                         │                                       │
│                    共享同一个 Token                              │
│                    任一端活跃都续期（滑动刷新）                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     单端模式 (SINGLE_LOGIN=true)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   1. 手机登录 → 服务端: { token: "abc-123" }                    │
│                                                                 │
│   2. 电脑登录 → 服务端: { token: "xyz-789" }  ← 新的覆盖旧的    │
│                                                                 │
│   3. 手机请求 → Token "abc-123" ≠ "xyz-789" → 401 被踢          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 代码详解

**AuthController.login()：**
```java
@PostMapping("/login")
public BaseDto login(@RequestBody AuthRequestDto authRequestDto) {
    // 1. 检查用户是否存在
    if (!authService.verfiyAuthFiles()) {
        return BaseDto.setErrorBean("用户名密码不存在，请注册", 418);
    }

    // 2. 验证用户名密码
    AuthDto authDto = authService.login(
        authRequestDto.getUsername(),
        authRequestDto.getPassword()
    );

    if (authDto == null) {
        return BaseDto.setErrorBean("用户名或密码错误", 401);
    }

    // 3. 返回 Token
    BaseDto<AuthDto> baseDto = BaseDto.setSuccessBean();
    baseDto.setData(authDto);
    return baseDto;
}
```

**AuthService.login()：**
```java
@Value("${auth.single_login:true}")
private boolean singleLogin;

public AuthDto login(String username, String password) {
    Auth auth = authUtils.getAuth();

    if (auth != null) {
        // 比对用户名和密码
        if (auth.getUsername().equals(username) &&
            auth.getPasswordMD5().equals(password)) {

            long now = System.currentTimeMillis();

            if (!singleLogin && auth.getExpireTime() > now) {
                // 多端模式 + Token未过期：只刷新过期时间，不换Token
                auth.setExpireTime(now + expired * 60 * 1000);
                log.info("多端登录模式：复用现有Token，刷新过期时间");
            } else {
                // 单端模式 或 Token已过期：生成新Token
                auth.refreshToken(expired);
            }

            String token = auth.getToken();

            // 保存到文件
            authUtils.saveAuth(auth);

            log.debug("登录成功 user: {} ,token: {}", username, token);

            AuthDto authDto = new AuthDto();
            authDto.setToken(token);
            return authDto;
        }
    }
    return null;
}
```

---

## Token 验证流程

### 验证逻辑

```
┌─────────────────────────────────────────────────────────────────┐
│                   AuthUtils.isAuth(token)                        │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ auth.enable ?   │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │ false                       │ true
              ▼                             ▼
        ┌──────────┐              ┌─────────────────┐
        │ return   │              │ token == null ? │
        │   200    │              └────────┬────────┘
        │  (放行)   │                       │
        └──────────┘           ┌────────────┴────────────┐
                               │ null                    │ 有值
                               ▼                         ▼
                    ┌─────────────────┐       ┌─────────────────┐
                    │ secret.key存在? │       │ isTokenValid()  │
                    └────────┬────────┘       └────────┬────────┘
                             │                         │
              ┌──────────────┴──────────────┐          │
              │ 不存在                      │ 存在      │
              ▼                             ▼          │
        ┌──────────┐              ┌──────────┐         │
        │ return   │              │ return   │         │
        │   418    │              │   401    │         │
        │(需要注册) │              │(需要登录) │         │
        └──────────┘              └──────────┘         │
                                                       │
                              ┌────────────────────────┘
                              ▼
                    ┌─────────────────┐
                    │  读取 secret.key │
                    │  解析 Auth 对象  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ token 匹配 &&   │
                    │ 未过期 ?        │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │ 是                          │ 否
              ▼                             ▼
        ┌──────────┐              ┌──────────┐
        │ return   │              │ return   │
        │   200    │              │   401    │
        │  (通过)   │              │(需要登录) │
        └──────────┘              └──────────┘
```

### 代码详解

**AuthUtils.isAuth()：**
```java
public int isAuth(String token) {
    // 1. 认证未启用，直接放行
    if (!authEnable) {
        return 200;
    }

    // 2. Token 为空
    if (token == null) {
        if (!isFileExist()) {
            return 418;  // 用户不存在，需要注册
        } else {
            return 401;  // 用户存在，需要登录
        }
    }

    // 3. 验证 Token
    return isTokenValid(token);
}

private int isTokenValid(String token) {
    File file = new File(authFolder + "/secret.key");
    try {
        // 读取文件
        String key = Okio.buffer(Okio.source(file)).readUtf8();

        // Base64 解码为 Auth 对象
        Auth auth = Auth.decode(key);
        if (auth == null) {
            return 418;
        }

        long currentTime = System.currentTimeMillis();

        // 验证 Token 和过期时间
        if (auth.getToken().equals(token) && auth.getExpireTime() > currentTime) {
            return 200;  // 验证通过
        } else {
            return 401;  // Token 无效或已过期
        }
    } catch (IOException e) {
        log.error("Error reading key file: {}", e.getMessage());
        return 418;
    }
}
```

---

## 拦截器工作机制

### 拦截器配置

**WebConfig.java：**
```java
@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Value("${auth.enable}")
    private boolean authEnable;

    @Autowired
    private AuthUtils authUtils;

    @Bean
    public TokenInterceptor tokenInterceptor() {
        return new TokenInterceptor(authEnable, authUtils);
    }

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        if (authEnable) {
            registry.addInterceptor(tokenInterceptor())
                    .addPathPatterns("/**")         // 拦截所有路径
                    .excludePathPatterns(           // 排除以下路径
                        "/swagger-ui.html",
                        "/swagger-ui/**",
                        "/v2/api-docs",
                        "/swagger-resources/**",
                        "/webjars/**",
                        "/auth/login",              // 登录接口
                        "/auth/register",           // 注册接口
                        "/error",
                        "/image/**"                 // 图片接口
                    );
        }
    }
}
```

### 排除路径说明

| 路径 | 原因 |
|------|------|
| `/auth/login` | 登录接口，无需认证 |
| `/auth/register` | 注册接口，无需认证 |
| `/image/**` | 图片资源，允许公开访问 |
| `/swagger-*` | API 文档，开发调试用 |
| `/error` | 错误页面 |

### TokenInterceptor 实现

**TokenInterceptor.java：**
```java
public class TokenInterceptor implements HandlerInterceptor {

    private boolean authEnable;
    private AuthUtils authUtils;

    public TokenInterceptor(boolean authEnable, AuthUtils authUtils) {
        this.authEnable = authEnable;
        this.authUtils = authUtils;
    }

    @Override
    public boolean preHandle(HttpServletRequest request,
                            HttpServletResponse response,
                            Object handler) throws Exception {

        log.debug("TokenInterceptor preHandle called for URI: {}",
                  request.getRequestURI());

        // 认证未启用，直接放行
        if (!authEnable) {
            return true;
        }

        // 获取 Token
        String token = request.getHeader("Authorization");
        log.debug("Authorization token: {}", token);

        // 验证 Token
        int code = authUtils.isAuth(token);

        if (code == 200) {
            log.debug("Authentication successful for URI: {}",
                      request.getRequestURI());
            return true;  // 放行
        } else {
            log.warn("Authentication failed for URI: {} with code: {}",
                     request.getRequestURI(), code);

            String errorMsg = "";
            if (code == 401) {
                errorMsg = "需要登录";
            } else if (code == 418) {
                errorMsg = "需要注册";
            }

            response.sendError(code, errorMsg);
            return false;  // 拦截
        }
    }
}
```

---

## 数据存储格式

### 文件位置

```
{auth.folder}/secret.key

生产环境: /Ledger/auth/secret.key
Windows:  G:\Temp\auth\secret.key
```

### 存储格式

Auth 对象 → JSON → Base64 编码 → 写入文件

**示例：**

原始 Auth 对象：
```json
{
    "token": "550e8400-e29b-41d4-a716-446655440000",
    "username": "admin",
    "passwordMD5": "e10adc3949ba59abbe56e057f20f883e",
    "expireTime": 1704067200000,
    "createTime": 1704063600000
}
```

Base64 编码后（存储内容）：
```
eyJ0b2tlbiI6IjU1MGU4NDAwLWUyOWItNDFkNC1hNzE2LTQ0NjY1NTQ0MDAwMCIsInVzZXJuYW1lIjoiYWRtaW4iLCJwYXNzd29yZE1ENSI6ImUxMGFkYzM5NDliYTU5YWJiZTU2ZTA1N2YyMGY4ODNlIiwiZXhwaXJlVGltZSI6MTcwNDA2NzIwMDAwMCwiY3JlYXRlVGltZSI6MTcwNDA2MzYwMDAwMH0=
```

### 编解码实现

**Auth.java：**
```java
// 编码：对象 → Base64
public String encode() {
    String authStr = GsonUtils.gson.toJson(this);
    Base64.Encoder encoder = Base64.getEncoder();
    return encoder.encodeToString(authStr.getBytes());
}

// 解码：Base64 → 对象
public static Auth decode(String secretKey) {
    Base64.Decoder decoder = Base64.getDecoder();
    String authStr = new String(decoder.decode(secretKey));
    return GsonUtils.gson.fromJson(authStr, Auth.class);
}
```

---

## 单端多端登录模式

### 模式说明

系统支持两种登录模式，通过环境变量 `SINGLE_LOGIN` 控制：

| 模式 | 配置值 | 说明 |
|------|--------|------|
| 单端模式 | `true`（默认） | 每次登录生成新 Token，旧设备被踢下线 |
| 多端模式 | `false` | 多设备共享同一个 Token，同时在线 |

### 完整认证流程图

```
                    ┌─────────────────┐
                    │   客户端请求     │
                    │ Header: Token   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Token == null? │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │ 是                          │ 否
              ▼                             ▼
     ┌─────────────────┐          ┌─────────────────┐
     │ 用户文件存在？   │          │  读取存储的 Auth │
     └────────┬────────┘          └────────┬────────┘
              │                            │
       ┌──────┴──────┐                     ▼
       │ 否          │ 是        ┌─────────────────┐
       ▼             ▼           │ Token 匹配？     │
  ┌────────┐   ┌────────┐       │ 存储的 == 请求的 │
  │  418   │   │  401   │       └────────┬────────┘
  │需要注册│   │需要登录│                │
  └────────┘   └────────┘         ┌──────┴──────┐
                                  │ 否          │ 是
                                  ▼             ▼
                            ┌────────┐  ┌─────────────────┐
                            │  401   │  │   未过期？       │
                            │Token错误│  │ expireTime > now│
                            └────────┘  └────────┬────────┘
                                                 │
                                          ┌──────┴──────┐
                                          │ 否          │ 是
                                          ▼             ▼
                                    ┌────────┐    ┌────────────┐
                                    │  401   │    │    200     │
                                    │已过期  │    │ ✅ 放行    │
                                    └────────┘    │ 滑动刷新   │
                                                  └────────────┘
```

### 需要重新登录的两种情况

| 情况 | 触发场景 | 返回码 |
|------|----------|--------|
| **Token 不一致** | 单端模式下被新登录踢掉 | 401 |
| **Token 已过期** | 任何模式下，超过过期时间没活动 | 401 |

### 多端模式 Token 过期场景

```
时间线:
─────────────────────────────────────────────────────────────────►

10:00                    10:30                    11:00
  │                        │                        │
  │  Token 过期时间         │                        │
  │  ────────────────────► │                        │
  │                        │                        │
  ▼                        ▼                        ▼
┌────┐                  ┌────┐                   ┌────┐
│手机│ 登录获取Token     │    │                   │手机│ 请求 → 401 过期
└────┘                  └────┘                   └────┘
                                                    │
┌────┐                  ┌────┐                   ┌────┐
│电脑│                  │电脑│ 请求 → 401 过期   │电脑│ 重新登录 → 新Token
└────┘                  └────┘                   └────┘
                           │                        │
                           │                        ▼
                           │                   ┌────────────┐
                           │                   │ 手机也要   │
                           │                   │ 重新登录   │
                           │                   │ 获取新Token│
                           │                   └────────────┘
```

### 模式切换影响

| 切换方向 | 影响 |
|----------|------|
| 单端 → 多端 | 现有 Token 继续有效，新登录设备共享该 Token |
| 多端 → 单端 | 下次登录生成新 Token，其他设备 Token 失效 |

---

## 设计选择与权衡

本系统的认证设计基于**私有部署模式**的核心理念：每个用户在自己的服务器上部署自己的实例，拥有完全的数据控制权。

### 1. HTTPS 由 Nginx 处理

| 设计选择 | 说明 |
|----------|------|
| **后端不处理 HTTPS** | HTTPS/TLS 加密由前置的 Nginx 反向代理负责 |
| **标准架构模式** | 这是业界标准的部署架构，后端专注于业务逻辑 |
| **灵活性** | 用户可根据自己的环境配置 SSL 证书、选择证书提供商 |

```
客户端 ─── HTTPS ───> Nginx (TLS终止) ─── HTTP ───> 后端服务
```

> **部署建议**：生产环境务必在 Nginx 配置 HTTPS，可使用 Let's Encrypt 免费证书。

### 2. 单用户模式

| 设计选择 | 理由 |
|----------|------|
| **私有部署模式** | 每个用户安装自己的实例，天然实现数据隔离 |
| **简化架构** | 无需复杂的用户管理、权限系统、数据隔离逻辑 |
| **完全控制权** | 用户拥有自己服务器的完全控制权，数据完全私有 |
| **降低维护成本** | 开发者无需维护中心化服务，无运维负担 |

这种模式类似于自建密码管理器（如 Bitwarden 自托管版）、个人 NAS 等应用的设计理念。

### 3. 删除 Key 重置密码

| 设计选择 | 理由 |
|----------|------|
| **无"忘记密码"功能** | 避免密码重置成为安全攻击向量 |
| **删除 secret.key 重新注册** | 只有服务器管理员才能执行此操作 |
| **明确责任边界** | 密码重置由服务器所有者自行操作，开发者不承担责任 |
| **安全设计** | 即使应用层被攻破，攻击者也无法通过应用重置密码 |

```bash
# 密码重置流程（需服务器访问权限）
rm /path/to/auth/secret.key
# 重新访问应用，进入注册页面
```

> **安全理念**：谁拥有服务器，谁拥有数据控制权。这确保了即使应用存在漏洞，攻击者也无法在不接触服务器的情况下重置密码。

### 4. 文件存储认证信息

| 设计选择 | 理由 |
|----------|------|
| **独立于数据库** | 认证系统不依赖数据库，启动时无需数据库连接 |
| **简化部署** | 减少初始化步骤，降低部署复杂度 |
| **单用户足够** | 对于单用户场景，文件存储性能完全足够 |
| **易于备份** | 认证数据独立存储，可单独备份或排除 |

### 5. 其他设计说明

| 设计 | 说明 |
|------|------|
| **MD5 哈希** | 前端预处理，确保明文密码不在网络传输（配合 HTTPS） |
| **UUID Token** | 简单可靠，单用户场景下无需 JWT 的复杂性 |
| **可关闭认证** | 内网环境或开发调试时可通过环境变量关闭 |
| **418 状态码** | 便于前端区分"认证失效"与其他错误，触发登录跳转 |

---

## 可选扩展方向

以下是一些可选的扩展方向，可根据实际需求选择性实施。当前架构对于私有部署的单用户场景已经足够使用。

### 性能优化（可选）

#### 1. 添加内存缓存

```java
@Component
public class AuthUtils {
    private Auth cachedAuth;
    private long cacheExpireTime;

    public Auth getAuth() {
        long now = System.currentTimeMillis();
        if (cachedAuth != null && now < cacheExpireTime) {
            return cachedAuth;
        }
        // 读取文件并缓存
        cachedAuth = readFromFile();
        cacheExpireTime = now + 60000; // 缓存 1 分钟
        return cachedAuth;
    }
}
```

#### 2. 使用常量时间比较（安全增强）

```java
import java.security.MessageDigest;

// 防止时序攻击
private boolean constantTimeEquals(String a, String b) {
    return MessageDigest.isEqual(a.getBytes(), b.getBytes());
}
```

### 功能扩展（可选）

#### 1. 使用 JWT 替代 UUID Token（如需跨服务认证）

```java
// 使用 jjwt 库
String jwt = Jwts.builder()
    .setSubject(username)
    .setIssuedAt(new Date())
    .setExpiration(new Date(System.currentTimeMillis() + expireTime))
    .signWith(SignatureAlgorithm.HS256, secretKey)
    .compact();
```

JWT 优势：
- 自包含，无需服务端存储
- 可携带用户信息
- 签名防篡改
- 支持无状态扩展

#### 2. 添加 Token 刷新机制（如需长期会话）

```java
@PostMapping("/refresh")
public BaseDto refreshToken(@RequestHeader("Authorization") String token) {
    // 验证旧 Token（允许已过期但未超过刷新窗口）
    // 生成新 Token
    // 返回新 Token
}
```

### 多用户扩展（如需 SaaS 化）

> 注意：以下内容仅适用于需要转型为 SaaS 多用户模式的场景，当前私有部署模式无需实现。

#### 1. 集成 Spring Security

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http
            .authorizeRequests()
                .antMatchers("/auth/**").permitAll()
                .anyRequest().authenticated()
            .and()
            .addFilterBefore(jwtFilter, UsernamePasswordAuthenticationFilter.class);
    }
}
```

#### 2. 数据库存储用户

```sql
CREATE TABLE user (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME,
    last_login DATETIME
);

CREATE TABLE user_token (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    token VARCHAR(255),
    expire_at DATETIME,
    device_info VARCHAR(255)
);
```

#### 3. 多用户数据隔离

如果转型为 SaaS 模式，还需实现：

- 用户注册/管理界面
- 数据隔离（所有业务表添加 user_id 外键）
- 角色权限控制（可选）

---

## 相关文件路径

| 类型 | 路径 |
|------|------|
| 控制器 | `controller/AuthController.java` |
| 服务 | `service/AuthService.java` |
| 实体 | `entity/Auth.java` |
| 工具 | `utils/AuthUtils.java` |
| 拦截器 | `config/TokenInterceptor.java` |
| 配置 | `config/WebConfig.java` |
| DTO | `dto/AuthRequestDto.java`, `dto/AuthDto.java` |
| 配置文件 | `resources/application-*.properties` |
