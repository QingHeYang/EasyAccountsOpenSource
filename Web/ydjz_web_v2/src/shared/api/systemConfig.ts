import { getRequest } from './request'
import type { ApiResponse } from '../types'
import type { ReminderConfig } from './scheduledFlow'

/* ============================================================
 * 系统设置（v2.7.0 新增 / 接管 v2.6.x 老接口）
 *
 * 后端把所有"管理员级配置"统一收口在 /system/config/* 下，
 * 前端按域分接口；overview 接口一处拿全部 5 域用于设置首页。
 *
 * - mail：邮件 SMTP / 收件人 / 全局开关
 * - backup：自动 SQL 备份调度
 * - auth：认证（登录开关 / 单点 / token 时长）
 * - scheduledFlow：定时记账事前提醒（站内 + 邮件触发时点）
 * - autoExcel：自动月度 Excel 生成 + 提前提醒
 *
 * partial update：所有 PUT 都是"未传字段不修改"，只发改动字段即可。
 * ============================================================ */

/* ---------- 1. mail ---------- */

/** 邮件配置（GET 响应）
 *
 * - password：始终为空字符串，用 isPasswordSet 判断密码是否已设置
 * - smtpPort：字符串（不是 number），常用 "465"(SMTPS) / "587"(STARTTLS) / "25"
 * - toList：逗号分隔多邮箱
 */
export interface MailConfig {
  smtpServer: string
  smtpPort: string
  fromEmail: string
  /** 始终为空，看 isPasswordSet 判断 */
  password: string
  /** 是否已设置密码（前端展示「已设置」/「未设置」用） */
  isPasswordSet: boolean
  toList: string
  /** SQL 备份邮件全局开关 */
  sendSqlBackup: boolean
  /** Excel 邮件全局开关（覆盖月度 / 筛选 等 Excel） */
  sendExcel: boolean
}

/** 更新邮件配置（partial）
 *
 * - password：null/undefined=不修改；""=清空已设置的密码；其它=明文，后端加密入库
 * - 其它字段：传 = 修改；不传 = 不动
 */
export interface MailConfigUpdate {
  smtpServer?: string
  smtpPort?: string
  fromEmail?: string
  password?: string | null
  toList?: string
  sendSqlBackup?: boolean
  sendExcel?: boolean
}

/** 测试发邮件结果 */
export interface SendResult {
  success: boolean
  /** SMTP 异常文本（success=false 时给前端展示） */
  message: string
}

/* ---------- 2. backup（自动 SQL 备份调度） ---------- */

/** 备份频率枚举（字符串） */
export type BackupFrequency = 'daily' | 'weekly' | 'monthly'

/** 备份配置（GET 响应） */
export interface BackupConfig {
  enabled: boolean
  frequency: BackupFrequency
  /** "HH:mm" 24 小时制，例 "22:00" */
  time: string
  /** 1-7（1=周一，7=周日，ISO），仅 frequency=weekly 用 */
  dayOfWeek: number
  /** 1-28，仅 frequency=monthly 用（避免 2 月跳月） */
  dayOfMonth: number
  /** 后端拼出的 cron 表达式，前端展示 / 调试用 */
  cron: string
}

/** 更新备份配置（partial） */
export interface BackupConfigUpdate {
  enabled?: boolean
  frequency?: BackupFrequency
  time?: string
  dayOfWeek?: number
  dayOfMonth?: number
}

/* ---------- 3. auth（认证） ---------- */

/** 认证配置 */
export interface AuthConfig {
  /** 是否启用登录功能 */
  loginEnable: boolean
  /** true=新登录踢旧设备；false=多设备共享 Token */
  singleLogin: boolean
  /** Token 过期时间（分钟） */
  tokenExpiredMinutes: number
}

/** 更新认证配置（partial） */
export interface AuthConfigUpdate {
  loginEnable?: boolean
  singleLogin?: boolean
  tokenExpiredMinutes?: number
}

