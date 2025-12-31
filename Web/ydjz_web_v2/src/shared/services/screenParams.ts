/**
 * 筛选参数共享服务
 * 用于 AI 工具跳转到筛选页面时传递参数
 */
import { reactive } from 'vue'

// 筛选参数接口（与 AI 工具返回的 queryParams 对应）
export interface ScreenParams {
  startDate?: string
  endDate?: string
  singleMonth?: boolean
  chooseHandle?: number  // 0收入 1支出 2转账 3全部
  actions?: number[]
  types?: number[]
  collect?: boolean | string
  accountId?: number
  note?: string
}

// 服务状态
interface ScreenParamsState {
  params: ScreenParams | null
  source: 'ai' | 'manual' | null  // 参数来源
}

const state = reactive<ScreenParamsState>({
  params: null,
  source: null
})

/**
 * 设置筛选参数
 */
export function setScreenParams(params: ScreenParams, source: 'ai' | 'manual' = 'ai'): void {
  state.params = { ...params }
  state.source = source
}

/**
 * 获取筛选参数
 */
export function getScreenParams(): ScreenParams | null {
  return state.params
}

/**
 * 获取参数来源
 */
export function getScreenParamsSource(): 'ai' | 'manual' | null {
  return state.source
}

/**
 * 清除筛选参数
 */
export function clearScreenParams(): void {
  state.params = null
  state.source = null
}

/**
 * 检查是否有待应用的参数
 */
export function hasScreenParams(): boolean {
  return state.params !== null
}

/**
 * 消费筛选参数（获取后自动清除）
 */
export function consumeScreenParams(): ScreenParams | null {
  const params = state.params
  clearScreenParams()
  return params
}

// 导出 composable
export function useScreenParams() {
  return {
    setParams: setScreenParams,
    getParams: getScreenParams,
    getSource: getScreenParamsSource,
    clearParams: clearScreenParams,
    hasParams: hasScreenParams,
    consumeParams: consumeScreenParams
  }
}
