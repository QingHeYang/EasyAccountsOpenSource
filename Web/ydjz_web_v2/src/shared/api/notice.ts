import { getRequest } from './request'
import type { ApiResponse } from '../types'

/** 通知类型
 *
 * 目前只有 SCHEDULED_REMINDER；未来扩展（回收站、AI 错误等）再追加 2、3…
 * 前端按 type 分 icon / 跳转。
 */
export enum NoticeType {
  /** 定时记账事前提醒（执行前 N 天触发） */
  SCHEDULED_REMINDER = 1,
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
  /** 关联的定时规则 ID（type=SCHEDULED_REMINDER 时有值） */
  relatedRuleId?: number
  /** 关联的执行日期 */
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
