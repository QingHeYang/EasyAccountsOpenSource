# API 接口详情

本文档详细介绍 EasyAccounts Server 模块的 REST API 接口、数据定义、拦截器机制和 Swagger 配置。

---

## 目录

1. [接口概述](#接口概述)
2. [统一响应格式](#统一响应格式)
3. [身份认证机制](#身份认证机制)
4. [拦截器配置](#拦截器配置)
5. [Swagger 配置](#swagger-配置)
6. [CORS 跨域配置](#cors-跨域配置)
7. [接口详情](#接口详情)
8. [DTO 数据定义](#dto-数据定义)
9. [错误码说明](#错误码说明)

---

## 接口概述

### 基本信息

| 项目 | 说明 |
|------|------|
| 基础路径 | `/` |
| 协议 | HTTP/HTTPS |
| 数据格式 | JSON |
| 字符编码 | UTF-8 |
| 认证方式 | Token（Header: Authorization） |

### 控制器列表

| 控制器 | 路径前缀 | 功能 | Swagger Tag |
|--------|----------|------|-------------|
| AuthController | `/auth` | 登录注册 | 登录注册 |
| HomeController | `/home` | 首页信息 | 首页信息 |
| FlowController | `/flow` | 流水管理 | 流水管理 |
| AccountController | `/account` | 账户管理 | 账户管理 |
| TypeController | `/type` | 分类管理 | 分类管理 |
| ActionController | `/action` | 收支管理 | 收支管理 |
| AnalysisController | `/analysis` | 财务分析 | 财务分析 |
| ScreenController | `/screen` | 筛选功能 | 筛选功能 |
| FlowTemplateController | `/template` | 快记模板 | 快记模板 |
| TagController | `/tag` | 模板标签管理 | 模板标签管理 |
| ImageController | `/image` | 图片管理 | 图片管理 |

---

## 统一响应格式

所有 API 接口使用统一的响应格式 `BaseDto<T>`：

```java
public class BaseDto<T> {
    private int code;      // 状态码
    private String msg;    // 消息
    private T data;        // 数据
}
```

### 状态码定义

| 状态码 | 常量 | 说明 |
|--------|------|------|
| 0 | SUCCESS | 成功 |
| 401 | - | 需要登录/密码错误 |
| 403 | - | 资源不存在 |
| 404 | NOT_FOUND | 未找到 |
| 418 | - | 需要注册 |
| 500 | SERVER_ERROR | 服务器错误 |

### 响应示例

**成功响应：**
```json
{
    "code": 0,
    "msg": "Success",
    "data": {
        // 具体数据
    }
}
```

**错误响应：**
```json
{
    "code": 401,
    "msg": "用户名或密码错误",
    "data": null
}
```

---

## 身份认证机制

### 认证流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   客户端     │     │   拦截器     │     │   控制器     │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       │  1. 发送请求       │                   │
       │  (带 Token)       │                   │
       │ ─────────────────>│                   │
       │                   │                   │
       │                   │ 2. 验证 Token      │
       │                   │ ────────────┐     │
       │                   │             │     │
       │                   │ <───────────┘     │
       │                   │                   │
       │                   │ 3. 验证通过        │
       │                   │ ─────────────────>│
       │                   │                   │
       │                   │   4. 处理请求      │
       │                   │ <─────────────────│
       │                   │                   │
       │  5. 返回响应       │                   │
       │ <─────────────────│                   │
       │                   │                   │
```

### Token 验证逻辑

**AuthUtils.java** - Token 验证核心逻辑：

```java
public int isAuth(String token) {
    // 1. 认证未启用时直接放行
    if (!authEnable) {
        return 200;
    }

    // 2. Token 为空时
    if (token == null) {
        if (!isFileExist()) {
            return 418;  // 需要注册
        } else {
            return 401;  // 需要登录
        }
    }

    // 3. 验证 Token 有效性
    return isTokenValid(token);
}

private int isTokenValid(String token) {
    // 从文件读取认证信息
    Auth auth = Auth.decode(key);

    // 验证 Token 和过期时间
    if (auth.getToken().equals(token) && auth.getExpireTime() > currentTime) {
        return 200;  // 验证通过
    } else {
        return 401;  // 验证失败
    }
}
```

### 认证配置

**application.properties:**
```properties
# 启用认证
auth.enable=${ENABLE_LOGIN:false}

# 认证文件存储路径
auth.folder=/Ledger/auth/

# Token 过期时间（天）
auth.expired=${EXPIRED_TIME:30}
```

### Token 存储

Token 信息以 Base64 编码的 JSON 格式存储在 `secret.key` 文件中：

```java
public class Auth {
    private String token;          // UUID Token
    private String username;       // 用户名
    private String passwordMD5;    // 密码 MD5
    private long expireTime;       // 过期时间戳
    private long createTime;       // 创建时间戳
}
```

---

## 拦截器配置

### TokenInterceptor

**位置：** `config/TokenInterceptor.java`

Token 验证拦截器，在请求到达控制器之前进行身份验证。

```java
public class TokenInterceptor implements HandlerInterceptor {

    private boolean authEnable;
    private AuthUtils authUtils;

    @Override
    public boolean preHandle(HttpServletRequest request,
                            HttpServletResponse response,
                            Object handler) throws Exception {

        // 认证未启用时直接放行
        if (!authEnable) {
            return true;
        }

        // 获取 Token
        String token = request.getHeader("Authorization");

        // 验证 Token
        int code = authUtils.isAuth(token);

        if (code == 200) {
            return true;  // 放行
        } else {
            // 返回错误
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

### 拦截器注册

**WebConfig.java:**

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
                    .addPathPatterns("/**")
                    .excludePathPatterns(
                        "/swagger-ui.html",
                        "/swagger-ui/**",
                        "/v2/api-docs",
                        "/swagger-resources/**",
                        "/webjars/**",
                        "/auth/login",
                        "/auth/register",
                        "/error",
                        "/image/**"
                    );
        }
    }
}
```

### 排除路径说明

| 路径 | 说明 |
|------|------|
| `/swagger-ui.html` | Swagger UI 页面 |
| `/swagger-ui/**` | Swagger 静态资源 |
| `/v2/api-docs` | Swagger API 文档 |
| `/swagger-resources/**` | Swagger 资源 |
| `/webjars/**` | Web Jar 资源 |
| `/auth/login` | 登录接口 |
| `/auth/register` | 注册接口 |
| `/error` | 错误页面 |
| `/image/**` | 图片获取（无需鉴权） |

---

## Swagger 配置

### 配置类

**SwaggerConfig.java:**

```java
@Configuration
@EnableSwagger2
public class SwaggerConfig {

    public static final String AUTHORIZATION_HEADER = "Authorization";

    @Bean
    public Docket api() {
        return new Docket(DocumentationType.SWAGGER_2)
                .select()
                .apis(RequestHandlerSelectors.basePackage(
                    "com.deepblue.yd_jz.controller"))
                .paths(PathSelectors.any())
                .build()
                .securitySchemes(Collections.singletonList(apiKey()))
                .securityContexts(Collections.singletonList(securityContext()))
                .apiInfo(apiInfo());
    }

    private ApiInfo apiInfo() {
        return new ApiInfo(
                "EasyAccounts后台接口",
                "下列接口均为nginx前端请求使用接口",
                "v2.4.0",
                "",
                new Contact("Mercy",
                    "https://github.com/QingHeYang/EasyAccounts", ""),
                "MIT License",
                "https://github.com/QingHeYang/EasyAccounts",
                Collections.emptyList()
        );
    }

    // API Key 配置（用于 Token 认证）
    private ApiKey apiKey() {
        return new ApiKey("UUID", AUTHORIZATION_HEADER, "header");
    }
}
```

### 访问地址

| 环境 | URL |
|------|-----|
| 开发环境 | `http://localhost:8085/swagger-ui.html` |
| 生产环境 | `http://server:8081/swagger-ui.html` |

### Swagger 注解使用

```java
@RestController
@RequestMapping("/flow")
@Api(value = "FlowController", tags = {"流水管理"})
public class FlowController {

    @ApiOperation(value = "添加流水")
    @PostMapping("/addFlow")
    public BaseDto addFlow(@RequestBody FlowAddRequestDto dto) {
        // ...
    }

    @ApiOperation(value = "获取主业流水")
    @ApiParam(name = "chooseHandle",
              value = "0:全部 1:支出 2:收入",
              required = true)
    @GetMapping("/getFlowListMain/{chooseHandle}/{chooseOrder}/{date}")
    public BaseDto<FlowListDto> getFlowListMain(
            @PathVariable int chooseHandle,
            @PathVariable int chooseOrder,
            @PathVariable String date) {
        // ...
    }
}
```

---

## CORS 跨域配置

**WebConfig.java:**

```java
@Bean
public CorsFilter corsFilter() {
    UrlBasedCorsConfigurationSource source =
        new UrlBasedCorsConfigurationSource();

    CorsConfiguration config = new CorsConfiguration();

    // 允许所有头部
    config.addAllowedHeader("*");

    // 允许所有方法
    config.addAllowedMethod("*");

    // 允许所有来源
    config.addAllowedOrigin("*");

    // 应用到所有路径
    source.registerCorsConfiguration("/**", config);

    return new CorsFilter(source);
}
```

---

## 接口详情

### 1. 登录注册 (AuthController)

#### POST /auth/login - 登录

**请求体：**
```json
{
    "username": "admin",
    "password": "password123"
}
```

**响应：**
```json
{
    "code": 0,
    "msg": "Success",
    "data": {
        "token": "550e8400-e29b-41d4-a716-446655440000"
    }
}
```

**错误码：**
- 401: 用户名或密码错误
- 418: 用户名密码不存在，请注册

#### POST /auth/register - 注册

**请求体：**
```json
{
    "username": "admin",
    "password": "password123"
}
```

**响应：**
```json
{
    "code": 0,
    "msg": "Success",
    "data": {
        "token": "550e8400-e29b-41d4-a716-446655440000"
    }
}
```

---

### 2. 首页信息 (HomeController)

#### GET /home/getHomeInfo - 获取首页信息

**响应：**
```json
{
    "code": 0,
    "msg": "Success",
    "data": {
        "totalAsset": "50000.00",
        "netAsset": "45000.00",
        "curIncome": "8000.00",
        "curOutCome": "3000.00",
        "yearIncome": "96000.00",
        "yearOutCome": "36000.00",
        "yearBalance": "60000.00",
        "accounts": [
            {
                "id": 1,
                "accountName": "招商银行",
                "accountAsset": "30000.00",
                "exemptAsset": "0.00",
                "percent": "60%",
                "note": "工资卡"
            }
        ],
        "monthDetails": [
            {
                "month": "2024-01",
                "income": "8000.00",
                "outcome": "3000.00",
                "balance": "5000.00"
            }
        ]
    }
}
```

#### GET /home/getHomeInfoV2/{year} - V2版本获取首页信息

**路径参数：**
- `year`: 年份，如 2024

#### GET /home/getVersion - 获取版本信息

**响应：**
```json
{
    "code": 0,
    "msg": "Success",
    "data": {
        "fontBranch": "3.1.0",
        "backendBranch": "2.5.0",
        "mysqlBranch": "2.5.0",
        "release": "2.5.0"
    }
}
```

---

### 3. 流水管理 (FlowController)

#### POST /flow/addFlow - 添加流水

**请求体：**
```json
{
    "money": "100.00",
    "fDate": "2024-01-15",
    "createDate": "2024-01-15 10:30:00",
    "actionId": 2,
    "accountId": 1,
    "accountToId": 0,
    "typeId": 5,
    "isCollect": false,
    "note": "午餐",
    "from": "manual",
    "images": ["image1.jpg", "image2.jpg"]
}
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| money | String | 是 | 金额 |
| fDate | String | 是 | 交易日期 (yyyy-MM-dd) |
| createDate | String | 否 | 创建时间 |
| actionId | int | 是 | 操作类型 (1:收入, 2:支出, 3:转账) |
| accountId | int | 是 | 主账户 ID |
| accountToId | int | 否 | 转账目标账户 ID |
| typeId | int | 是 | 分类 ID |
| isCollect | boolean | 否 | 是否收藏 |
| note | String | 否 | 备注 |
| from | String | 否 | 来源标识 (如 "ai") |
| images | List<String> | 否 | 图片文件名列表 |

#### GET /flow/getFlow/{id} - 获取指定流水

**路径参数：**
- `id`: 流水 ID

**响应：**
```json
{
    "code": 0,
    "msg": "Success",
    "data": {
        "id": 1,
        "fDate": "2024-01-15",
        "money": "100.00",
        "typeId": 5,
        "typeName": "餐饮",
        "actionId": 2,
        "actionName": "支出",
        "accountId": 1,
        "accountName": "招商银行",
        "note": "午餐",
        "collect": false,
        "exempt": false,
        "images": ["image1.jpg"]
    }
}
```

#### PUT /flow/updateFlow/{id} - 更新流水

**路径参数：**
- `id`: 流水 ID

**请求体：** 同添加流水

#### PUT /flow/collectFlow/{id}/{collect} - 收藏/取消收藏流水

**路径参数：**
- `id`: 流水 ID
- `collect`: 1=收藏, 0=取消收藏

#### DELETE /flow/deleteFlow/{id} - 删除流水

**路径参数：**
- `id`: 流水 ID

#### GET /flow/getFlowListMain/{chooseHandle}/{chooseOrder}/{date} - 获取主页流水列表

**路径参数：**

| 参数 | 说明 |
|------|------|
| chooseHandle | 0:全部, 1:支出, 2:收入 |
| chooseOrder | 排序方式 |
| date | 月份 (yyyy-MM) |

**响应：**
```json
{
    "code": 0,
    "msg": "Success",
    "data": {
        "totalIn": "8000.00",
        "totalOut": "3000.00",
        "totalEarn": "5000.00",
        "typeList": [
            {
                "typeName": "餐饮",
                "money": "1500.00",
                "typeId": 5,
                "parent": true,
                "children": [
                    {
                        "typeName": "午餐",
                        "money": "800.00",
                        "typeId": 6
                    }
                ]
            }
        ],
        "flows": [
            {
                "id": 1,
                "tName": "餐饮-午餐",
                "money": "25.00",
                "exempt": false,
                "collect": false,
                "handle": 2,
                "hName": "支出",
                "note": "午餐",
                "aName": "招商银行",
                "toAName": null,
                "fDate": "2024-01-15",
                "from": "manual",
                "hasImages": true
            }
        ]
    }
}
```

#### GET /flow/makeExcel/{date} - 生成月度流水Excel

**路径参数：**
- `date`: 月份 (yyyy-MM)

---

### 4. 账户管理 (AccountController)

#### POST /account/addAccount - 添加账户

**请求体：**
```json
{
    "name": "招商银行",
    "money": "10000.00",
    "exemptMoney": "0.00",
    "card": "6225xxxx",
    "note": "工资卡"
}
```

#### PUT /account/updateAccount/{id} - 更新账户

#### GET /account/getAccount/{id} - 获取指定账户

#### GET /account/getAccount - 获取全部账户（排除禁用）

#### GET /account/getAccountNoLimit - 获取全部账户（含禁用）

#### DELETE /account/deleteAccount/{id} - 停用账户

---

### 5. 分类管理 (TypeController)

#### POST /type/addType - 添加分类

**请求体：**
```json
{
    "tName": "餐饮",
    "parent": -1,
    "actionId": 2,
    "analysisDisable": false
}
```

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| tName | String | 分类名称 |
| parent | Integer | 父分类 ID，-1 表示顶级 |
| actionId | Integer | 操作类型 (1:收入, 2:支出) |
| analysisDisable | Boolean | 是否排除出分析 |

#### PUT /type/updateType/{id} - 更新分类

#### DELETE /type/deleteType/{id} - 停用分类

#### PUT /type/archiveType/{id}?archive=true - 归档/取消归档分类

#### GET /type/getType - 获取所有分类

**响应：**
```json
{
    "code": 0,
    "msg": "Success",
    "data": [
        {
            "id": 1,
            "tName": "餐饮",
            "parent": -1,
            "hasChild": true,
            "actionId": 2,
            "actionName": "支出",
            "children": [
                {
                    "id": 2,
                    "tName": "午餐",
                    "parent": 1
                }
            ]
        }
    ]
}
```

#### GET /type/getType/{parent} - 获取二级分类

#### GET /type/getTypeByActionId/{actionId} - 获取指定收支的分类

#### GET /type/getType/noLimit - 获取所有分类（含归档、停用）

#### GET /type/getTypeSingle/{id} - 获取单个分类

#### GET /type/getTypeArchive - 获取归档分类

---

### 6. 收支管理 (ActionController)

#### POST /action/addAction - 添加收支类型

**请求体：**
```json
{
    "hName": "收入",
    "exempt": false,
    "handle": 1
}
```

#### PUT /action/updateAction/{id} - 更新收支类型

#### GET /action/getAction - 获取全部收支类型

#### GET /action/getAction/{id} - 获取指定收支类型

---

### 7. 财务分析 (AnalysisController)

#### GET /analysis/doAnalysis?start={start}&end={end} - 财务分析

**查询参数：**
- `start`: 开始日期 (yyyy-MM-dd)
- `end`: 结束日期 (可选)

#### GET /analysis/exportExcel?start={start}&end={end} - 导出分析Excel

#### POST /analysis/v2/getAnalysisTypeList - 获取分类列表

**请求体：**
```json
{
    "start": "2024-01-01",
    "end": "2024-12-31",
    "combineSubType": false,
    "showDisableAnalysisType": false
}
```

#### POST /analysis/v2/getAnalysisTypeMonthData - 获取分类月度数据

---

### 8. 筛选功能 (ScreenController)

#### POST /screen/getFlowByScreen - 条件筛选流水

**请求体：**
```json
{
    "chooseHandle": 0,
    "accountId": 0,
    "startDate": "2024-01-01",
    "endDate": "2024-12-31",
    "isSingleMonth": false,
    "collect": false,
    "note": "",
    "actions": [1, 2],
    "types": [5, 6, 7]
}
```

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| chooseHandle | int | 0:全部, 1:支出, 2:收入 |
| accountId | int | 账户 ID，0 表示全部 |
| startDate | String | 开始日期 |
| endDate | String | 结束日期 |
| isSingleMonth | boolean | 是否单月模式 |
| collect | boolean | 只显示收藏 |
| note | String | 备注关键词 |
| actions | List<Integer> | 操作类型 ID 列表 |
| types | List<Integer> | 分类 ID 列表 |

#### POST /screen/makeExcel?excelName={name} - 生成筛选Excel

---

### 9. 快记模板 (FlowTemplateController)

#### POST /template/addTemplate - 添加模板

**请求体：**
```json
{
    "name": "工资",
    "dateType": 0,
    "money": "8000.00",
    "typeId": 10,
    "actionId": 1,
    "accountId": 1,
    "accountToId": null,
    "tagId": 1
}
```

#### PUT /template/updateTemplate - 更新模板

#### GET /template/getAllTemplates - 获取全部模板

#### GET /template/getAllTemplatesByTag/{tagId} - 按标签获取模板

#### GET /template/getTemplateById/{id} - 获取单个模板

#### DELETE /template/deleteTemplate/{id} - 删除模板

---

### 10. 模板标签管理 (TagController)

#### POST /tag/addTag - 添加标签

**请求体：**
```json
{
    "name": "日常",
    "color": "#FF5722"
}
```

#### PUT /tag/updateTag - 更新标签

#### GET /tag/getTags - 获取全部标签

#### GET /tag/getTag/{id} - 获取指定标签

#### DELETE /tag/deleteTag/{id} - 删除标签

---

### 11. 图片管理 (ImageController)

#### POST /image/upload - 上传图片

**请求：**
- Content-Type: `multipart/form-data`
- 参数: `file` (图片文件)

**限制：**
- 最大文件大小: 10MB
- 允许类型: image/*

**响应：**
```json
{
    "code": 0,
    "msg": "Success",
    "data": {
        "fileName": "20240115_103000_abc123.jpg"
    }
}
```

**错误码：**
- 400: 文件为空/文件过大/文件类型错误
- 500: 上传失败

#### GET /image/{fileName} - 获取图片

**路径参数：**
- `fileName`: 图片文件名

**响应：**
- Content-Type: image/jpeg | image/png | image/gif | image/webp
- 返回图片二进制数据

**注意：** 此接口无需认证

---

## DTO 数据定义

### 请求 DTO

#### FlowAddRequestDto
```java
public class FlowAddRequestDto {
    private String money;         // 金额
    private String fDate;         // 交易日期
    private String createDate;    // 创建时间
    private int actionId;         // 操作类型 ID
    private int accountId;        // 账户 ID
    private int accountToId;      // 目标账户 ID
    private int typeId;           // 分类 ID
    private boolean isCollect;    // 是否收藏
    private String note;          // 备注
    private String from;          // 来源标识
    private List<String> images;  // 图片列表
}
```

#### AccountRequestDto
```java
public class AccountRequestDto {
    private String name;          // 账户名称
    private String money;         // 余额
    private String exemptMoney;   // 免计金额
    private String card;          // 卡号
    private String note;          // 备注
}
```

#### TypeSingleDto
```java
public class TypeSingleDto {
    private int id;
    private String tName;         // 分类名称
    private Integer parent;       // 父分类 ID，-1 表示顶级
    private boolean disable;      // 是否禁用
    private Boolean archive;      // 是否归档
    private Integer actionId;     // 操作类型 ID
    private Boolean analysisDisable;  // 是否排除分析
}
```

#### ScreenFlowRequestDto
```java
public class ScreenFlowRequestDto {
    private int chooseHandle;     // 筛选类型
    private int accountId;        // 账户 ID
    private String startDate;     // 开始日期
    private String endDate;       // 结束日期
    private boolean isSingleMonth;// 单月模式
    private boolean collect;      // 只显示收藏
    private String note;          // 备注关键词
    private ArrayList<Integer> actions;  // 操作类型列表
    private ArrayList<Integer> types;    // 分类列表
}
```

#### AuthRequestDto
```java
public class AuthRequestDto {
    private String username;
    private String password;
}
```

#### FlowTemplateRequestDto
```java
public class FlowTemplateRequestDto {
    private Integer id;
    private String name;          // 模板名称
    private Integer dateType;     // 日期类型
    private String money;         // 预设金额
    private Integer typeId;       // 分类 ID
    private Integer actionId;     // 操作类型 ID
    private Integer accountId;    // 账户 ID
    private Integer accountToId;  // 目标账户 ID
    private Integer tagId;        // 标签 ID
}
```

### 响应 DTO

#### FlowListDto
```java
public class FlowListDto {
    private String totalIn;       // 总收入
    private String totalOut;      // 总支出
    private String totalEarn;     // 总结余
    private List<FlowTypeDto> typeList;  // 分类统计
    private List<FlowListSingleDto> flows;  // 流水列表

    public static class FlowListSingleDto {
        private int id;
        private String tName;     // 分类名称
        private String money;     // 金额
        private boolean exempt;   // 是否免计
        private boolean collect;  // 是否收藏
        private int handle;       // 操作类型
        private String hName;     // 操作名称
        private String note;      // 备注
        private String aName;     // 账户名称
        private String toAName;   // 目标账户名称
        private String fDate;     // 日期
        private String from;      // 来源
        private boolean hasImages;// 是否有图片
    }

    public static class FlowTypeDto {
        private String typeName;
        private String money;
        private int typeId;
        private boolean parent;
        private List<FlowTypeDto> children;
    }
}
```

#### HomeDto
```java
public class HomeDto {
    private String totalAsset;    // 总资产
    private String netAsset;      // 净资产
    private String curIncome;     // 当月收入
    private String curOutCome;    // 当月支出
    private String yearIncome;    // 年度收入
    private String yearOutCome;   // 年度支出
    private String yearBalance;   // 年度结余
    private List<HomeAccountBean> accounts;
    private List<HomeMonthDetailBean> monthDetails;

    public static class HomeAccountBean {
        private int id;
        private String accountName;
        private String accountAsset;
        private String exemptAsset;
        private String percent;
        private String note;
    }

    public static class HomeMonthDetailBean {
        private String month;
        private String income;
        private String outcome;
        private String balance;
    }
}
```

#### AuthDto
```java
public class AuthDto {
    private String token;  // 认证 Token
}
```

---

## 错误码说明

| HTTP 状态码 | 业务码 | 说明 |
|------------|--------|------|
| 200 | 0 | 成功 |
| 200 | 401 | 需要登录/密码错误 |
| 200 | 403 | 资源不存在 |
| 200 | 404 | 未找到 |
| 200 | 418 | 需要注册 |
| 200 | 500 | 服务器错误 |
| 400 | - | 请求参数错误 |
| 401 | - | 未授权（拦截器返回） |
| 418 | - | 需要注册（拦截器返回） |
| 500 | - | 服务器内部错误 |

---

## 相关文件路径

| 类型 | 路径 |
|------|------|
| 控制器 | `src/main/java/com/deepblue/yd_jz/controller/` |
| DTO | `src/main/java/com/deepblue/yd_jz/dto/` |
| 配置类 | `src/main/java/com/deepblue/yd_jz/config/` |
| 工具类 | `src/main/java/com/deepblue/yd_jz/utils/` |
| 配置文件 | `src/main/resources/application-*.properties` |
