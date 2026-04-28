/**
 * 本地存储工具（localStorage 封装）
 *
 * 双端通用：桌面端 / 移动端均可 import 使用
 *
 * 用法：
 *   import { storage } from '@shared/utils/storage'
 *
 *   storage.setJSON('flowList.cardOrder', ['month', 'stats', 'trend'])
 *   const order = storage.getJSON<string[]>('flowList.cardOrder', [])
 *
 *   storage.setString('token', 'xxxxxx')
 *   const token = storage.getString('token')
 *
 *   storage.remove('token')
 */

interface StorageApi {
  /** 读取 JSON 值，解析失败或 key 不存在时返回 defaultValue */
  getJSON<T>(key: string, defaultValue: T): T
  /** 写入 JSON 值（自动 stringify） */
  setJSON<T>(key: string, value: T): void
  /** 读取字符串值，未设置时返回 null */
  getString(key: string): string | null
  /** 读取字符串值，未设置时返回 defaultValue */
  getString(key: string, defaultValue: string): string
  /** 写入字符串值（不做 JSON 序列化） */
  setString(key: string, value: string): void
  /** 删除某个 key */
  remove(key: string): void
}

export const storage: StorageApi = {
  getJSON<T>(key: string, defaultValue: T): T {
    try {
      const raw = localStorage.getItem(key)
      if (raw === null) return defaultValue
      return JSON.parse(raw) as T
    } catch (err) {
      console.warn(`[storage] getJSON("${key}") failed, fallback to default:`, err)
      return defaultValue
    }
  },

  setJSON<T>(key: string, value: T): void {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch (err) {
      console.error(`[storage] setJSON("${key}") failed:`, err)
    }
  },

  getString(key: string, defaultValue?: string): any {
    const v = localStorage.getItem(key)
    if (v === null) return defaultValue ?? null
    return v
  },

  setString(key: string, value: string): void {
    try {
      localStorage.setItem(key, value)
    } catch (err) {
      console.error(`[storage] setString("${key}") failed:`, err)
    }
  },

  remove(key: string): void {
    localStorage.removeItem(key)
  },
}
