import axios, { type AxiosInstance, type AxiosResponse } from 'axios'
import { ApiCode, type ApiResponse } from '../types'

/**
 * 未授权回调类型
 */
export type UnauthorizedHandler = (code: number, redirectPath?: string) => void

/**
 * 错误回调类型
 */
export type ErrorHandler = (code: number, msg: string) => void

/**
 * 请求配置选项
 */
export interface RequestOptions {
  /** API 基础地址 */
  baseURL: string
  /** 超时时间（毫秒） */
  timeout?: number
  /** 未授权回调（401/418/4010/4011） */
  onUnauthorized?: UnauthorizedHandler
  /** 错误回调 */
  onError?: ErrorHandler
}

/** 全局请求实例 */
let requestInstance: AxiosInstance | null = null

/** 全局回调 */
let globalHandlers: {
  onUnauthorized?: UnauthorizedHandler
  onError?: ErrorHandler
} = {}

/**
 * 创建 Axios 实例（内部使用）
 */
function createAxiosInstance(baseURL: string, timeout: number): AxiosInstance {
  const instance = axios.create({
    baseURL,
    timeout,
  })

  // 请求拦截器
  instance.interceptors.request.use(
    (config) => {
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
    (response: AxiosResponse<ApiResponse>) => {
      const { code, msg } = response.data

      // 成功
      if (code === ApiCode.SUCCESS) {
        return response
      }

      // 未登录/token过期
      if (code === ApiCode.UNAUTHORIZED) {
        localStorage.removeItem('token')
        globalHandlers.onUnauthorized?.(code)
        return response
      }

      // 未注册
      if (code === ApiCode.NOT_REGISTERED) {
        localStorage.removeItem('token')
        globalHandlers.onUnauthorized?.(code)
        return response
      }

      // 需要验证
      if (code === ApiCode.NEED_VERIFY || code === ApiCode.NEED_VERIFY_2) {
        globalHandlers.onUnauthorized?.(code)
        return response
      }

      // 其他业务错误
      globalHandlers.onError?.(code, msg)
      return response
    },
    (error) => {
      const status = error.response?.status
      const msg = error.response?.statusText || error.message

      // HTTP 401
      if (status === 401) {
        localStorage.removeItem('token')
        globalHandlers.onUnauthorized?.(401)
      }
      // HTTP 418
      else if (status === 418) {
        localStorage.removeItem('token')
        globalHandlers.onUnauthorized?.(418)
      }
      // 其他 HTTP 错误
      else {
        globalHandlers.onError?.(status || 0, msg)
      }

      return Promise.reject(error)
    }
  )

  return instance
}

/**
 * 初始化请求实例
 * 在各端的 main.ts 中调用
 */
export function setupRequest(options: RequestOptions): void {
  requestInstance = createAxiosInstance(
    options.baseURL,
    options.timeout ?? 10000
  )

  globalHandlers = {
    onUnauthorized: options.onUnauthorized,
    onError: options.onError,
  }
}

/**
 * 获取请求实例
 */
export function getRequest(): AxiosInstance {
  if (!requestInstance) {
    throw new Error('Request not initialized. Call setupRequest() first.')
  }
  return requestInstance
}

/**
 * 更新回调处理器（可选，用于动态更新）
 */
export function setHandlers(handlers: {
  onUnauthorized?: UnauthorizedHandler
  onError?: ErrorHandler
}): void {
  globalHandlers = { ...globalHandlers, ...handlers }
}
