import axios, { type AxiosInstance, type AxiosResponse } from 'axios'

/**
 * AI 请求配置选项
 */
export interface AiRequestOptions {
  /** 超时时间（毫秒） */
  timeout?: number
  /** 错误回调 */
  onError?: (status: number, msg: string) => void
}

/** AI 请求实例 */
let aiRequestInstance: AxiosInstance | null = null

/** 错误回调 */
let errorHandler: ((status: number, msg: string) => void) | undefined

/**
 * 获取 AI API 基础地址
 */
function getAiApiUrl(): string {
  return window.config?.aiApiUrl || '/ai-api'
}

/**
 * 创建 AI Axios 实例
 */
function createAiAxiosInstance(timeout: number): AxiosInstance {
  const instance = axios.create({
    baseURL: getAiApiUrl(),
    timeout,
  })

  // 请求拦截器
  instance.interceptors.request.use(
    (config) => {
      // 动态更新 baseURL（支持运行时配置变化）
      config.baseURL = getAiApiUrl()

      const token = localStorage.getItem('token')
      if (token) {
        config.headers.Authorization = token
      }
      return config
    },
    (error) => Promise.reject(error)
  )

  // 响应拦截器
  instance.interceptors.response.use(
    (response: AxiosResponse) => response,
    (error) => {
      const status = error.response?.status
      const msg = error.response?.data?.message || error.response?.statusText || error.message

      errorHandler?.(status || 0, msg)
      return Promise.reject(error)
    }
  )

  return instance
}

/**
 * 初始化 AI 请求实例
 */
export function setupAiRequest(options?: AiRequestOptions): void {
  aiRequestInstance = createAiAxiosInstance(options?.timeout ?? 30000)
  errorHandler = options?.onError
}

/**
 * 获取 AI 请求实例
 */
export function getAiRequest(): AxiosInstance {
  if (!aiRequestInstance) {
    // 如果未初始化，自动初始化（使用默认配置）
    setupAiRequest()
  }
  return aiRequestInstance!
}

/**
 * 获取 AI WebSocket 地址
 */
export function getAiWebSocketUrl(): string {
  return window.config?.aiWebSocketUrl || `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ai-api`
}
