import { getRequest } from './request'
import type { ApiResponse } from '../types'

/** 模板标签 */
export interface Tag {
  id: number
  name: string
  color: string
}

/** 添加/更新标签参数 */
export interface TagParams {
  id?: number
  name: string
  color: string
}

/** 标签管理 API */
export const tagApi = {
  /** 获取全部标签 */
  getAll() {
    return getRequest().get<ApiResponse<Tag[]>>('/tag/getTags')
  },

  /** 获取指定标签 */
  getById(id: number) {
    return getRequest().get<ApiResponse<Tag>>(`/tag/getTag/${id}`)
  },

  /** 添加标签 */
  add(params: TagParams) {
    return getRequest().post<ApiResponse<void>>('/tag/addTag', params)
  },

  /** 更新标签 */
  update(params: TagParams) {
    return getRequest().put<ApiResponse<void>>('/tag/updateTag', params)
  },

  /** 停用标签 */
  delete(id: number) {
    return getRequest().delete<ApiResponse<void>>(`/tag/deleteTag/${id}`)
  },
}
