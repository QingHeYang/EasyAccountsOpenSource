import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { RouteLocationNormalized } from 'vue-router'

/**
 * 路由历史管理 Store
 *
 * 解决问题：
 * 1. 登录后返回会回到登录页
 * 2. 从 A 页面进入 B 页面，返回时应该回到 A 而非固定页面
 *
 * 原理：
 * - 维护一个自定义的路由历史栈，排除登录页
 * - 提供 smartBack 方法，优先从历史栈返回
 * - 登录页跳转和登录成功都使用 replace，不污染历史
 */
export const useRouteHistoryStore = defineStore('routeHistory', () => {
  // 路由历史栈（排除登录页）
  const history = ref<string[]>([])

  // 需要排除的路由（不记录到历史）
  const excludedRoutes = ['/auth', '/login']

  // 最大历史记录数
  const maxHistory = 50

  /**
   * 记录路由（在路由守卫 afterEach 中调用）
   */
  function push(route: RouteLocationNormalized) {
    const path = route.fullPath

    // 排除登录页
    if (excludedRoutes.some(r => path.startsWith(r))) {
      return
    }

    // 避免重复记录同一页面
    if (history.value.length > 0 && history.value[history.value.length - 1] === path) {
      return
    }

    history.value.push(path)

    // 限制历史栈大小
    if (history.value.length > maxHistory) {
      history.value.shift()
    }
  }

  /**
   * 弹出最后一条记录（返回时调用）
   */
  function pop(): string | undefined {
    return history.value.pop()
  }

  /**
   * 获取上一页路径
   * @param fallback 如果没有历史记录，返回的默认路径
   */
  function getPrevious(fallback: string = '/board'): string {
    // 先弹出当前页
    pop()
    // 再获取上一页
    const prev = history.value[history.value.length - 1]
    return prev || fallback
  }

  /**
   * 清空历史（登录成功后可调用）
   */
  function clear() {
    history.value = []
  }

  /**
   * 移除指定路径的所有记录
   */
  function remove(path: string) {
    history.value = history.value.filter(p => p !== path)
  }

  /**
   * 获取历史栈长度
   */
  function size(): number {
    return history.value.length
  }

  return {
    history,
    push,
    pop,
    getPrevious,
    clear,
    remove,
    size,
  }
})
