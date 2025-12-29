import { getRequest } from './request'
import type { ApiResponse } from '../types'

/** 分类统计项 */
export interface AnalysisTypeItem {
  id: number
  /** 父分类ID，-1表示一级分类，0表示合并小项 */
  parentId: number
  name: string
  money: string
  /** 百分比，如 43.84 */
  percent: number
}

/** 分类统计列表响应 */
export interface AnalysisTypeListResult {
  totalIn: string
  totalOut: string
  /** 收入分类（图表用，合并后） */
  showInTypeList: AnalysisTypeItem[]
  /** 支出分类（图表用，合并后） */
  showOutTypeList: AnalysisTypeItem[]
  /** 全部收入分类（列表用） */
  allInTypeList: AnalysisTypeItem[]
  /** 全部支出分类（列表用） */
  allOutTypeList: AnalysisTypeItem[]
}

/** 分类统计请求参数 */
export interface AnalysisTypeListParams {
  /** 开始年月 yyyy-MM */
  start: string
  /** 结束年月 yyyy-MM */
  end: string
  /** 是否合并子分类 */
  combineSubType?: boolean
  /** 是否显示全部分类（含禁用的） */
  showDisableAnalysisType?: boolean
}

/** 月度数据 */
export interface MonthData {
  month: number
  income: string
  outcome: string
}

/** 年度数据 */
export interface YearData {
  year: number
  income: string
  outcome: string
  monthData: MonthData[]
}

/** 单项分类统计响应 */
export interface AnalysisTypeMonthResult {
  typeId: number
  /** 分类名称，如 "老公收入/私活" */
  typeName: string
  totalIncome: string
  totalOutcome: string
  yearData: YearData[]
}

/** 单项分类统计请求参数 */
export interface AnalysisTypeMonthParams {
  typeId: number
  /** 开始年月 yyyy-MM */
  start: string
  /** 结束年月 yyyy-MM */
  end: string
}

/** 统计分析 API */
export const analysisApi = {
  /** 获取分类统计列表 */
  getTypeList(params: AnalysisTypeListParams) {
    return getRequest().post<ApiResponse<AnalysisTypeListResult>>(
      '/analysis/v2/getAnalysisTypeList',
      params
    )
  },

  /** 获取单项分类月度统计 */
  getTypeMonthData(params: AnalysisTypeMonthParams) {
    return getRequest().post<ApiResponse<AnalysisTypeMonthResult>>(
      '/analysis/v2/getAnalysisTypeMonthData',
      params
    )
  },
}
