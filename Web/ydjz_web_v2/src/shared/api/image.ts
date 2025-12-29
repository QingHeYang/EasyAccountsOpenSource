import { getRequest } from './request'
import type { ApiResponse } from '../types'

/** 上传图片响应 */
export interface UploadImageResult {
  fileName: string
}

/** 图片管理 API */
export const imageApi = {
  /** 上传图片 */
  upload(file: File) {
    const formData = new FormData()
    formData.append('file', file)

    return getRequest().post<ApiResponse<UploadImageResult>>('/image/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 30000, // 图片上传超时 30s
    })
  },

  /** 获取图片URL */
  getUrl(fileName: string) {
    const baseURL = getRequest().defaults.baseURL || ''
    return `${baseURL}/image/${fileName}`
  },
}
