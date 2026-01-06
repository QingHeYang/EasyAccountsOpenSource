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

/**
 * API 错误类型
 */
export class ApiError extends Error {
  /** 错误码 */
  code: number
  /** 是否为认证错误（已由拦截器处理，业务代码可忽略） */
  isAuthError: boolean
  /** 是否已全局处理（业务代码可忽略） */
  handled: boolean

  constructor(code: number, message: string, isAuthError = false, handled = false) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.isAuthError = isAuthError
    this.handled = handled
  }
}

/**
 * 判断是否为认证错误（业务代码可用此判断是否需要显示错误提示）
 */
export function isAuthError(error: unknown): boolean {
  return error instanceof ApiError && error.isAuthError
}

/**
 * 判断错误是否已被全局处理
 */
export function isHandledError(error: unknown): boolean {
  return error instanceof ApiError && error.handled
}

/**
 * 需要跳转登录页的错误码
 * 注意：不含 401，因为登录接口用 401 表示密码错误
 */
const AUTH_ERROR_CODES = [
  ApiCode.NOT_REGISTERED,  // 418
  ApiCode.NEED_VERIFY,     // 4010
  ApiCode.NEED_VERIFY_2,   // 4011
]

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

      // 认证相关错误（418/4010/4011）- 需要跳转登录页
      if (AUTH_ERROR_CODES.includes(code)) {
        // 418 未注册时清除 token
        if (code === ApiCode.NOT_REGISTERED) {
          localStorage.removeItem('token')
        }
        // 调用认证错误回调（跳转登录页等）
        globalHandlers.onUnauthorized?.(code)
        // 抛出认证错误，标记为已处理，业务代码可忽略
        return Promise.reject(new ApiError(code, '登录已过期，请重新登录', true, true))
      }

      // 其他业务错误 - 调用全局错误回调
      globalHandlers.onError?.(code, msg)
      // 抛出业务错误，标记为已全局处理
      return Promise.reject(new ApiError(code, msg, false, true))
    },
    (error) => {
      const status = error.response?.status
      const data = error.response?.data as ApiResponse | undefined
      const msg = data?.msg || error.response?.statusText || error.message || '网络错误'

      // HTTP 401/418 - 认证错误
      if (status === 401 || status === 418) {
        localStorage.removeItem('token')
        globalHandlers.onUnauthorized?.(status)
        return Promise.reject(new ApiError(status, '登录已过期，请重新登录', true, true))
      }

      // 其他 HTTP 错误
      globalHandlers.onError?.(status || 0, msg)
      return Promise.reject(new ApiError(status || 0, msg, false, true))
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
