import { getRequest } from './request'
import type { ApiResponse } from '../types'

/** 首页账户信息 */
export interface HomeAccount {
  id: number
  accountName: string
  accountAsset: string
  exemptAsset: string
  note: string
  percent: string
}

/** 月度明细 */
export interface HomeMonthDetail {
  month: string
  income: string
  outcome: string
  balance: string
}

/** 首页数据 */
export interface HomeInfo {
  /** 账户列表 */
  accounts: HomeAccount[]
  /** 当月收入 */
  curIncome: string
  /** 当月支出 */
  curOutCome: string
  /** 月度明细列表 */
  monthDetails: HomeMonthDetail[]
  /** 净资产 */
  netAsset: string
  /** 总资产 */
  totalAsset: string
  /** 年度结余 */
  yearBalance: string
  /** 年度收入 */
  yearIncome: string
  /** 年度支出 */
  yearOutCome: string
}

/** 版本信息 */
export interface VersionInfo {
  /** 总版本号 */
  release: string
  /** 前端版本 */
  fontBranch: string
  /** 后端版本 */
  backendBranch: string
  /** 数据库版本 */
  mysqlBranch: string
  /** AI Agent 版本 */
  agentBranch: string
  /** WebHook 版本 */
  webhookBranch: string
}

/** 首页 API */
export const homeApi = {
  /** 获取首页信息 */
  getHomeInfo() {
    return getRequest().get<ApiResponse<HomeInfo>>('/home/getHomeInfo')
  },

  /** 获取首页信息（指定年份） */
  getHomeInfoByYear(year: number) {
    return getRequest().get<ApiResponse<HomeInfo>>(`/home/getHomeInfoV2/${year}`)
  },

  /** 获取版本信息 */
  getVersion() {
    return getRequest().get<ApiResponse<VersionInfo>>('/home/getVersion')
  },
}
