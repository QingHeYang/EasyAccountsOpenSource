import { getRequest } from './request'
import type { ApiResponse } from '../types'

/** 周期类型 */
export enum CycleType {
  /** 每日 */
  DAILY = 1,
  /** 每周（ISO：周一=1 … 周日=7） */
  WEEKLY = 2,
  /** 每月（1-31；31 号遇 2 月后端自动回退月末） */
  MONTHLY = 3,
  /** 每年（MM-DD，两位数补零） */
  YEARLY = 4,
}

/** 规则状态（五态） */
export enum RuleStatus {
  /** 未开始：已创建但还没到 startDate */
  NOT_STARTED = 1,
  /** 开始：正在执行 */
  RUNNING = 2,
  /** 暂停：用户主动暂停 */
  PAUSED = 3,
  /** 完成：已到 endDate */
  FINISHED = 4,
  /** 失效：主数据停用/归档/子分类阻断，需用户编辑后重新启动 */
  INVALID = 5,
}

/** 执行失败分类（成功时后端返回 null） */
export enum FailCategory {
  /** 主数据类：账户停用 / 分类停用或归档 / 分类子分类阻断 */
  MASTER_DATA = 1,
  /** 其他类：余额异常 / 代码异常 / 其它 BusinessException */
  OTHER = 2,
}

/** 定时规则（响应，对应后端 ScheduledFlowRuleResponseDto）
 *
 * 失效状态（status=INVALID）下，引用的主数据名称字段
 * （accountName / accountToName / typeName / actionName）后端会置空字符串；
 * 前端按空值隐藏对应展示即可，不需要额外的 invalidFields 结构。
 */
export interface ScheduledFlowRule {
  id: number
  name: string
  money: string

  typeId: number
  typeName: string

  actionId: number
  actionName: string

  accountId: number
  accountName: string

  /** 转账目标账户（转账类规则时有值） */
  accountToId?: number
  accountToName?: string

  note?: string

  cycleType: CycleType
  /** 周期内具体日期，JSON 字符串；见 parseCycleDates / stringifyCycleDates */
  cycleDates?: string
  /** 执行时间，响应固定 HH:mm:ss */
  runTime: string

  /** 开始日期 yyyy-MM-dd */
  startDate: string
  /** 结束日期 yyyy-MM-dd；空代表永久 */
  endDate?: string
  /** 是否永久（endDate 为空时系统自动标记） */
  permanent: boolean

  status: RuleStatus

  /** 下次执行日期 */
  nextRunDate?: string
  /** 上次执行日期 */
  lastRunDate?: string

  /** 是否开启站内提醒（规则级） */
  reminderEnabled: boolean
  /** 是否开启邮件提醒（规则级） */
  emailEnabled: boolean

  createTime: string
}

/** 创建/更新规则参数（请求，对应后端 ScheduledFlowRuleRequestDto） */
export interface ScheduledFlowRuleParams {
  name: string
  money: string
  typeId: number
  actionId: number
  accountId: number
  accountToId?: number
  note?: string
  cycleType: CycleType
  /** 周期内具体日期，JSON 字符串；见 stringifyCycleDates */
  cycleDates?: string
  /** HH:mm 或 HH:mm:ss 都可，后端统一归一化为 HH:mm:ss */
  runTime: string
  /** 必须 >= 今天 + 1 */
  startDate: string
  /** 可选，不填 = 永久 */
  endDate?: string
  reminderEnabled: boolean
  emailEnabled: boolean
}

/** 未来执行日预览 */
export interface ScheduledFlowPreview {
  /**
   * MONTHLY：下一个月的执行日；
   * YEARLY：下一年的执行日；
   * DAILY / WEEKLY：返回空数组（前端不展示）
   */
  runDates: string[]
}

/** 执行日志 */
export interface ScheduledFlowLog {
  id: number
  ruleId: number
  /** 规则名称冗余；规则已被删除时后端返回 "[已删除]" */
  ruleName: string
  executeTime: string
  success: boolean
  /** 成功时关联的流水 ID；失败时为 null */
  flowId?: number | null
  /** 失败分类；成功时为 null */
  failCategory: FailCategory | null
  /** 失败原因文本；成功时为 null */
  failReason?: string | null
}

/** 执行日志查询参数（倒序分页） */
export interface ScheduledFlowLogQuery {
  /** 按规则过滤；不传则查全部 */
  ruleId?: number
  /** 页码，从 0 开始；默认 0 */
  page?: number
  /** 每页大小；默认 20 */
  size?: number
}

