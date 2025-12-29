import { getRequest } from './request'
import type { ApiResponse } from '../types'
import type { Action } from './action'

/** 分类基础信息 */
export interface Type {
  id: number
  /** 分类名称 */
  tname: string
  /** 关联的收支类型 */
  action?: Action
  /** 收支类型ID */
  actionId: number
  /** 父级分类ID，0表示一级分类 */
  parent: number
  /** 是否有子分类 */
  hasChild: boolean
  /** 是否归档 */
  archive: boolean
  /** 是否停用 */
  disable: boolean
  /** 是否在分析中禁用 */
  analysisDisable: boolean
}

/** 分类列表响应（包含子分类） */
export interface TypeWithChildren extends Type {
  /** 子分类列表 */
  childrenTypes?: TypeWithChildren[]
}

/** 添加/更新分类参数 */
export interface TypeParams {
  tname: string
  actionId: number
  /** 父级分类ID，0表示一级分类 */
  parent?: number
  analysisDisable?: boolean
  archive?: boolean
  disable?: boolean
}

/** 分类管理 API */
export const typeApi = {
  /** 获取所有分类 */
  getAll() {
    return getRequest().get<ApiResponse<TypeWithChildren[]>>('/type/getType')
  },

  /** 获取所有分类（无归档、停用限制） */
  getAllNoLimit() {
    return getRequest().get<ApiResponse<TypeWithChildren[]>>('/type/getType/noLimit')
  },

  /** 获取归档分类 */
  getArchived() {
    return getRequest().get<ApiResponse<TypeWithChildren[]>>('/type/getTypeArchive')
  },

  /** 获取指定收支的分类 */
  getByActionId(actionId: number) {
    return getRequest().get<ApiResponse<TypeWithChildren[]>>(`/type/getTypeByActionId/${actionId}`)
  },

  /** 获取二级指定分类 */
  getByParent(parentId: number) {
    return getRequest().get<ApiResponse<Type[]>>(`/type/getType/${parentId}`)
  },

  /** 获取单个分类 */
  getById(id: number) {
    return getRequest().get<ApiResponse<Type>>(`/type/getTypeSingle/${id}`)
  },

  /** 添加分类 */
  add(params: TypeParams) {
    return getRequest().post<ApiResponse<void>>('/type/addType', params)
  },

  /** 更新分类 */
  update(id: number, params: TypeParams) {
    return getRequest().put<ApiResponse<void>>(`/type/updateType/${id}`, params)
  },

  /** 归档/取消归档分类 */
  archive(id: number, archive: boolean) {
    return getRequest().put<ApiResponse<void>>(`/type/archiveType/${id}`, null, {
      params: { archive },
    })
  },

  /** 停用分类 */
  delete(id: number) {
    return getRequest().delete<ApiResponse<void>>(`/type/deleteType/${id}`)
  },
}