/* ---------- 4. scheduledFlow（定时记账提醒） ---------- */

/* ReminderConfig 类型沿用 scheduledFlow.ts 中的定义（remindBeforeDays + remindTime） */

/* ---------- 5. autoExcel（自动月度 Excel） ---------- */

/** 自动月度 Excel 生成目标
 *
 * - LAST_MONTH：每月生成"上个月"的报表（典型场景：月初统计上月）
 * - CURRENT_MONTH：每月生成"本月"的报表
 */
export type AutoExcelTarget = 'LAST_MONTH' | 'CURRENT_MONTH'

/** 自动月度 Excel 配置（GET 响应）
 *
 * 含 3 个后端计算出的展示字段（PUT 时不需传）：
 * - lastRunDate / nextRunDate：上次/下次执行日期
 * - targetYearMonth：本次将生成的目标月（YYYY-MM）
 */
export interface AutoExcelConfig {
  enabled: boolean
  /** 1-28 */
  dayOfMonth: number
  /** "HH:mm"，例 "21:00" */
  time: string
  target: AutoExcelTarget
  /** 生成成功后是否邮件发送（独立于 mail.sendExcel 全局开关） */
  sendEmail: boolean
  /** 是否提前提醒（总开关） */
  remindEnabled: boolean
  /** 提前 N 天，1-28；remindEnabled=false 时忽略 */
  remindBeforeDays: number
  /**
   * 提醒是否邮件发送。
   * remindEnabled=false 时忽略；
   * remindEnabled=true 时站内通知必发，邮件按这个开关。
   */
  remindEmailEnabled: boolean
  /** 上次执行日期（后端计算） */
  lastRunDate?: string
  /** 下次执行日期（后端计算） */
  nextRunDate?: string
  /** 本次将生成的目标月 YYYY-MM（后端计算） */
  targetYearMonth?: string
}

/** 更新自动月度 Excel 配置（partial） */
export interface AutoExcelConfigUpdate {
  enabled?: boolean
  dayOfMonth?: number
  time?: string
  target?: AutoExcelTarget
  sendEmail?: boolean
  remindEnabled?: boolean
  remindBeforeDays?: number
  remindEmailEnabled?: boolean
}

/* ---------- 6. overview（5 域聚合，设置首页一次拿全） ---------- */

/** 邮件 overview（不含 password / 完整 toList，只暴露收件人数量） */
export interface MailOverview {
  /** 是否已配置（smtpServer/fromEmail/密码 / toList 都齐） */
  isConfigured: boolean
  smtpServer: string
  fromEmail: string
  /** 收件人数量（不暴露具体邮箱） */
  toListCount: number
  sendSqlBackup: boolean
  sendExcel: boolean
}

/** 备份 overview（含人类可读描述） */
export interface BackupOverview extends BackupConfig {
  /** 例 "每日 22:00 自动备份" */
  humanReadable: string
}

/** 认证 overview（与 AuthConfig 同结构） */
export type AuthOverview = AuthConfig

/** 定时记账 overview（与 ReminderConfig 同结构） */
export type ScheduledFlowOverview = ReminderConfig

/** 自动 Excel overview（含人类可读描述） */
export interface AutoExcelOverview extends AutoExcelConfig {
  /** 例 "每月 1 号 21:00 生成上月 Excel，提前 3 天站内+邮件提醒" */
  humanReadable: string
}

/** 系统配置整体 overview（5 域聚合） */
export interface SystemConfigOverview {
  mail: MailOverview
  backup: BackupOverview
  auth: AuthOverview
  scheduledFlow: ScheduledFlowOverview
  autoExcel: AutoExcelOverview
}

/* ============================================================
 * API
 * ============================================================ */