/** 全局提醒配置（v2.7.0 起接口迁移到 /system/config/scheduledFlow，
 *  调用方请使用 systemConfigApi.getScheduledFlow / updateScheduledFlow） */
export interface ReminderConfig {
  /** 提醒前 N 天，N ∈ [1, 5]，不支持当天提醒 */
  remindBeforeDays: number
  /** 提醒时间 HH:mm 或 HH:mm:ss */
  remindTime: string
}

/* ---------- cycleDates 编解码 ---------- */

/** 把后端返回的 cycleDates JSON 字符串解析为数组
 *
 * - 空串 / null / undefined / 非法 JSON → 返回 []
 * - 泛型由调用方指定：WEEKLY / MONTHLY 用 `number`，YEARLY 用 `string`
 */
export function parseCycleDates<T extends number | string = number | string>(
  cycleDates: string | null | undefined
): T[] {
  if (!cycleDates) return []
  try {
    const parsed = JSON.parse(cycleDates)
    return Array.isArray(parsed) ? (parsed as T[]) : []
  } catch {
    return []
  }
}

/** 把数组编码为 cycleDates JSON 字符串
 *
 * DAILY 固定返回 "[]"（忽略传入的数组）
 */
export function stringifyCycleDates(
  dates: Array<number | string>,
  cycleType: CycleType
): string {
  if (cycleType === CycleType.DAILY) return '[]'
  return JSON.stringify(dates)
}

/* ---------- API ---------- */

/** 定时记账 API */
export const scheduledFlowApi = {
  /* 规则 CRUD */

  /** 获取全部定时规则列表 */
  listRules() {
    return getRequest().get<ApiResponse<ScheduledFlowRule[]>>(
      '/scheduledFlow/rule/list'
    )
  },

  /** 获取规则详情 */
  getRule(id: number) {
    return getRequest().get<ApiResponse<ScheduledFlowRule>>(
      `/scheduledFlow/rule/${id}`
    )
  },

  /** 创建规则 */
  createRule(params: ScheduledFlowRuleParams) {
    return getRequest().post<ApiResponse<ScheduledFlowRule>>(
      '/scheduledFlow/rule',
      params
    )
  },

  /** 更新规则 */
  updateRule(id: number, params: ScheduledFlowRuleParams) {
    return getRequest().put<ApiResponse<ScheduledFlowRule>>(
      `/scheduledFlow/rule/${id}`,
      params
    )
  },

  /** 删除规则（级联删执行日志 + 未读通知） */
  deleteRule(id: number) {
    return getRequest().delete<ApiResponse<void>>(`/scheduledFlow/rule/${id}`)
  },

  /** 启动规则：未开始 / 暂停 / 完成 / 失效 → 开始
   *
   * 产品规则：从"暂停 / 完成 / 失效"恢复到"开始"必须用户编辑过一次
   * 才允许点击；按钮启用态由前端根据 UX 规则拦截（后端不强制）。
   */
  startRule(id: number) {
    return getRequest().post<ApiResponse<ScheduledFlowRule>>(
      `/scheduledFlow/rule/${id}/start`
    )
  },

  /** 暂停规则：开始 → 暂停 */
  pauseRule(id: number) {
    return getRequest().post<ApiResponse<ScheduledFlowRule>>(
      `/scheduledFlow/rule/${id}/pause`
    )
  },

  /* 预览 */

  /** 预览未来一轮执行日
   *
   * - MONTHLY：下一个月的执行日数组
   * - YEARLY：下一年的执行日数组
   * - DAILY / WEEKLY：返回空数组
   */
  previewRule(id: number) {
    return getRequest().get<ApiResponse<ScheduledFlowPreview>>(
      `/scheduledFlow/rule/${id}/preview`
    )
  },

  /* 执行日志 */

  /** 查执行日志（按规则过滤 + 倒序分页） */
  listLogs(query: ScheduledFlowLogQuery = {}) {
    return getRequest().get<ApiResponse<ScheduledFlowLog[]>>(
      '/scheduledFlow/log',
      { params: query }
    )
  },

  /** 删单条日志 */
  deleteLog(id: number) {
    return getRequest().delete<ApiResponse<void>>(`/scheduledFlow/log/${id}`)
  },

  /** 按规则批量清日志 */
  clearLogsByRule(ruleId: number) {
    return getRequest().delete<ApiResponse<void>>('/scheduledFlow/log', {
      params: { ruleId },
    })
  },

  /* 全局提醒配置已迁移到 systemConfigApi（systemConfig.ts），
     新代码请用 systemConfigApi.getScheduledFlow / updateScheduledFlow */
}
