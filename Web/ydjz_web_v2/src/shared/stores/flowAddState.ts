/**
 * FlowAdd 页面状态保存
 * 用于跳转到模板管理等页面后返回时恢复输入内容
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Action } from '@shared/api/action'
import type { Account } from '@shared/api/account'

export interface FlowAddState {
  money: string
  note: string
  isCollect: boolean
  chooseDate: string
  selectedAction: Action | null
  selectedAccount: Account | null
  selectedAccountTo: Account | null
  selectedType: { id: number; tname: string } | null
  // 图片列表（只保存已上传成功的）
  uploadedImages: Array<{
    url: string
    serverFileName: string
  }>
}

export const useFlowAddStateStore = defineStore('flowAddState', () => {
  // 状态
  const money = ref('')
  const note = ref('')
  const isCollect = ref(false)
  const chooseDate = ref('')
  const selectedAction = ref<Action | null>(null)
  const selectedAccount = ref<Account | null>(null)
  const selectedAccountTo = ref<Account | null>(null)
  const selectedType = ref<{ id: number; tname: string } | null>(null)
  const uploadedImages = ref<Array<{ url: string; serverFileName: string }>>([])

  // 初始化标记
  const initialized = ref(false)

  // 保存状态
  function save(state: FlowAddState) {
    money.value = state.money
    note.value = state.note
    isCollect.value = state.isCollect
    chooseDate.value = state.chooseDate
    selectedAction.value = state.selectedAction
    selectedAccount.value = state.selectedAccount
    selectedAccountTo.value = state.selectedAccountTo
    selectedType.value = state.selectedType
    uploadedImages.value = state.uploadedImages
    initialized.value = true
  }

  // 重置状态
  function reset() {
    money.value = ''
    note.value = ''
    isCollect.value = false
    chooseDate.value = ''
    selectedAction.value = null
    selectedAccount.value = null
    selectedAccountTo.value = null
    selectedType.value = null
    uploadedImages.value = []
    initialized.value = false
  }

  return {
    money,
    note,
    isCollect,
    chooseDate,
    selectedAction,
    selectedAccount,
    selectedAccountTo,
    selectedType,
    uploadedImages,
    initialized,
    save,
    reset,
  }
})