export const systemConfigApi = {
  /** 5 域整体概览（设置首页推荐用这个，少一次往返） */
  getOverview() {
    return getRequest().get<ApiResponse<SystemConfigOverview>>(
      '/system/config/overview'
    )
  },

  /* ---- mail ---- */

  /** 读邮件配置 */
  getMail() {
    return getRequest().get<ApiResponse<MailConfig>>('/system/config/mail')
  },

  /** 更新邮件配置（partial） */
  updateMail(params: MailConfigUpdate) {
    return getRequest().put<ApiResponse<MailConfig>>(
      '/system/config/mail',
      params
    )
  },

  /** 测试发一封测试邮件给收件人列表，把 SMTP 异常文本返回前端 */
  testMail() {
    return getRequest().post<ApiResponse<SendResult>>(
      '/system/config/mail/test',
      null,
      { timeout: 30000 }
    )
  },

  /**
   * 一键测试所有 8 类邮件（验证 HTML 模板渲染）
   *
   * ⚠️ 后端要求 mail.sendSqlBackup / sendExcel 都为 true，否则跳过对应模板。
   * 通常只在开发期使用，生产前端不用挂这个按钮。
   */
  testAllMails() {
    return getRequest().post<
      ApiResponse<Array<Record<string, unknown>>>
    >('/system/config/mail/testAll', null, { timeout: 60000 })
  },

  /* ---- backup（自动备份调度） ---- */

  /** 读自动备份调度配置 */
  getBackup() {
    return getRequest().get<ApiResponse<BackupConfig>>(
      '/system/config/backup'
    )
  },

  /** 更新自动备份调度（partial）；变更后后端自动重排 cron，无需重启 */
  updateBackup(params: BackupConfigUpdate) {
    return getRequest().put<ApiResponse<BackupConfig>>(
      '/system/config/backup',
      params
    )
  },

  /* ---- auth ---- */

  /** 读认证配置 */
  getAuth() {
    return getRequest().get<ApiResponse<AuthConfig>>('/system/config/auth')
  },

  /** 更新认证配置（partial）；切换登录开关后下一个请求即生效，无需重启 */
  updateAuth(params: AuthConfigUpdate) {
    return getRequest().put<ApiResponse<AuthConfig>>(
      '/system/config/auth',
      params
    )
  },

  /* ---- scheduledFlow（定时记账事前提醒） ---- */

  /** 读定时记账全局提醒配置 */
  getScheduledFlow() {
    return getRequest().get<ApiResponse<ReminderConfig>>(
      '/system/config/scheduledFlow'
    )
  },

  /** 更新定时记账全局提醒配置（remindBeforeDays 1-5；remindTime "HH:mm"） */
  updateScheduledFlow(params: ReminderConfig) {
    return getRequest().put<ApiResponse<ReminderConfig>>(
      '/system/config/scheduledFlow',
      params
    )
  },

  /* ---- autoExcel（自动月度 Excel） ---- */

  /** 读自动月度 Excel 配置（含计算字段 nextRunDate / targetYearMonth） */
  getAutoExcel() {
    return getRequest().get<ApiResponse<AutoExcelConfig>>(
      '/system/config/autoExcel'
    )
  },

  /** 更新自动月度 Excel 配置（partial）；变更后调度自动重排，无需重启 */
  updateAutoExcel(params: AutoExcelConfigUpdate) {
    return getRequest().put<ApiResponse<AutoExcelConfig>>(
      '/system/config/autoExcel',
      params
    )
  },

  /** 立即触发一次生成（不等下次 cron）。生成耗时较长，前端给 60s 超时 */
  runAutoExcelNow() {
    return getRequest().post<ApiResponse<void>>(
      '/system/config/autoExcel/runNow',
      null,
      { timeout: 60000 }
    )
  },

  /** 立即派发一次提醒（用于测试；走防重逻辑，已发过则不重发） */
  sendAutoExcelReminderNow() {
    return getRequest().post<ApiResponse<void>>(
      '/system/config/autoExcel/sendReminder'
    )
  },
}
