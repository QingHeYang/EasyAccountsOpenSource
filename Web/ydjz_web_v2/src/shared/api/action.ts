import { getRequest } from './request'
import type { ApiResponse } from '../types'

/**
 * 内部转账豁免模式
 * 仅对内部转账（handle=2）生效，用于控制转账时哪个账户的金额变动不计入净资产
 */
export enum ExemptMode {
  /** 都不豁免（默认） */
  NONE = 0,
  /** 转出账户豁免 */
  FROM_EXEMPT = 1,
  /** 转入账户豁免（如还信用卡） */
  TO_EXEMPT = 2,
  /** 两边都豁免 */
  BOTH_EXEMPT = 3,
}

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
  /** 内部转账豁免模式（仅 handle=2 时生效） */
  exemptMode?: ExemptMode
}

/** 添加/更新收支参数 */
export interface ActionParams {
  hname: string
  handle: ActionHandle
  exempt?: boolean
  /** 内部转账豁免模式（仅 handle=2 时生效，默认0） */
  exemptMode?: ExemptMode
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
