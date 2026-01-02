/**
 * 工具解析助手
 * 提供工具名称映射、显示名称、跳转参数等功能
 * PC 端和移动端共用
 */
import type { UnifiedMessage } from './UnifiedMessage'

// ==================== 工具名称映射 ====================

/** 静态名称工具映射 */
export const toolNameMap: Record<string, string> = {
  accounts: '查询账户',
  types: '查询全部分类',
  current_date: '获取日期',
  year_statistics: '年度统计',
  get_flow: '查询流水详情'
}

/** 带 title 的工具前缀映射 */
export const toolPrefixMap: Record<string, string> = {
  flows: '查询',
  add_flow: '新增',
  update_flow: '更新',
  make_excel: 'Excel'
}

// ==================== 工具分类 ====================

/** 不可点击的工具列表（不显示箭头、不弹出详情） */
export const nonClickableTools = [
  'accounts',
  'types',
  'current_date',
  'year_statistics',
  'make_excel'
]

/** 可跳转的工具列表（点击后跳转到其他页面） */
export const navigableTools = ['flows', 'get_flow', 'add_flow', 'update_flow']

// ==================== 工具数据解析 ====================

/**
 * 解析工具参数（可能是对象或 JSON 字符串）
 */
export function parseToolData(data: unknown): Record<string, unknown> {
  if (!data) return {}
  if (typeof data === 'string') {
    try {
      return JSON.parse(data)
    } catch {
      return {}
    }
  }
  return data as Record<string, unknown>
}

// ==================== 工具显示 ====================

/**
 * 获取工具显示名称
 * - 带 title 的工具：显示为 "前缀:title"（如 "新增:午餐"）
 * - 静态名称工具：显示映射名称
 * - 其他：显示原始工具名
 */
export function getToolDisplayName(msg: UnifiedMessage): string {
  const toolName = msg.tool?.name || ''

  // 带 title 的工具：显示为 "前缀:title"
  if (toolPrefixMap[toolName]) {
    const args = parseToolData(msg.tool?.arguments)
    if (args.title) {
      return `${toolPrefixMap[toolName]}:${args.title}`
    }
    return toolPrefixMap[toolName]
  }

  return toolNameMap[toolName] || toolName
}

/**
 * 获取工具额外显示信息
 * - current_date：显示日期
 * - year_statistics：显示年份
 */
export function getToolExtraInfo(msg: UnifiedMessage): string {
  const toolName = msg.tool?.name || ''

  if (toolName === 'current_date' && msg.tool?.result) {
    const result = parseToolData(msg.tool.result)
    if (result.today) {
      return String(result.today)
    }
  }

  if (toolName === 'year_statistics' && msg.tool?.arguments) {
    const args = parseToolData(msg.tool.arguments)
    if (args.year) {
      return `${args.year}年`
    }
  }

  return ''
}

// ==================== 工具交互判断 ====================

/**
 * 判断工具是否可点击（显示箭头）
 */
export function isToolClickable(toolName: string): boolean {
  // 可跳转的工具也是可点击的
  return !nonClickableTools.includes(toolName) || navigableTools.includes(toolName)
}

/**
 * 判断工具是否可跳转到其他页面
 */
export function isToolNavigable(toolName: string): boolean {
  return navigableTools.includes(toolName)
}

// ==================== 工具跳转参数 ====================

/** flows 工具的跳转参数 */
export interface FlowsNavigationParams {
  startDate?: string
  endDate?: string
  singleMonth?: boolean
  chooseHandle?: number
  actions?: number[]
  types?: number[]
  collect?: boolean | string
  accountId?: number
  note?: string
}

/** flow 详情跳转参数 */
export interface FlowNavigationParams {
  flowId: number
}

/** 工具跳转结果 */
export interface ToolNavigationResult {
  type: 'flows' | 'flow' | 'unknown'
  params?: FlowsNavigationParams
  flowParams?: FlowNavigationParams
  route?: string
}

/**
 * 获取工具跳转参数
 * 返回跳转类型和参数，由组件处理实际跳转
 */
export function getToolNavigationParams(msg: UnifiedMessage): ToolNavigationResult | null {
  const toolName = msg.tool?.name || ''

  if (!isToolNavigable(toolName)) {
    return null
  }

  if (toolName === 'flows') {
    const result = parseToolData(msg.tool?.result)
    const queryParams = result.queryParams as Record<string, unknown> | undefined

    if (queryParams) {
      return {
        type: 'flows',
        params: {
          startDate: queryParams.startDate as string,
          endDate: queryParams.endDate as string,
          singleMonth: queryParams.singleMonth as boolean,
          chooseHandle: queryParams.chooseHandle as number,
          actions: queryParams.actions as number[],
          types: queryParams.types as number[],
          collect: queryParams.collect as boolean | string,
          accountId: queryParams.accountId as number,
          note: queryParams.note as string
        },
        // PC 端路由
        route: '/flow?tab=screen'
      }
    }
  }

  // get_flow / add_flow / update_flow 都返回 flow id
  if (toolName === 'get_flow' || toolName === 'add_flow' || toolName === 'update_flow') {
    const result = parseToolData(msg.tool?.result)
    // add_flow/update_flow 返回 flowId，get_flow 返回 id
    const flowId = (result.flowId ?? result.id) as number | undefined

    if (flowId) {
      return {
        type: 'flow',
        flowParams: { flowId }
      }
    }
  }

  return { type: 'unknown' }
}

// ==================== 格式化工具 ====================

/**
 * 格式化 JSON 数据为字符串
 */
export function formatToolJson(data: unknown): string {
  if (!data) return '暂无数据'
  try {
    if (typeof data === 'string') {
      const parsed = JSON.parse(data)
      return JSON.stringify(parsed, null, 2)
    }
    return JSON.stringify(data, null, 2)
  } catch {
    return String(data)
  }
}
