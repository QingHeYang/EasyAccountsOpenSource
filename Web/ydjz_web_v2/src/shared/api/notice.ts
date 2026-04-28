import { getRequest } from './request'
import type { ApiResponse } from '../types'

/** 通知类型
 *
 * 前端按 type 分 icon / 颜色 / 跳转。
 *
 * - 1：定时记账事前提醒 → 跳转规则编辑（relatedRuleId）
 * - 2：自动月度 Excel 提前提醒 → 跳转设置「自动 Excel」
 * - 3：自动月度 Excel 已生成 → 跳转明细页 / 下载入口
 * - 4：当月无流水，已跳过自动 Excel 生成 → 仅展示，不跳转
 * - 5：自动 Excel 生成失败 → 跳转设置「自动 Excel」（让用户检查配置）
 */
export enum NoticeType {
  /** 定时记账事前提醒（执行前 N 天触发） */
  SCHEDULED_REMINDER = 1,
  /** 自动月度 Excel 提前提醒（执行前 N 天触发） */
  AUTO_EXCEL_REMIND = 2,
  /** 自动月度 Excel 已生成 */
  AUTO_EXCEL_GENERATED = 3,
  /** 当月无流水，自动 Excel 已跳过本次生成 */
  AUTO_EXCEL_SKIPPED = 4,
  /** 自动 Excel 生成失败 */
  AUTO_EXCEL_FAILED = 5,
}

/** 用户通知（对应后端 UserNoticeResponseDto）
 *
 * 注意：跟 home.ts 的 `Notice`（系统公告）不是一回事，
 * 本类型是面向用户的通知中心条目。
 */
export interface UserNotice {
  id: number
  /** 通知类型，见 NoticeType */
  type: NoticeType
  title: string
  content: string
  /** 关联的定时规则 ID（type=SCHEDULED_REMINDER 时有值；自动 Excel 类通知不携带） */
  relatedRuleId?: number
  /** 关联日期：定时记账=执行日；自动 Excel=目标月或生成日 */
  relatedRunDate?: string
  /** 是否已读 */
  read: boolean
  /** 创建时间 */
  createTime: string
}

/** 通知列表查询参数 */
export interface NoticeListQuery {
  /** 按已读状态过滤；不传返回全部 */
  isRead?: boolean
}

/** 通知 API */
export const noticeApi = {
  /** 获取通知列表 */
  list(query: NoticeListQuery = {}) {
    return getRequest().get<ApiResponse<UserNotice[]>>('/notice/list', {
      params: query,
    })
  },

  /** 单条标记已读 */
  markRead(id: number) {
    return getRequest().put<ApiResponse<void>>(`/notice/${id}/read`)
  },

  /** 全部标记已读 */
  markAllRead() {
    return getRequest().put<ApiResponse<void>>('/notice/markAllRead')
  },

  /** 删除单条通知 */
  delete(id: number) {
    return getRequest().delete<ApiResponse<void>>(`/notice/${id}`)
  },
}
