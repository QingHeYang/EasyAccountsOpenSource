# YDJZ Web V2 架构设计

## 技术栈

- **构建**：Vite
- **框架**：Vue 3 + TypeScript + Pinia
- **UI**：Desktop (Element Plus) / Mobile (Vant)
- **请求**：Axios

## 架构方案

单应用双入口：一个项目，两套页面，共享核心代码。

## 目录结构

```
ydjz_web_v2/
├── src/
│   ├── desktop/              # PC 端
│   │   ├── views/
│   │   ├── components/
│   │   ├── layouts/
│   │   └── router.ts
│   │
│   ├── mobile/               # 移动端
│   │   ├── views/
│   │   ├── components/
│   │   ├── layouts/
│   │   └── router.ts
│   │
│   ├── shared/               # 共享代码
│   │   ├── api/              # API 封装
│   │   ├── types/            # 类型定义
│   │   ├── stores/           # Pinia stores
│   │   ├── utils/            # 工具函数
│   │   └── constants/        # 常量
│   │
│   ├── main-desktop.ts       # PC 端入口
│   └── main-mobile.ts        # 移动端入口
│
├── index.html                # PC 端 HTML
├── mobile.html               # 移动端 HTML
├── vite.config.ts
├── docs/
└── package.json
```

## 双端切换

Nginx 根据 User-Agent 重定向到对应入口：
- PC 访问 → `index.html`
- 移动端访问 → `mobile.html`

## 共享原则

- **共享**：API、类型、stores、工具函数、常量
- **不共享**：views、components、layouts、router
