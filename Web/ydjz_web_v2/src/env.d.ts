/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** 后端 API 基础路径 */
  readonly VITE_API_BASE_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

/** 运行时配置（来自 public/config.js） */
interface AppConfig {
  /** 后端 API 基础路径 */
  apiBaseUrl?: string
  /** AI 服务基础路径 */
  aiApiUrl?: string
  /** WebSocket 基础路径 */
  wsBaseUrl?: string
}

declare global {
  interface Window {
    config?: AppConfig
  }
}

export {}
