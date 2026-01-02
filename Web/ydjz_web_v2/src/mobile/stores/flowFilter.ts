import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * 明细页面筛选状态 Store
 * 用于在页面跳转后保持筛选条件
 */
export const useFlowFilterStore = defineStore('flowFilter', () => {
  // 当前月份
  const chooseMonth = ref('')

  // 筛选类型 3=全部, 0=流入, 1=流出, 2=转账
  const handleType = ref(3)

  // 排序类型 0=按时间, 1=按金额
  const orderType = ref(0)

  // 是否已初始化
  const initialized = ref(false)

  function save(state: {
    chooseMonth: string
    handleType: number
    orderType: number
  }) {
    chooseMonth.value = state.chooseMonth
    handleType.value = state.handleType
    orderType.value = state.orderType
    initialized.value = true
  }

  function reset() {
    chooseMonth.value = ''
    handleType.value = 3
    orderType.value = 0
    initialized.value = false
  }

  return {
    chooseMonth,
    handleType,
    orderType,
    initialized,
    save,
    reset,
  }
})
