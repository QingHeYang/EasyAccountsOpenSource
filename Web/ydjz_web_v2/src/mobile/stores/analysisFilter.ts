import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * 分析页面筛选状态 Store
 * 用于在页面跳转后保持筛选条件
 */
export const useAnalysisFilterStore = defineStore('analysisFilter', () => {
  // 时间筛选
  const fastChoose = ref(0) // 0当月 1上月 2近3月 3近6月 4近1年 5当年 6上年 7自定义
  const startDate = ref('')
  const endDate = ref('')

  // Tab 状态
  const tabIndex = ref(0) // 0收入 1支出

  // 筛选选项
  const combineSubType = ref(false)
  const showDisableAnalysisType = ref(true)

  // 是否已初始化（避免首次进入时覆盖默认值）
  const initialized = ref(false)

  function save(state: {
    fastChoose: number
    startDate: string
    endDate: string
    tabIndex: number
    combineSubType: boolean
    showDisableAnalysisType: boolean
  }) {
    fastChoose.value = state.fastChoose
    startDate.value = state.startDate
    endDate.value = state.endDate
    tabIndex.value = state.tabIndex
    combineSubType.value = state.combineSubType
    showDisableAnalysisType.value = state.showDisableAnalysisType
    initialized.value = true
  }

  function reset() {
    fastChoose.value = 0
    startDate.value = ''
    endDate.value = ''
    tabIndex.value = 0
    combineSubType.value = false
    showDisableAnalysisType.value = true
    initialized.value = false
  }

  return {
    fastChoose,
    startDate,
    endDate,
    tabIndex,
    combineSubType,
    showDisableAnalysisType,
    initialized,
    save,
    reset,
  }
})
