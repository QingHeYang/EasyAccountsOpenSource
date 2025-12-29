import { getRequest } from './request'
import type { ApiResponse } from '../types'
import type { FlowListResult } from './flow'

/** 筛选请求参数 */
export interface ScreenFlowParams {
  /** 开始日期 */
  startDate?: string
  /** 结束日期 */
  endDate?: string
  /** 账户ID */
  accountId?: number
  /** 收支类型：0-流入 1-流出 2-内部转账 3-全部 */
  chooseHandle?: number
  /** 收支ID列表 */
  actions?: number[]
  /** 分类ID列表 */
  types?: number[]
  /** 是否只看收藏 */
  collect?: boolean
  /** 备注关键词 */
  note?: string
  /** 是否单月模式 */
  singleMonth?: boolean
}

/** 筛选功能 API */
export const screenApi = {
  /** 获取筛选结果 */
  getFlowByScreen(params: ScreenFlowParams) {
    return getRequest().post<ApiResponse<FlowListResult>>('/screen/getFlowByScreen', params)
  },

  /** 生成Excel */
  makeExcel(excelName: string, params: ScreenFlowParams) {
    return getRequest().post<ApiResponse<{ success: boolean; log: string }>>('/screen/makeExcel', params, {
      params: { excelName },
    })
  },

  /** 生成筛选Excel */
  makeScreenExcel(params: ScreenFlowParams) {
    return getRequest().post<ApiResponse<{ success: boolean; log: string }>>('/screen/makeScreenExcel', params)
  },
}
