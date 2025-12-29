/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** API 基础地址 */
  readonly VITE_API_BASE_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

/** 运行时配置 */
interface RuntimeConfig {
  /** 主 API 地址（记账服务，端口 10672） */
  apiBaseUrl: string
  /** AI API 地址（AI 服务，端口 10680） */
  readonly aiApiUrl: string
  /** AI WebSocket 地址 */
  readonly aiWebSocketUrl: string
}

declare global {
  interface Window {
    config: RuntimeConfig
  }
}
