import { getRequest } from './request'
import type { ApiResponse } from '../types'

/** 备份 API */
export const backupApi = {
  /**
   * 手动备份
   * 生成备份文件 → 发送 WebHook（邮件）→ 返回文件名
   */
  backup() {
    return getRequest().post<ApiResponse<string>>('/backup/backup')
  },

  /**
   * 上传恢复
   * 上传 SQL 备份文件进行数据恢复
   * @param file SQL 备份文件（.sql 格式）
   */
  restore(file: File) {
    const formData = new FormData()
    formData.append('file', file)

    return getRequest().post<ApiResponse<null>>('/backup/restore', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 120000, // 恢复操作可能需要较长时间，设置 2 分钟超时
    })
  },
}
