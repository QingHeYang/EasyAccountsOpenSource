import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Flow } from '@shared/api/flow'
import type { AnalysisTypeMonthResult } from '@shared/api/analysis'

/**
 * 分类统计页面状态 Store
 * 用于在跳转到 FlowAdd 后返回时保持状态
 */
export const useAnalysisTypeFilterStore = defineStore('analysisTypeFilter', () => {
  // 分类选择
  const selectedTypeId = ref<number | null>(null)
  const selectedTypeName = ref('')

  // 时间筛选
  const fastChoose = ref('1')
  const startDate = ref('')
  const endDate = ref('')

  // 流水弹窗状态
  const showFlowPopup = ref(false)
  const flowMonth = ref('')
  const flowChooseHandle = ref(0) // 0收入 1支出
  const flowList = ref<Flow[]>([])

  // 查询结果
  const result = ref<AnalysisTypeMonthResult | null>(null)

  // 是否已初始化
  const initialized = ref(false)

  function save(state: {
    selectedTypeId: number | null
    selectedTypeName: string
    fastChoose: string
    startDate: string
    endDate: string
    showFlowPopup: boolean
    flowMonth: string
    flowChooseHandle: number
    flowList: Flow[]
    result: AnalysisTypeMonthResult | null
  }) {
    selectedTypeId.value = state.selectedTypeId
    selectedTypeName.value = state.selectedTypeName
    fastChoose.value = state.fastChoose
    startDate.value = state.startDate
    endDate.value = state.endDate
    showFlowPopup.value = state.showFlowPopup
    flowMonth.value = state.flowMonth
    flowChooseHandle.value = state.flowChooseHandle
    flowList.value = state.flowList
    result.value = state.result
    initialized.value = true
  }

  function reset() {
    selectedTypeId.value = null
    selectedTypeName.value = ''
    fastChoose.value = '1'
    startDate.value = ''
    endDate.value = ''
    showFlowPopup.value = false
    flowMonth.value = ''
    flowChooseHandle.value = 0
    flowList.value = []
    result.value = null
    initialized.value = false
  }

  return {
    selectedTypeId,
    selectedTypeName,
    fastChoose,
    startDate,
    endDate,
    showFlowPopup,
    flowMonth,
    flowChooseHandle,
    flowList,
    result,
    initialized,
    save,
    reset,
  }
})
