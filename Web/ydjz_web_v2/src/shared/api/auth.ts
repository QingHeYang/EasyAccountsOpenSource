import { getRequest } from './request'
import type { ApiResponse } from '../types'

/** 登录参数 */
export interface LoginParams {
  username: string
  password: string
}

/** 登录响应 */
export interface LoginResult {
  token: string
}

/** 认证 API */
export const authApi = {
  /** 登录 */
  login(params: LoginParams) {
    return getRequest().post<ApiResponse<LoginResult>>('/auth/login', params)
  },

  /** 注册 */
  register(params: LoginParams) {
    return getRequest().post<ApiResponse<LoginResult>>('/auth/register', params)
  },
}
