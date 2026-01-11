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
  /** 账户类型：0=资产，1=负债 */
  accountType?: number
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

/** 认证配置 */
export interface AuthConfig {
  /** 是否启用认证 */
  enable: boolean
  /** Token 过期时间（分钟） */
  expiredMinutes: number
  /** 是否单点登录 */
  singleLogin: boolean
}

/** 备份配置 */
export interface BackupConfig {
  /** Cron 表达式 */
  cron: string
  /** 配置是否有效 */
  valid: boolean
  /** 描述信息 */
  description: string
}

/** 系统配置（版本 + 认证 + 备份） */
export interface SystemConfig {
  versions: VersionInfo
  auth: AuthConfig
  backup: BackupConfig
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

  /** 获取系统配置（版本 + 认证） */
  getSystemConfig() {
    return getRequest().get<ApiResponse<SystemConfig>>('/home/getVersion')
  },
}
