# YDJZ Web V2

EasyAccounts 记账应用前端 V2 版本，支持 PC 端和移动端双端访问。

## 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 构建工具 | Vite | 7.x |
| 框架 | Vue | 3.5 |
| 语言 | TypeScript | 5.9 |
| 状态管理 | Pinia | 3.x |
| 路由 | Vue Router | 4.x |
| HTTP | Axios | 1.x |
| PC 端 UI | Element Plus | 2.x |
| 移动端 UI | Vant | 4.x |

## 项目结构

```
ydjz_web_v2/
├── src/
│   ├── desktop/                # PC 端
│   │   ├── views/              # 页面组件
│   │   ├── components/         # 业务组件
│   │   ├── layouts/            # 布局组件
│   │   ├── router.ts           # 路由配置
│   │   └── App.vue
│   │
│   ├── mobile/                 # 移动端（路由前缀 /m）
│   │   ├── views/
│   │   ├── components/
│   │   ├── layouts/
│   │   ├── router.ts
│   │   └── App.vue
│   │
│   ├── shared/                 # 共享代码
│   │   ├── api/                # API 模块（11个）
│   │   │   ├── request.ts      # Axios 封装
│   │   │   ├── auth.ts         # 认证
│   │   │   ├── account.ts      # 账户
│   │   │   ├── action.ts       # 收支
│   │   │   ├── type.ts         # 分类
│   │   │   ├── flow.ts         # 流水
│   │   │   ├── home.ts         # 首页
│   │   │   ├── analysis.ts     # 分析
│   │   │   ├── screen.ts       # 筛选
│   │   │   ├── tag.ts          # 标签
│   │   │   ├── template.ts     # 模板
│   │   │   ├── image.ts        # 图片
│   │   │   └── index.ts        # 统一导出
│   │   ├── types/              # 类型定义
│   │   ├── stores/             # Pinia stores
│   │   ├── utils/              # 工具函数
│   │   └── constants/          # 常量
│   │
│   ├── main-desktop.ts         # PC 端入口
│   ├── main-mobile.ts          # 移动端入口
│   └── env.d.ts                # 环境变量类型
│
├── docs/
│   ├── architecture.md         # 架构设计
│   ├── api/                    # API 文档
│   │   ├── README.md           # API 总览
│   │   ├── openapi.json        # OpenAPI 规范
│   │   └── *.md                # 各模块文档
│   └── old/                    # V1 业务逻辑文档
│
├── index.html                  # PC 端 HTML
├── mobile.html                 # 移动端 HTML
├── vite.config.ts              # Vite 配置
├── .env                        # 环境变量
└── package.json
```

## 快速开始

### 安装依赖

```bash
pnpm install
```

### 开发模式

```bash
pnpm dev
```

访问地址：
- PC 端：http://localhost:5173/
- 移动端：http://localhost:5173/m

### 构建生产版本

```bash
pnpm build
```

## 环境配置

### 开发环境

修改 `vite.config.ts` 中的代理目标：

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8080', // 后端地址
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, ''),
    },
  },
},
```

### 生产环境

Nginx 配置示例：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 移动端检测
    set $app_root /var/www/ydjz/desktop;
    if ($http_user_agent ~* "(Mobile|Android|iPhone|iPad)") {
        set $app_root /var/www/ydjz/mobile;
    }

    location / {
        root $app_root;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api/ {
        proxy_pass http://backend:8080/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 路径别名

| 别名 | 路径 |
|------|------|
| `@` | src/ |
| `@desktop` | src/desktop/ |
| `@mobile` | src/mobile/ |
| `@shared` | src/shared/ |

## API 使用

### 导入

```typescript
import { authApi, flowApi, homeApi } from '@shared/api'
import type { Flow, HomeInfo } from '@shared/api'
```

### 调用示例

```typescript
// 登录
const res = await authApi.login({ username: 'user', password: 'pass' })
if (res.data.code === 0) {
  localStorage.setItem('token', res.data.data.token)
}

// 获取流水列表
const flows = await flowApi.getMonthList(3, 0, '2024-01')

// 获取首页数据
const home = await homeApi.getHomeInfoByYear(2024)
```

### API 模块列表

| 模块 | 说明 | 接口数 |
|------|------|--------|
| authApi | 登录注册 | 2 |
| accountApi | 账户管理 | 6 |
| actionApi | 收支管理 | 4 |
| typeApi | 分类管理 | 10 |
| flowApi | 流水管理 | 7 |
| homeApi | 首页信息 | 3 |
| analysisApi | 财务分析 | 4 |
| screenApi | 筛选功能 | 3 |
| tagApi | 标签管理 | 5 |
| templateApi | 快记模板 | 6 |
| imageApi | 图片管理 | 2 |

详细文档见 [docs/api/README.md](./docs/api/README.md)

## 响应格式

所有 API 返回统一格式：

```typescript
interface ApiResponse<T> {
  code: number   // 0 成功，非 0 失败
  msg: string    // 提示信息
  data: T        // 业务数据
}
```

错误码：
- `0` - 成功
- `401` - 未登录/token 过期
- `418` - 未注册
- `4010/4011` - 需要验证

## 开发规范

### 文件命名

- 文件/目录：kebab-case（如 `flow-add.vue`）
- 组件名：PascalCase（如 `FlowAdd`）
- API/工具：camelCase（如 `flowApi`）

### 共享原则

| 共享（放 shared/） | 不共享（各端独立） |
|-------------------|-------------------|
| API 模块 | views 页面 |
| 类型定义 | components 组件 |
| Pinia stores | layouts 布局 |
| 工具函数 | router 路由 |
| 常量 | 样式 |

## 相关文档

- [架构设计](./docs/architecture.md)
- [API 文档](./docs/api/README.md)
- [V1 业务逻辑](./docs/old/README.md)

## License

MIT
