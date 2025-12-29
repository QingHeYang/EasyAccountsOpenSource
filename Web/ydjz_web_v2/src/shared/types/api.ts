/**
 * API 通用响应格式
 */
export interface ApiResponse<T = unknown> {
  /** 状态码，0 表示成功 */
  code: number
  /** 提示信息 */
  msg: string
  /** 业务数据 */
  data: T
}

/**
 * 分页请求参数
 */
export interface PageParams {
  page?: number
  size?: number
}

/**
 * 分页响应数据
 */
export interface PageData<T> {
  list: T[]
  total: number
  page: number
  size: number
}

/**
 * API 错误码
 */
export enum ApiCode {
  /** 成功 */
  SUCCESS = 0,
  /** 未登录/token过期 */
  UNAUTHORIZED = 401,
  /** 未注册 */
  NOT_REGISTERED = 418,
  /** 需要验证 */
  NEED_VERIFY = 4010,
  /** 需要验证 */
  NEED_VERIFY_2 = 4011,
}

/**
 * 判断响应是否成功
 */
export function isSuccess<T>(response: ApiResponse<T>): boolean {
  return response.code === ApiCode.SUCCESS
}
