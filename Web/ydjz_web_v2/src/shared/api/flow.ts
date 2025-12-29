import { getRequest } from './request'
import type { ApiResponse } from '../types'
import type { Account } from './account'
import type { Action } from './action'
import type { TypeWithChildren } from './type'

/** 流水操作类型 */
export enum FlowHandle {
  /** 流入 */
  IN = 0,
  /** 流出 */
  OUT = 1,
  /** 内部转账 */
  TRANSFER = 2,
}

/** 流水列表单条记录 */
export interface Flow {
  id: number
  /** 金额 */
  money: string
  /** 日期 */
  fdate: string
  /** 分类名称 */
  tname: string
  /** 账户名称 */
  aname: string
  /** 收支名称 */
  hname: string
  /** 收支类型 0-流入 1-流出 2-转账 */
  handle: FlowHandle
  /** 备注 */
  note?: string
  /** 是否收藏 */
  collect: boolean
  /** 是否不计入统计 */
  exempt: boolean
  /** 是否有图片 */
  hasImages: boolean
  /** 来源 */
  from?: string
  /** 转账目标账户名称 */
  toAName?: string
}

/** 流水详情（getById 返回） */
export interface FlowDetail {
  id: number
  money: string
  fdate: string
  note?: string
  collect: boolean
  from?: string
  images?: string[]
  /** 完整账户信息 */
  account: Account
  /** 转账目标账户 */
  accountTo?: Account
  /** 完整收支信息 */
  action: Action
  /** 完整分类信息 */
  type: TypeWithChildren
}

/** 分类金额汇总 */
export interface FlowTypeDto {
  typeId: number
  typeName: string
  money: string
  parent: boolean
  children?: FlowTypeDto[]
}

/** 流水列表响应 */
export interface FlowListResult {
  flows: Flow[]
  /** 总收入 */
  totalIn: string
  /** 总支出 */
  totalOut: string
  /** 结余 */
  totalEarn: string
  /** 分类汇总 */
  typeList?: FlowTypeDto[]
}

/** 添加/更新流水参数 */
export interface FlowParams {
  money: string
  fDate: string
  actionId: number
  accountId: number
  accountToId?: number
  typeId: number
  collect?: boolean
  note?: string
  images?: string[]
  createDate?: string
  from?: string
}

/** @deprecated 使用 FlowParams */
export type AddFlowParams = FlowParams

/** 流水 API */
export const flowApi = {
  /** 获取月度流水列表 */
  getMonthList(handle: number, order: number, month: string) {
    return getRequest().get<ApiResponse<FlowListResult>>(
      `/flow/getFlowListMain/${handle}/${order}/${month}`
    )
  },

  /** 获取单条流水详情 */
  getById(id: number) {
    return getRequest().get<ApiResponse<FlowDetail>>(`/flow/getFlow/${id}`)
  },

  /** 添加流水 */
  add(params: AddFlowParams) {
    return getRequest().post<ApiResponse<Flow>>('/flow/addFlow', params)
  },

  /** 更新流水 */
  update(id: number, params: AddFlowParams) {
    return getRequest().put<ApiResponse<Flow>>(`/flow/updateFlow/${id}`, params)
  },

  /** 删除流水 */
  delete(id: number) {
    return getRequest().delete<ApiResponse<void>>(`/flow/deleteFlow/${id}`)
  },

  /** 收藏/取消收藏 */
  toggleCollect(id: number, collect: boolean) {
    return getRequest().put<ApiResponse<void>>(
      `/flow/collectFlow/${id}/${collect ? 1 : 0}`
    )
  },

  /** 生成月度报表 */
  makeExcel(month: string) {
    return getRequest().get<ApiResponse<{ success: boolean; log: string }>>(
      `/flow/makeExcel/${month}`
    )
  },
}
