import { getRequest } from './request'
import type { ApiResponse } from '../types'
import type { Action } from './action'
import type { Account } from './account'
import type { Type } from './type'
import type { Tag } from './tag'

/** 快记模板响应 */
export interface Template {
  id: number
  name: string
  money?: string
  actionId?: number
  action?: Action
  accountId?: number
  account?: Account
  accountToId?: number
  accountTo?: Account
  typeId?: number
  type?: Type
  tagId?: number
  tag?: Tag
  /** 日期类型：0-记本月 1-补上月 */
  dateType?: number
}

/** 添加/更新模板参数 */
export interface TemplateParams {
  id?: number
  name: string
  money?: string
  actionId?: number
  accountId?: number
  accountToId?: number
  typeId?: number
  tagId?: number
  dateType?: number
}

/** 快记模板 API */
export const templateApi = {
  /** 获取全部模板 */
  getAll() {
    return getRequest().get<ApiResponse<Template[]>>('/template/getAllTemplates')
  },

  /** 根据标签获取模板 */
  getByTagId(tagId: number) {
    return getRequest().get<ApiResponse<Template[]>>(`/template/getAllTemplatesByTag/${tagId}`)
  },

  /** 获取单个模板 */
  getById(id: number) {
    return getRequest().get<ApiResponse<Template>>(`/template/getTemplateById/${id}`)
  },

  /** 添加模板 */
  add(params: TemplateParams) {
    return getRequest().post<ApiResponse<void>>('/template/addTemplate', params)
  },

  /** 更新模板 */
  update(params: TemplateParams) {
    return getRequest().put<ApiResponse<void>>('/template/updateTemplate', params)
  },

  /** 删除模板 */
  delete(id: number) {
    return getRequest().delete<ApiResponse<void>>(`/template/deleteTemplate/${id}`)
  },
}
