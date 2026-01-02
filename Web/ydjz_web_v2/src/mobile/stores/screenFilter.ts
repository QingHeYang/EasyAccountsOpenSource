import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * 筛选页面状态 Store
 * 用于在跳转到 FlowAdd 后返回时保持筛选条件
 */
export const useScreenFilterStore = defineStore('screenFilter', () => {
  // 搜索
  const searchNote = ref('')

  // 时间筛选
  const fastChoose = ref(0) // 0当月 1上月 2全年 3上年 -1自定义
  const startDate = ref('')
  const endDate = ref('')
  const singleMonth = ref(true)

  // 账户
  const accountId = ref(-1)
  const accountName = ref('全部账户')

  // 资金流向
  const handleType = ref(3) // 0收入 1支出 2转账 3全部

  // 收藏
  const collectOnly = ref(false)

  // 收支类型（多选）
  const chooseActions = ref<number[]>([])

  // 分类（多选）
  const chooseTypes = ref<number[]>([])

  // 滚动定位：最后点击的 flow ID
  const lastClickedFlowId = ref<number | null>(null)

  // 是否已初始化
  const initialized = ref(false)

  function save(state: {
    searchNote: string
    fastChoose: number
    startDate: string
    endDate: string
    singleMonth: boolean
    accountId: number
    accountName: string
    handleType: number
    collectOnly: boolean
    chooseActions: number[]
    chooseTypes: number[]
    lastClickedFlowId: number | null
  }) {
    searchNote.value = state.searchNote
    fastChoose.value = state.fastChoose
    startDate.value = state.startDate
    endDate.value = state.endDate
    singleMonth.value = state.singleMonth
    accountId.value = state.accountId
    accountName.value = state.accountName
    handleType.value = state.handleType
    collectOnly.value = state.collectOnly
    chooseActions.value = [...state.chooseActions]
    chooseTypes.value = [...state.chooseTypes]
    lastClickedFlowId.value = state.lastClickedFlowId
    initialized.value = true
  }

  function reset() {
    searchNote.value = ''
    fastChoose.value = 0
    startDate.value = ''
    endDate.value = ''
    singleMonth.value = true
    accountId.value = -1
    accountName.value = '全部账户'
    handleType.value = 3
    collectOnly.value = false
    chooseActions.value = []
    chooseTypes.value = []
    lastClickedFlowId.value = null
    initialized.value = false
  }

  return {
    searchNote,
    fastChoose,
    startDate,
    endDate,
    singleMonth,
    accountId,
    accountName,
    handleType,
    collectOnly,
    chooseActions,
    chooseTypes,
    lastClickedFlowId,
    initialized,
    save,
    reset,
  }
})
