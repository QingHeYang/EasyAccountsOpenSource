# Copilot 指南 — ydjz_web_v2 前端仓库

目标：让自动化编码代理（Copilot / AI agent）快速上手并在本仓库安全、高效地完成改动。

- **工作目录**：所有活跃开发在 `ydjz_web_v2/` 下，`ydjz_web/` 为旧版，已弃用。
- **关键入口**：`ydjz_web_v2/src/main-desktop.ts`（PC），`ydjz_web_v2/src/main-mobile.ts`（移动）。

快速命令（开发者可直接使用）：

```
cd ydjz_web_v2
pnpm install
pnpm dev       # 启动 Vite 开发服务器（默认 5173）
pnpm build     # 生产构建，输出到 dist/
pnpm preview   # 预览构建产物
```

开发注意事项（对 AI 代理尤为重要）

- 架构分层：
  - `desktop/`：PC 端（Element Plus）相关代码和路由（`router.ts`）。
  - `mobile/`：移动端（Vant）相关代码和路由（`router.ts`）。
  - `shared/`：两端共享逻辑：`api/`（统一 Axios 配置）、`services/`（如 AI 聊天）、`stores/`、`utils/`、`types/`。

- 路由与页面：PC 根路径为 `/`；移动端挂载到 `/m`（访问移动端时在 URL 中加 `/m`）。参考：`desktop/router.ts`、`mobile/router.ts`。

- 接口约定（必须遵守）：
  - 返回格式：`{ code: number, msg: string, data: T }`。`code === 0` 表示成功。
  - API 模块位置：`src/shared/api/*.ts`（例如 `flowApi`, `accountApi`）。示例：`const { data } = await flowApi.getFlowList(params)`。

- 路径别名（导入示例）：
  - `@shared` => `src/shared/`
  - `@desktop` => `src/desktop/`
  - `@mobile`  => `src/mobile/`
  使用示例：`import { flowApi } from '@shared/api'`。

- 开发代理与本地后端（Vite）：请参考 `vite.config.ts` 中的 `proxy` 设置。开发中常见：
  - `/api` 指向后端 API
  - `/ai-api` 指向 AI 服务（WebSocket/REST）

- AI 功能与 WebSocket：AI 聊天服务位于 `src/shared/services/chat/`（例如 `chatService.ts`, `messageStore.ts`）。代理或变更与 AI 相关的网络路径时，请同时检查前端 `proxy` 与后端/ws 配置。

约定与变更规则（AI 代理必须遵守）

- 修改共享代码（`shared/`）时：
  1) 同时在 `desktop` 与 `mobile` 模式下进行功能回归测试（UI 可能不同）。
  2) 若改动影响 API 返回格式或字段，须更新 `ydjz_web_v2/docs/api/` 中对应文档。

- 样式与组件：PC 使用 Element Plus，移动端使用 Vant，避免在单个 view 中混用两套组件。

- 代码风格：
  - 文件/目录：kebab-case（例如 `flow-add.vue`）。
  - 组件名：PascalCase（例如 `FlowAdd`）。
  - API/工具：camelCase（例如 `flowApi`）。

定位重要文件（便于快速导航）

- 项目根说明：[ydjz_web_v2/README.md](ydjz_web_v2/README.md)
- 代理与配置：[vite.config.ts](ydjz_web_v2/vite.config.ts)
- AI 服务：[src/shared/services/chat/](ydjz_web_v2/src/shared/services/chat/)
- API 模块：[src/shared/api/](ydjz_web_v2/src/shared/api/)
- 入口：[src/main-desktop.ts](ydjz_web_v2/src/main-desktop.ts), [src/main-mobile.ts](ydjz_web_v2/src/main-mobile.ts)

当你不确定时（安全策略）

- 不要直接改动 `ydjz_web/`（旧版）。
- 对于影响后端契约的更改，先创建 issue 并在 PR 描述中标注需要更新的 `docs/api/*` 文件。
- 若需修改 Dockerfile 或 CI，优先通知维护者（当前仓库根 Dockerfile 指向旧版，需要升级以适配 `ydjz_web_v2`）。

变更提交建议（PR 模板要点）

- 简要说明改动范围（desktop / mobile / shared / api）
- 是否需要同步修改 `docs/api/*`（是/否）
- 若改动影响 AI/WS，请注明测试步骤与回归场景

参考：根目录 `CLAUDE.md` 包含更详尽的项目说明（架构、路由、API 列表、开发命令）。

---

如果你希望我把某一项扩展为更详细的代码导航或添加 PR 模板/检查清单，我可以继续补充。请指出优先项。
