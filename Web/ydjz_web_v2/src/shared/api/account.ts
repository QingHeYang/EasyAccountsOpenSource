import { getRequest } from './request'
import type { ApiResponse } from '../types'

/** 账户信息（响应） */
export interface Account {
  id: number
  /** 账户名称 */
  name: string
  /** 账户余额 */
  money: string
  /** 不计入资产金额 */
  exemptMoney?: string
  /** 卡号 */
  card?: string
  /** 备注 */
  note?: string
  /** 创建时间 */
  createTime?: string
}

/** 添加/更新账户参数（请求） */
export interface AccountParams {
  /** 账户名称 */
  name: string
  /** 账户余额 */
  money?: string
  /** 不计入资产金额 */
  exemptMoney?: string
  /** 卡号 */
  card?: string
  /** 备注 */
  note?: string
}

/** @deprecated 使用 AccountParams */
export type AddAccountParams = AccountParams
/** @deprecated 使用 AccountParams */
export type UpdateAccountParams = AccountParams

/** 账户 API */
export const accountApi = {
  /** 获取全部账户 */
  getAll() {
    return getRequest().get<ApiResponse<Account[]>>('/account/getAccount')
  },

  /** 获取全部账户（无限制） */
  getAllNoLimit() {
    return getRequest().get<ApiResponse<Account[]>>('/account/getAccountNoLimit')
  },

  /** 获取指定账户 */
  getById(id: number) {
    return getRequest().get<ApiResponse<Account>>(`/account/getAccount/${id}`)
  },

  /** 添加账户 */
  add(params: AddAccountParams) {
    return getRequest().post<ApiResponse<Account>>('/account/addAccount', params)
  },

  /** 更新账户 */
  update(id: number, params: UpdateAccountParams) {
    return getRequest().put<ApiResponse<Account>>(`/account/updateAccount/${id}`, params)
  },

  /** 停用账户 */
  delete(id: number) {
    return getRequest().delete<ApiResponse<void>>(`/account/deleteAccount/${id}`)
  },
}
