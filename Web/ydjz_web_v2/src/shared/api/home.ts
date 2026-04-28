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
  /** 版本码 */
  versionCode: number
  /** 前端版本 */
  fontBranch: string
  /** 后端版本 */
  backendBranch: string
  /** 数据库版本 */
  mysqlBranch: string
  /** AI Agent 版本 */
  agentBranch: string
}

/** 更新信息 */
export interface UpdateInfo {
  /** 新版本号 */
  version: string
  /** 新版本码 */
  versionCode: number
  /** 发布日期 */
  releaseDate: string
  /** 更新内容（Markdown） */
  changelog: string
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

/** 系统配置（版本 + 认证 + 备份 + 更新） */
export interface SystemConfig {
  versions: VersionInfo
  auth: AuthConfig
  backup: BackupConfig
  /** 更新信息（有新版本时返回，无更新时为 null） */
  update: UpdateInfo | null
}

/** 公告信息 */
export interface Notice {
  /** 公告唯一标识 */
  id: number
  /** 公告标题 */
  title: string
  /** 公告内容 */
  content: string
  /** 发布日期 (yyyy-MM-dd) */
  date: string
  /** 跳转链接，空则无链接 */
  url: string
  /** 过期日期，空则永不过期 */
  expire: string
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

  /** 获取公告列表（自动过滤已过期公告） */
  getNotices() {
    return getRequest().get<ApiResponse<Notice[]>>('/home/getNotices')
  },
}
