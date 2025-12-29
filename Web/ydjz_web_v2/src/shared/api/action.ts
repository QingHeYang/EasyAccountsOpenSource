import { getRequest } from './request'
import type { ApiResponse } from '../types'

/** 收支操作类型 */
export enum ActionHandle {
  /** 流入（账户金额增加） */
  IN = 0,
  /** 流出（账户金额减少） */
  OUT = 1,
  /** 内部转账（账户金额不变） */
  TRANSFER = 2,
}

/** 收支类型 */
export interface Action {
  id: number
  /** 收支名称 */
  hname: string
  /** 操作类型：0-流入 1-流出 2-内部转账 */
  handle: ActionHandle
  /** 是否不计入总金额 */
  exempt: boolean
}

/** 添加/更新收支参数 */
export interface ActionParams {
  hname: string
  handle: ActionHandle
  exempt?: boolean
}

/** 收支管理 API */
export const actionApi = {
  /** 获取全部收支 */
  getAll() {
    return getRequest().get<ApiResponse<Action[]>>('/action/getAction')
  },

  /** 获取指定收支 */
  getById(id: number) {
    return getRequest().get<ApiResponse<Action>>(`/action/getAction/${id}`)
  },

  /** 添加收支 */
  add(params: ActionParams) {
    return getRequest().post<ApiResponse<void>>('/action/addAction', params)
  },

  /** 更新收支 */
  update(id: number, params: ActionParams) {
    return getRequest().put<ApiResponse<void>>(`/action/updateAction/${id}`, params)
  },
}
