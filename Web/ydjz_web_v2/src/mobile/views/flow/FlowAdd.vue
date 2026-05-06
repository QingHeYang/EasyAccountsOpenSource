<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  showToast,
  showConfirmDialog,
  showLoadingToast,
  closeToast,
  showImagePreview,
} from 'vant'
import { flowApi, type FlowParams } from '@shared/api/flow'
import { actionApi, type Action, ActionHandle, ExemptMode } from '@shared/api/action'
import { accountApi, AccountType, type Account } from '@shared/api/account'
import TypePicker from '@mobile/components/flow/TypePicker.vue'
import { templateApi, type Template } from '@shared/api/template'
import { tagApi, type Tag } from '@shared/api/tag'
import { imageApi } from '@shared/api/image'
import { compressImage } from '@shared/utils/image-compress'
import { useSmartBack } from '@shared/composables/useSmartBack'
import { useFlowAddStateStore } from '@shared/stores/flowAddState'

const route = useRoute()
const router = useRouter()
const { smartBack } = useSmartBack()
const flowAddStateStore = useFlowAddStateStore()

// ==================== 模式判断 ====================
const flowId = computed(() => {
  const id = route.params.id as string
  return id ? parseInt(id) : null
})
const isEdit = computed(() => flowId.value !== null)

// ==================== 表单数据 ====================
const money = ref('')
const note = ref('')
const isCollect = ref(false)
const chooseDate = ref('')

// 选择的对象
const selectedAction = ref<Action | null>(null)
const selectedAccount = ref<Account | null>(null)
const selectedAccountTo = ref<Account | null>(null)
const selectedType = ref<{ id: number; tname: string } | null>(null)

// 图片上传
interface FileItem {
  url: string
  status: 'uploading' | 'done' | 'failed'
  message?: string
  serverFileName?: string
  file?: File
}
const fileList = ref<FileItem[]>([])

// 追加分账单（编辑模式）
interface ChildMoney {
  index: number
  money: string
  note: string
}
const childMoneyList = ref<ChildMoney[]>([])

// 来源标记（编辑时保留）
const fromSource = ref<string | null>(null)

// 流水不存在（已删除）
const flowNotFound = ref(false)

// ==================== 列表数据 ====================
const actions = ref<Action[]>([])
const accounts = ref<Account[]>([])
const tags = ref<Tag[]>([])
const templates = ref<Template[]>([])

// ==================== 弹窗状态 ====================
const showAccountSheet = ref(false)
const accountSheetType = ref<1 | 2>(1)
const showTypePicker = ref(false)
const showCalendar = ref(false)
const showTemplatePopup = ref(false)
const showTemplateDetail = ref(false)

// 模板相关
const selectedTag = ref<Tag | null>(null)
const selectedTemplate = ref<Template | null>(null)

// 请求锁
const requestLocks = ref({
  action: false,
  account: false,
})

// ==================== 配置 ====================
const minDate = new Date(2021, 0, 1)
const maxDate = new Date()

// ==================== 计算属性 ====================
const isTransfer = computed(() => selectedAction.value?.handle === 2)

// 普通 / 不计入分组（chip 区主显示 normal，exempt 折叠）
// chip 显示顺序：支出(1) → 收入(0) → 转账(2)
const HANDLE_ORDER: Record<number, number> = { 1: 0, 0: 1, 2: 2 }
const normalActions = computed(() => {
  const list = actions.value.filter((a) => !a.exempt)
  return [...list].sort(
    (a, b) => (HANDLE_ORDER[a.handle] ?? 99) - (HANDLE_ORDER[b.handle] ?? 99)
  )
})
const exemptActions = computed(() => actions.value.filter((a) => a.exempt))
const exemptActionsExpanded = ref(false)

// 当前选中收支类型的颜色（用于卡片渐变背景）
const actionColor = computed(() => {
  if (!selectedAction.value) return 'var(--color-transfer)'
  switch (selectedAction.value.handle) {
    case 0:
      return 'var(--color-income)'
    case 1:
      return 'var(--color-expense)'
    case 2:
      return 'var(--color-transfer)'
    default:
      return 'var(--color-transfer)'
  }
})

// ==================== 双向限制逻辑 ====================

/**
 * 判断账户是否应该被禁用（根据已选收支类型）
 * 负债账户不能用于"不计入"类型的收支
 */
function isAccountDisabled(account: Account, panelType: 1 | 2): boolean {
  // 如果账户不是负债，不禁用
  if (account.accountType !== AccountType.LIABILITY) return false

  // 如果没选收支，或者收支不是"不计入"类型，不禁用
  if (!selectedAction.value?.exempt) return false

  // 普通不计入收支（非转账）：禁用所有负债账户
  if (selectedAction.value.handle !== ActionHandle.TRANSFER) {
    return true
  }

  // 内部转账的不计入，根据 exemptMode 判断
  const mode = selectedAction.value.exemptMode ?? ExemptMode.NONE

  if (panelType === 1) {
    // 源账户面板：禁用负债如果是转出不计入或两边不计入
    return mode === ExemptMode.FROM_EXEMPT || mode === ExemptMode.BOTH_EXEMPT
  } else {
    // 目标账户面板：禁用负债如果是转入不计入或两边不计入
    return mode === ExemptMode.TO_EXEMPT || mode === ExemptMode.BOTH_EXEMPT
  }
}

/**
 * 判断收支是否应该被禁用（根据已选账户）
 * 如果选了负债账户，则禁用相关的"不计入"收支
 */
function isActionDisabled(action: Action): boolean {
  // 如果收支不是"不计入"类型，不禁用
  if (!action.exempt) return false

  // 检查源账户是否为负债
  const sourceIsLiability = selectedAccount.value?.accountType === AccountType.LIABILITY
  // 检查目标账户是否为负债
  const targetIsLiability = selectedAccountTo.value?.accountType === AccountType.LIABILITY

  // 如果都不是负债，不禁用
  if (!sourceIsLiability && !targetIsLiability) return false

  // 普通不计入收支（非转账）：只要源账户是负债就禁用
  if (action.handle !== ActionHandle.TRANSFER) {
    return sourceIsLiability
  }

  // 内部转账的不计入
  const mode = action.exemptMode ?? ExemptMode.NONE

  if (sourceIsLiability) {
    // 源账户是负债：禁用转出不计入、两边不计入
    if (mode === ExemptMode.FROM_EXEMPT || mode === ExemptMode.BOTH_EXEMPT) {
      return true
    }
  }

  if (targetIsLiability) {
    // 目标账户是负债：禁用转入不计入、两边不计入
    if (mode === ExemptMode.TO_EXEMPT || mode === ExemptMode.BOTH_EXEMPT) {
      return true
    }
  }

  return false
}

/**
 * 获取账户禁用原因提示
 */
function getAccountDisabledReason(account: Account, panelType: 1 | 2): string {
  if (!isAccountDisabled(account, panelType)) return ''
  return '负债账户不支持此收支类型'
}

/**
 * 获取收支禁用原因提示
 */
function getActionDisabledReason(action: Action): string {
  if (!isActionDisabled(action)) return ''
  return '已选负债账户不支持此类型'
}

// 获取收支样式类
function getActionClass(handle: number | undefined): string {
  if (handle === 0) return 'income'
  if (handle === 1) return 'expense'
  if (handle === 2) return 'transfer'
  return ''
}

function getActionHandleText(handle: number | undefined): string {
  if (handle === 0) return '账户金额增加'
  if (handle === 1) return '账户金额减少'
  if (handle === 2) return '账户金额不变'
  return ''
}

// 获取不计入显示文本（内部转账根据模式显示）
function getExemptText(action: Action): string {
  if (!action.exempt) return ''
  // 收入/支出只显示"不计入"
  if (action.handle !== ActionHandle.TRANSFER) return '不计入'
  // 内部转账根据模式显示
  switch (action.exemptMode) {
    case ExemptMode.FROM_EXEMPT: return '转出不计入'
    case ExemptMode.TO_EXEMPT: return '转入不计入'
    case ExemptMode.BOTH_EXEMPT: return '两边不计入'
    default: return '不计入'
  }
}

// ==================== 数据加载 ====================
async function fetchActions() {
  try {
    const res = await actionApi.getAll()
    actions.value = res.data.data || []
    requestLocks.value.action = true

    // 新增模式 + 未从模板/store 恢复 + 当前未选时：默认选第一个支出
    if (
      !isEdit.value &&
      !selectedAction.value &&
      !flowAddStateStore.initialized
    ) {
      const firstExpense = actions.value.find(
        (a) => a.handle === ActionHandle.OUT && !a.exempt
      )
      if (firstExpense) onSelectAction(firstExpense)
    }

    checkAndLoadFlow()
  } catch (err) {
    console.error('获取收支列表失败', err)
  }
}

async function fetchAccounts() {
  try {
    const res = await accountApi.getAll()
    accounts.value = res.data.data || []
    requestLocks.value.account = true
    checkAndLoadFlow()
  } catch (err) {
    console.error('获取账户列表失败', err)
  }
}

async function fetchTags() {
  try {
    const res = await tagApi.getAll()
    tags.value = res.data.data || []
    fetchTemplates()
  } catch (err) {
    console.error('获取标签列表失败', err)
  }
}

async function fetchTemplates() {
  try {
    const res = selectedTag.value
      ? await templateApi.getByTagId(selectedTag.value.id)
      : await templateApi.getAll()
    templates.value = res.data.data || []
  } catch (err) {
    console.error('获取模板列表失败', err)
  }
}

// 检查并加载流水详情
function checkAndLoadFlow() {
  if (isEdit.value && requestLocks.value.action && requestLocks.value.account) {
    loadFlowDetail()
  }
}

async function loadFlowDetail() {
  if (!flowId.value) return

  showLoadingToast({ message: '加载中...', forbidClick: true, duration: 0 })

  try {
    const res = await flowApi.getById(flowId.value)
    const data = res.data.data

    // 流水不存在
    if (!data) {
      flowNotFound.value = true
      closeToast()
      showToast('该流水已被删除')
      return
    }

    money.value = data.money
    note.value = data.note || ''
    isCollect.value = data.collect
    chooseDate.value = data.fdate
    fromSource.value = data.from || null

    // 匹配收支（types 由 TypePicker 内部按 actionId 自行拉取）
    if (data.action) {
      selectedAction.value = actions.value.find(a => a.id === data.action.id) || null
    }

    // 匹配账户
    if (data.account) {
      selectedAccount.value = accounts.value.find(a => a.id === data.account.id) || null
    }

    // 匹配目标账户
    if (data.accountTo) {
      selectedAccountTo.value = accounts.value.find(a => a.id === data.accountTo!.id) || null
    }

    // 匹配分类（兼容旧数据 —— 连接符，统一显示为 /）
    if (data.type) {
      selectedType.value = {
        id: data.type.id,
        tname: data.type.tname.replace(/——/g, '/'),
      }
    }

    // 处理图片
    if (data.images && data.images.length > 0) {
      fileList.value = data.images.map(fileName => ({
        url: imageApi.getUrl(fileName),
        status: 'done' as const,
        serverFileName: fileName,
      }))
    }

    closeToast()
  } catch (err) {
    closeToast()
    flowNotFound.value = true
    showToast('流水加载失败，可能已被删除')
    console.error(err)
  }
}

// ==================== 表单交互 ====================
function onSelectAction(action: Action) {
  if (action.id === selectedAction.value?.id) return
  selectedAction.value = action
  selectedAccountTo.value = null
  selectedType.value = null
  // types 由 TypePicker 内部按 actionId 自动重新拉取
}

function openAccountSheet(type: 1 | 2) {
  accountSheetType.value = type
  showAccountSheet.value = true
}

function onSelectAccount(account: Account) {
  if (accountSheetType.value === 1) {
    selectedAccount.value = account
  } else {
    selectedAccountTo.value = account
  }
  showAccountSheet.value = false
}

function openTypePicker() {
  if (!selectedAction.value) {
    showToast('请先选择收支')
    return
  }
  showTypePicker.value = true
}

function onCalendarConfirm(date: Date) {
  showCalendar.value = false
  chooseDate.value = formatDate(date)
}

function formatDate(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

// ==================== 金额处理 ====================
function formatMoney(value: string): string {
  let result = value.replace(/[^\d.]/g, '')
  const parts = result.split('.')
  if (parts.length > 2) {
    result = parts[0] + '.' + parts.slice(1).join('')
  }
  if (parts.length === 2 && parts[1].length > 2) {
    result = parts[0] + '.' + parts[1].slice(0, 2)
  }
  return result
}

function onMoneyInput(e: Event) {
  const input = e.target as HTMLInputElement
  const formatted = formatMoney(input.value)
  money.value = formatted
  // 强制更新 input 显示值，防止中文输入
  input.value = formatted
}

function onMoneyBlur() {
  if (money.value && !money.value.includes('.')) {
    money.value = parseFloat(money.value).toFixed(2)
  } else if (money.value) {
    money.value = parseFloat(money.value).toFixed(2)
  }
}

// ==================== 追加分账单（编辑模式） ====================
function addChildMoney() {
  childMoneyList.value.push({
    index: Date.now(),
    money: '',
    note: '',
  })
}

function removeChildMoney(item: ChildMoney) {
  const idx = childMoneyList.value.indexOf(item)
  if (idx > -1) {
    childMoneyList.value.splice(idx, 1)
  }
}

function onChildMoneyInput(item: ChildMoney, e: Event) {
  const input = e.target as HTMLInputElement
  const formatted = formatMoney(input.value)
  item.money = formatted
  // 强制更新 input 显示值，防止中文输入
  input.value = formatted
}

// ==================== 图片上传 ====================
async function onAfterRead(
  file: any,
  detail: { index: number; name: string | number }
) {
  const files = Array.isArray(file) ? file : [file]
  const startIndex = Array.isArray(file) ? detail.index : detail.index

  for (let i = 0; i < files.length; i++) {
    const item = files[i]
    const fileIndex = startIndex + i

    // Vant 已经把文件添加到 fileList 中了，找到它并更新状态
    const fileItem = fileList.value[fileIndex] as FileItem
    if (!fileItem) continue

    fileItem.status = 'uploading'
    fileItem.message = '上传中...'

    try {
      // 压缩图片
      const compressedFile = await compressImage(item.file)

      // 上传压缩后的图片
      const res = await imageApi.upload(compressedFile)
      if (res.data.code === 0 && res.data.data) {
        fileItem.status = 'done'
        fileItem.message = ''
        fileItem.serverFileName = res.data.data.fileName
        fileItem.url = imageApi.getUrl(res.data.data.fileName)
      } else {
        fileItem.status = 'failed'
        fileItem.message = '失败'
      }
    } catch (err) {
      fileItem.status = 'failed'
      fileItem.message = '失败'
      console.error(err)
    }
  }
}

async function onDeleteImage(file: FileItem) {
  try {
    await showConfirmDialog({ message: '确定删除该图片吗？' })
    const idx = fileList.value.indexOf(file)
    if (idx > -1) {
      fileList.value.splice(idx, 1)
    }
    return true
  } catch {
    return false
  }
}

function onPreviewImage(file: FileItem) {
  const images = fileList.value.filter(f => f.url && f.status === 'done').map(f => f.url)
  const startPosition = images.indexOf(file.url)
  showImagePreview({
    images,
    startPosition: startPosition >= 0 ? startPosition : 0,
    closeable: true,
  })
}

// ==================== 快记模板 ====================
function onSelectTag(tag: Tag) {
  selectedTag.value = tag
  fetchTemplates()
}

function onClearTag() {
  selectedTag.value = null
  fetchTemplates()
}

function onSelectTemplate(template: Template) {
  showTemplatePopup.value = false
  showTemplateDetail.value = false
  showToast(template.name)

  // 先清空表单（保留备注和照片）
  money.value = ''
  selectedAction.value = null
  selectedAccount.value = null
  selectedAccountTo.value = null
  selectedType.value = null
  chooseDate.value = formatDate(new Date()) // 默认今天
  isCollect.value = false

  // 再用模板数据填充
  if (template.money) {
    money.value = template.money
  }
  if (template.action?.hname) {
    selectedAction.value = actions.value.find(a => a.id === template.action!.id) || null
  }
  if (template.account?.name) {
    selectedAccount.value = accounts.value.find(a => a.id === template.account!.id) || null
  }
  // 只有转账类型才设置目标账户
  if (template.action?.handle === 2 && template.accountTo?.name) {
    selectedAccountTo.value = accounts.value.find(a => a.id === template.accountTo!.id) || null
  }
  if (template.type?.tname) {
    selectedType.value = { id: template.type.id, tname: template.type.tname }
  }
  if (template.dateType !== undefined && template.dateType !== null) {
    if (template.dateType === 0) {
      chooseDate.value = formatDate(new Date())
    } else {
      const lastMonth = new Date()
      lastMonth.setDate(0)
      chooseDate.value = formatDate(lastMonth)
    }
  }
  // 设置备注来源
  note.value = `账单来源：${template.name}`
}

function showTemplateInfo(template: Template) {
  selectedTemplate.value = template
  // 先关闭模板列表弹窗，再显示详情对话框
  showTemplatePopup.value = false
  showTemplateDetail.value = true
}

function toTemplateManage() {
  // 保存当前表单状态
  saveFormState()
  router.push('/setting/template')
}

// 保存表单状态到 store
function saveFormState() {
  // 只保存已上传成功的图片
  const uploadedImages = fileList.value
    .filter(f => f.status === 'done' && f.serverFileName)
    .map(f => ({ url: f.url, serverFileName: f.serverFileName! }))

  flowAddStateStore.save({
    money: money.value,
    note: note.value,
    isCollect: isCollect.value,
    chooseDate: chooseDate.value,
    selectedAction: selectedAction.value,
    selectedAccount: selectedAccount.value,
    selectedAccountTo: selectedAccountTo.value,
    selectedType: selectedType.value,
    uploadedImages,
  })
}

// 从 store 恢复表单状态
function restoreFormState() {
  money.value = flowAddStateStore.money
  note.value = flowAddStateStore.note
  isCollect.value = flowAddStateStore.isCollect
  chooseDate.value = flowAddStateStore.chooseDate
  selectedAction.value = flowAddStateStore.selectedAction
  selectedAccount.value = flowAddStateStore.selectedAccount
  selectedAccountTo.value = flowAddStateStore.selectedAccountTo
  selectedType.value = flowAddStateStore.selectedType

  // 恢复图片列表
  if (flowAddStateStore.uploadedImages.length > 0) {
    fileList.value = flowAddStateStore.uploadedImages.map(img => ({
      url: img.url,
      status: 'done' as const,
      serverFileName: img.serverFileName,
    }))
  }

  // 恢复后重置 store，避免下次进入时再次恢复
  flowAddStateStore.reset()
}

// ==================== 表单验证 ====================
function validateForm(): boolean {
  if (!money.value) {
    showToast('请输入金额')
    return false
  }
  if (!selectedAction.value) {
    showToast('请选择收支')
    return false
  }
  if (!selectedAccount.value) {
    showToast('请选择账户')
    return false
  }
  if (isTransfer.value && !selectedAccountTo.value) {
    showToast('请选择转入账户')
    return false
  }
  if (!selectedType.value?.tname) {
    showToast('请选择分类')
    return false
  }
  if (!chooseDate.value) {
    showToast('请选择日期')
    return false
  }
  return true
}

// ==================== 金额计算 ====================
function addMoney(...moneyList: (string | number)[]): number {
  return moneyList.reduce<number>((sum, val) => {
    const num = typeof val === 'string' ? parseFloat(val) || 0 : val
    return sum + num
  }, 0)
}

// ==================== 删除 ====================
async function onDelete() {
  if (!flowId.value) return

  try {
    await showConfirmDialog({
      title: '确认删除',
      message: '删除后无法恢复，确定要删除这条账单吗？',
      confirmButtonText: '删除',
      confirmButtonColor: 'var(--color-expense)',
    })
  } catch {
    return
  }

  showLoadingToast({ message: '删除中...', forbidClick: true })

  try {
    await flowApi.delete(flowId.value)
    closeToast()
    showToast('删除成功')
    smartBack('/flow')
  } catch (err) {
    closeToast()
    showToast('删除失败')
    console.error(err)
  }
}

// ==================== 提交 ====================
async function onSubmit() {
  if (!validateForm()) return

  // 计算总金额（包含追加分账单）
  let submitMoney = parseFloat(money.value)
  let submitNote = note.value

  // 处理追加分账单
  if (isEdit.value && childMoneyList.value.length > 0) {
    const childMoneys = childMoneyList.value
      .filter(c => c.money && parseFloat(c.money) > 0)
      .map(c => parseFloat(c.money))

    if (childMoneys.length > 0) {
      submitMoney = addMoney(submitMoney, ...childMoneys)

      // 追加备注
      const childNotes = childMoneyList.value
        .filter(c => c.money && parseFloat(c.money) > 0)
        .map(c => `${c.note || '追加'}(¥${parseFloat(c.money).toFixed(2)})`)
        .join('\n')

      if (childNotes) {
        submitNote = submitNote ? `${submitNote}\n${childNotes}` : childNotes
      }
    }
  }

  try {
    await showConfirmDialog({
      title: '请确认账单',
      message: `总金额: ¥${submitMoney.toFixed(2)}\n备注: ${submitNote || '无'}`,
      confirmButtonText: '确认无误',
    })
  } catch {
    return
  }

  showLoadingToast({
    message: isEdit.value ? '保存中...' : '提交中...',
    forbidClick: true,
  })

  try {
    const uploadedImages = fileList.value
      .filter(item => item.status === 'done' && item.serverFileName)
      .map(item => item.serverFileName!)

    const params: FlowParams = {
      money: submitMoney.toFixed(2),
      fDate: chooseDate.value,
      actionId: selectedAction.value!.id,
      accountId: selectedAccount.value!.id,
      accountToId: selectedAccountTo.value?.id,
      typeId: selectedType.value!.id,
      collect: isCollect.value,
      note: submitNote,
      images: uploadedImages,
    }

    // 编辑模式清空 from 字段
    if (isEdit.value) {
      params.from = undefined
    }

    if (isEdit.value) {
      await flowApi.update(flowId.value!, params)
    } else {
      await flowApi.add(params)
    }

    closeToast()
    showToast(isEdit.value ? '保存成功' : '添加成功')
    // 智能返回：优先返回上一页，否则返回明细页
    smartBack('/flow')
  } catch (err) {
    closeToast()
    showToast('操作失败')
    console.error(err)
  }
}

// ==================== 导航 ====================
function onBack() {
  // 智能返回：优先返回上一页，否则返回明细页
  smartBack('/flow')
}

// ==================== 生命周期 ====================
onMounted(() => {
  // 重置滚动位置，避免从其他页面滚动状态穿透
  window.scrollTo(0, 0)

  fetchActions()
  fetchAccounts()

  if (!isEdit.value) {
    fetchTags()

    // 检查是否有保存的状态需要恢复（从模板管理页返回）
    if (flowAddStateStore.initialized) {
      restoreFormState()
    } else {
      // 默认日期为今天
      chooseDate.value = formatDate(new Date())
    }
  }
})

// 监听标签变化重新加载模板
watch(selectedTag, () => {
  fetchTemplates()
})
</script>

<template>
  <div class="flow-add-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="header-left" @click="onBack">
        <van-icon name="arrow-left" size="20" />
      </div>
      <div class="header-title">{{ isEdit ? '修改账单' : '新增账单' }}</div>
      <div v-if="!isEdit" class="header-right" @click="showTemplatePopup = true">
        <van-icon name="notes-o" size="20" />
      </div>
      <div v-else class="header-right placeholder"></div>
    </div>

    <!-- 页面内容 -->
    <div class="page-body">
      <!-- 金额 + 收支类型合体卡（背景跟随 selectedAction.handle 渐变） -->
      <div class="amount-action-card" :style="{ '--action-color': actionColor }">
        <div class="aa-money-wrapper">
          <span class="aa-money-symbol">¥</span>
          <input
            :value="money"
            @input="onMoneyInput"
            @blur="onMoneyBlur"
            type="text"
            inputmode="decimal"
            class="aa-money-input"
            placeholder="0.00"
          />
        </div>

        <!-- 主 chip 行：normal action + 右侧"不计入"折叠按钮 -->
        <div class="aa-chip-row">
          <div
            v-for="action in normalActions"
            :key="action.id"
            class="aa-chip"
            :class="{
              active: selectedAction?.id === action.id,
              [getActionClass(action.handle)]: true,
              disabled: isActionDisabled(action),
            }"
            @click="!isActionDisabled(action) && onSelectAction(action)"
          >
            {{ action.hname }}
          </div>
          <!-- 不计入 折叠 toggle，紧贴右边 -->
          <div
            v-if="exemptActions.length > 0"
            class="aa-exempt-toggle"
            @click="exemptActionsExpanded = !exemptActionsExpanded"
          >
            <span>不计入</span>
            <van-icon
              :name="exemptActionsExpanded ? 'arrow-up' : 'arrow-down'"
              size="11"
            />
          </div>
        </div>

        <!-- 不计入 action 折叠展开区 -->
        <Transition name="aa-collapse">
          <div
            v-show="exemptActionsExpanded && exemptActions.length > 0"
            class="aa-chip-row aa-chip-row-exempt"
          >
            <div
              v-for="action in exemptActions"
              :key="action.id"
              class="aa-chip exempt"
              :class="{
                active: selectedAction?.id === action.id,
                [getActionClass(action.handle)]: true,
                disabled: isActionDisabled(action),
              }"
              @click="!isActionDisabled(action) && onSelectAction(action)"
            >
              {{ action.hname }}
            </div>
          </div>
        </Transition>
      </div>

      <!-- 基本信息 -->
      <div class="form-card">
        <!-- 选择账户 -->
        <div class="form-item" @click="openAccountSheet(1)">
          <div class="form-item-left">
            <van-icon name="credit-pay" size="20" class="form-icon" />
            <span class="form-label">{{ isTransfer ? '转出账户' : '账户' }}</span>
          </div>
          <div class="form-item-right">
            <span v-if="selectedAccount" class="form-value">{{ selectedAccount.name }}</span>
            <span v-else class="form-placeholder">请选择</span>
            <van-icon name="arrow" size="16" class="arrow-icon" />
          </div>
        </div>

        <!-- 转入账户（转账时显示） -->
        <div v-if="isTransfer" class="form-item" @click="openAccountSheet(2)">
          <div class="form-item-left">
            <van-icon name="exchange" size="20" class="form-icon transfer-icon" />
            <span class="form-label">转入账户</span>
          </div>
          <div class="form-item-right">
            <span v-if="selectedAccountTo" class="form-value">{{ selectedAccountTo.name }}</span>
            <span v-else class="form-placeholder">请选择</span>
            <van-icon name="arrow" size="16" class="arrow-icon" />
          </div>
        </div>

        <!-- 选择分类 -->
        <div class="form-item" @click="openTypePicker">
          <div class="form-item-left">
            <van-icon name="apps-o" size="20" class="form-icon" />
            <span class="form-label">账单分类</span>
          </div>
          <div class="form-item-right">
            <span v-if="selectedType" class="form-value">{{ selectedType.tname }}</span>
            <span v-else class="form-placeholder">请选择</span>
            <van-icon name="arrow" size="16" class="arrow-icon" />
          </div>
        </div>

        <!-- 选择日期 -->
        <div class="form-item" @click="showCalendar = true">
          <div class="form-item-left">
            <van-icon name="calendar-o" size="20" class="form-icon" />
            <span class="form-label">账单日期</span>
          </div>
          <div class="form-item-right">
            <span v-if="chooseDate" class="form-value">{{ chooseDate }}</span>
            <span v-else class="form-placeholder">请选择</span>
            <van-icon name="arrow" size="16" class="arrow-icon" />
          </div>
        </div>
      </div>

      <!-- 其他信息 -->
      <div class="form-card">
        <!-- 收藏开关 -->
        <div class="form-item switch-item">
          <div class="form-item-left">
            <van-icon name="star-o" size="20" class="form-icon" />
            <span class="form-label">收藏账单</span>
          </div>
          <van-switch v-model="isCollect" size="22" />
        </div>

        <!-- 备注 -->
        <div class="form-item textarea-item">
          <div class="form-item-left">
            <van-icon name="edit" size="20" class="form-icon" />
            <span class="form-label">备注</span>
          </div>
          <textarea
            v-model="note"
            class="note-textarea"
            placeholder="添加备注..."
            maxlength="200"
            rows="2"
          />
        </div>

        <!-- 图片上传 -->
        <div class="form-item uploader-item">
          <div class="form-item-left">
            <van-icon name="photo-o" size="20" class="form-icon" />
            <span class="form-label">图片</span>
          </div>
          <van-uploader
            v-model="fileList"
            :max-count="9"
            :max-size="20 * 1024 * 1024"
            :after-read="onAfterRead"
            :before-delete="onDeleteImage"
            @click-preview="onPreviewImage"
            multiple
            class="uploader-grid"
          />
        </div>
      </div>

      <!-- 追加分账单（仅编辑模式） -->
      <template v-if="isEdit">
        <div v-if="childMoneyList.length > 0" class="form-card">
          <div class="section-header">
            <span class="section-title">追加分账单</span>
          </div>
          <div
            v-for="child in childMoneyList"
            :key="child.index"
            class="child-money-item"
          >
            <div class="child-money-row">
              <div class="child-input-group">
                <span class="child-symbol">¥</span>
                <input
                  :value="child.money"
                  @input="(e) => onChildMoneyInput(child, e)"
                  type="text"
                  inputmode="decimal"
                  class="child-money-input"
                  placeholder="金额"
                />
              </div>
              <input
                v-model="child.note"
                type="text"
                class="child-note-input"
                placeholder="备注"
              />
              <div class="child-delete" @click="removeChildMoney(child)">
                <van-icon name="cross" size="16" />
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <button v-if="isEdit && !flowNotFound" class="add-child-btn" @click="addChildMoney">
          <van-icon name="plus" size="16" />
          追加分账单
        </button>
        <!-- 编辑模式：删除 + 保存 平分 -->
        <div v-if="isEdit" class="button-row">
          <button
            class="delete-btn"
            :disabled="flowNotFound"
            @click="onDelete"
          >
            删除
          </button>
          <button
            class="submit-btn"
            :class="{ disabled: flowNotFound }"
            :disabled="flowNotFound"
            @click="onSubmit"
          >
            {{ flowNotFound ? '流水已删除' : '保存修改' }}
          </button>
        </div>
        <!-- 新增模式：单独提交按钮 -->
        <button
          v-else
          class="submit-btn full"
          @click="onSubmit"
        >
          提交账单
        </button>
      </div>
    </div>

    <!-- 账户选择器 -->
    <van-action-sheet v-model:show="showAccountSheet" :title="accountSheetType === 1 ? (isTransfer ? '选择转出账户' : '选择账户') : '选择转入账户'" teleport="body">
      <div class="sheet-list">
        <div
          v-for="account in accounts"
          :key="account.id"
          class="sheet-item account-sheet-item"
          :class="{
            active: accountSheetType === 1
              ? selectedAccount?.id === account.id
              : selectedAccountTo?.id === account.id,
            disabled: isAccountDisabled(account, accountSheetType),
            asset: account.accountType !== AccountType.LIABILITY,
            liability: account.accountType === AccountType.LIABILITY
          }"
          @click="!isAccountDisabled(account, accountSheetType) && onSelectAccount(account)"
        >
          <div class="account-left">
            <div class="account-type-tag" :class="account.accountType === AccountType.LIABILITY ? 'liability' : 'asset'">
              {{ account.accountType === AccountType.LIABILITY ? '负债' : '资产' }}
            </div>
            <div class="sheet-item-info">
              <span class="sheet-item-name">{{ account.name }}</span>
              <span v-if="isAccountDisabled(account, accountSheetType)" class="sheet-item-note disabled-reason">
                {{ getAccountDisabledReason(account, accountSheetType) }}
              </span>
            </div>
          </div>
          <div class="account-right">
            <span class="account-balance">¥{{ account.money }}</span>
            <span v-if="account.exemptMoney && parseFloat(account.exemptMoney) !== 0" class="account-exempt">
              不计入 ¥{{ account.exemptMoney }}
            </span>
          </div>
        </div>
        <div v-if="accounts.length === 0" class="empty-accounts">
          暂无可用账户
        </div>
      </div>
    </van-action-sheet>

    <!-- 分类选择器（一级 section + 二级 chip 网格 + 搜索） -->
    <TypePicker
      v-model="selectedType"
      v-model:open="showTypePicker"
      :action-id="selectedAction?.id ?? null"
    />

    <!-- 日期选择器 - 50%高度 -->
    <van-popup v-model:show="showCalendar" position="bottom" round teleport="body" :style="{ height: '50%' }" class="flow-calendar-popup">
      <van-calendar
        :show="true"
        :poppable="false"
        :show-confirm="false"
        :min-date="minDate"
        :max-date="maxDate"
        @confirm="onCalendarConfirm"
        :style="{ height: '100%' }"
      />
    </van-popup>

    <!-- 快记模板弹窗 -->
    <van-popup
      v-model:show="showTemplatePopup"
      position="bottom"
      round
      teleport="body"
      :style="{ height: '75%' }"
    >
      <div class="template-popup">
        <div class="template-header">
          <div class="template-header-left">
            <van-icon name="cross" size="20" @click="showTemplatePopup = false" />
          </div>
          <span class="template-title">快记模板</span>
          <span class="template-manage" @click="toTemplateManage">管理</span>
        </div>

        <!-- 标签筛选 -->
        <div class="tag-filter-section">
          <div class="tag-filter-header">
            <span class="filter-label">标签筛选</span>
            <span v-if="selectedTag" class="clear-tag" @click="onClearTag">清除</span>
          </div>
          <div class="tag-scroll">
            <div
              v-for="tag in tags"
              :key="tag.id"
              class="tag-chip"
              :class="{ active: selectedTag?.id === tag.id }"
              :style="selectedTag?.id === tag.id ? { background: tag.color } : {}"
              @click="onSelectTag(tag)"
            >
              <span class="tag-dot" :style="{ background: tag.color }" v-if="selectedTag?.id !== tag.id"></span>
              {{ tag.name }}
            </div>
          </div>
        </div>

        <!-- 模板列表 -->
        <div class="template-list">
          <div v-if="templates.length === 0" class="empty-templates">
            <van-icon name="notes-o" size="48" />
            <span>暂无模板</span>
          </div>
          <div
            v-for="template in templates"
            :key="template.id"
            class="template-card"
            @click="onSelectTemplate(template)"
          >
            <div class="template-card-main">
              <div class="template-card-left">
                <span class="template-name">{{ template.name }}</span>
                <div class="template-meta">
                  <span
                    v-if="template.action"
                    class="action-tag mini"
                    :class="getActionClass(template.action.handle)"
                  >
                    {{ template.action.hname }}
                  </span>
                  <span v-if="template.type" class="type-name">{{ template.type.tname }}</span>
                </div>
              </div>
              <div class="template-card-right">
                <span v-if="template.money" class="template-money">¥{{ template.money }}</span>
                <div
                  v-if="template.tag"
                  class="template-tag-dot"
                  :style="{ background: template.tag.color }"
                  :title="template.tag.name"
                ></div>
              </div>
            </div>
            <div class="template-card-action" @click.stop="showTemplateInfo(template)">
              <van-icon name="info-o" size="18" />
            </div>
          </div>
        </div>
      </div>
    </van-popup>

    <!-- 模板详情弹窗 -->
    <van-dialog
      v-model:show="showTemplateDetail"
      :title="selectedTemplate?.name || ''"
      show-cancel-button
      cancel-button-text="编辑"
      confirm-button-text="选择"
      @cancel="() => { showTemplateDetail = false; saveFormState(); router.push(`/setting/template/edit/${selectedTemplate?.id}`) }"
      @confirm="() => selectedTemplate && onSelectTemplate(selectedTemplate)"
    >
      <div v-if="selectedTemplate" class="template-detail">
        <div v-if="selectedTemplate.money" class="detail-row">
          <span class="detail-label">金额</span>
          <span class="detail-value">¥{{ selectedTemplate.money }}</span>
        </div>
        <div v-if="selectedTemplate.action" class="detail-row">
          <span class="detail-label">收支</span>
          <span class="action-tag small" :class="getActionClass(selectedTemplate.action.handle)">
            {{ selectedTemplate.action.hname }}
          </span>
        </div>
        <div v-if="selectedTemplate.account" class="detail-row">
          <span class="detail-label">{{ selectedTemplate.action?.handle === ActionHandle.TRANSFER ? '转出账户' : '账户' }}</span>
          <span class="detail-value">
            <span
              class="account-type-badge"
              :class="selectedTemplate.account.accountType === AccountType.LIABILITY ? 'liability' : 'asset'"
            >
              {{ selectedTemplate.account.accountType === AccountType.LIABILITY ? '负债' : '资产' }}
            </span>
            {{ selectedTemplate.account.name }}
          </span>
        </div>
        <div v-if="selectedTemplate.accountTo" class="detail-row">
          <span class="detail-label">转入账户</span>
          <span class="detail-value">
            <span
              class="account-type-badge"
              :class="selectedTemplate.accountTo.accountType === AccountType.LIABILITY ? 'liability' : 'asset'"
            >
              {{ selectedTemplate.accountTo.accountType === AccountType.LIABILITY ? '负债' : '资产' }}
            </span>
            {{ selectedTemplate.accountTo.name }}
          </span>
        </div>
        <div v-if="selectedTemplate.type" class="detail-row">
          <span class="detail-label">分类</span>
          <span class="detail-value">{{ selectedTemplate.type.tname }}</span>
        </div>
        <div v-if="selectedTemplate.dateType !== undefined && selectedTemplate.dateType !== null" class="detail-row">
          <span class="detail-label">日期类型</span>
          <span class="detail-value">{{ selectedTemplate.dateType === 1 ? '补上月' : '记本月' }}</span>
        </div>
      </div>
    </van-dialog>
  </div>
</template>

<style scoped>
.flow-add-page {
  min-height: 100vh;
  background: var(--color-bg-page);
}

/* 顶部导航 */
.page-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 50;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.header-left,
.header-right {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: var(--color-bg-card);
  color: var(--color-text-primary);
}

.header-right.placeholder {
  background: transparent;
}

.header-left:active,
.header-right:active {
  opacity: 0.7;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.page-body {
  padding: 76px 16px 32px;
}

/* === 金额 + 收支类型 合体卡（紧凑版） === */
.amount-action-card {
  background: linear-gradient(
    135deg,
    var(--action-color) 0%,
    color-mix(in srgb, var(--action-color) 70%, #000) 100%
  );
  border-radius: 18px;
  padding: 14px 16px 12px;
  margin-bottom: 12px;
  color: #fff;
  transition: background 0.3s ease;
}

.aa-money-wrapper {
  display: flex;
  align-items: baseline;
  margin-bottom: 0;
  padding-bottom: 12px;
}

.aa-money-symbol {
  font-size: 22px;
  font-weight: 600;
  margin-right: 4px;
  color: #fff;
}

.aa-money-input {
  flex: 1;
  width: 100%;
  font-size: 40px;
  font-weight: 700;
  color: #fff;
  background: transparent;
  border: none;
  outline: none;
  letter-spacing: -1px;
  padding: 0;
  line-height: 1.1;
}

.aa-money-input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

/* chip 行 */
.aa-chip-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.18);
}

.aa-chip {
  padding: 5px 12px;
  border-radius: 14px;
  font-size: 12.5px;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.18);
  color: rgba(255, 255, 255, 0.9);
  transition: background 0.2s, color 0.2s, opacity 0.2s;
  user-select: none;
}

.aa-chip:active {
  background: rgba(255, 255, 255, 0.28);
}

/* 选中：白底 + 主色文字（颜色按 handle 区分） */
.aa-chip.active.income {
  background: #fff;
  color: var(--color-income);
}

.aa-chip.active.expense {
  background: #fff;
  color: var(--color-expense);
}

.aa-chip.active.transfer {
  background: #fff;
  color: var(--color-transfer);
}

.aa-chip.disabled {
  opacity: 0.4;
  pointer-events: none;
}

/* 不计入 chip 默认半透明（淡化层级） */
.aa-chip.exempt {
  opacity: 0.85;
}

.aa-chip.exempt.active {
  opacity: 1;
}

/* "不计入"折叠按钮（在主 chip 行内，靠 margin-left:auto 推到右边） */
.aa-exempt-toggle {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 11.5px;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.85);
  user-select: none;
}

.aa-exempt-toggle:active {
  background: rgba(255, 255, 255, 0.2);
}

.aa-chip-row-exempt {
  margin-top: 6px;
  padding-top: 8px;
  border-top: 1px dashed rgba(255, 255, 255, 0.18);
}

.aa-collapse-enter-active,
.aa-collapse-leave-active {
  transition: all 0.25s ease;
  overflow: hidden;
}

.aa-collapse-enter-from,
.aa-collapse-leave-to {
  opacity: 0;
  max-height: 0;
  margin-top: 0;
}

/* 表单卡片 */
.form-card {
  background: var(--color-bg-card);
  border-radius: 16px;
  margin-bottom: 16px;
  overflow: hidden;
}

.form-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border-light);
}

.form-item:last-child {
  border-bottom: none;
}

.form-item-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.form-icon {
  color: var(--color-text-tertiary);
}

.form-icon.transfer-icon {
  color: var(--color-transfer);
}

.form-label {
  font-size: 15px;
  color: var(--color-text-primary);
}

.form-item-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-value {
  font-size: 15px;
  color: var(--color-text-primary);
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  /* 长分类路径"餐饮/外卖" 优先保留末尾段（用 direction: rtl + 显示左对齐） */
  direction: rtl;
  text-align: left;
}

.form-placeholder {
  font-size: 15px;
  color: var(--color-text-placeholder);
}

.arrow-icon {
  color: var(--color-text-tertiary);
}

/* 收支标签 */
.action-tag {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 6px;
  font-weight: 500;
}

.action-tag.small {
  font-size: 11px;
  padding: 3px 8px;
}

.action-tag.mini {
  font-size: 10px;
  padding: 2px 6px;
}

.action-tag.income {
  background: var(--color-income-bg);
  color: var(--color-income);
}

.action-tag.expense {
  background: var(--color-expense-bg);
  color: var(--color-expense);
}

.action-tag.transfer {
  background: var(--color-transfer-bg);
  color: var(--color-transfer);
}

.exempt-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--color-bg-page);
  color: var(--color-text-tertiary);
}

.exempt-badge.small {
  font-size: 10px;
  padding: 2px 6px;
}

/* Switch 项 */
.switch-item {
  padding: 14px 20px;
}

/* 备注输入 */
.textarea-item {
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
}

.note-textarea {
  width: 100%;
  min-height: 60px;
  padding: 12px;
  font-size: 14px;
  color: var(--color-text-primary);
  background: var(--color-bg-page);
  border: none;
  border-radius: 10px;
  outline: none;
  resize: none;
  box-sizing: border-box;
}

.note-textarea::placeholder {
  color: var(--color-text-placeholder);
}

/* 图片上传 */
.uploader-item {
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
}

/* van-uploader 强制 3x3 网格：wrapper 用 grid，preview/upload 自适应正方形 */
.uploader-grid {
  width: 100%;
}

.uploader-grid :deep(.van-uploader__wrapper) {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  width: 100%;
}

.uploader-grid :deep(.van-uploader__preview),
.uploader-grid :deep(.van-uploader__upload) {
  margin: 0 !important;
  width: 100% !important;
  height: auto !important;
  aspect-ratio: 1 / 1;
  border-radius: 10px;
  overflow: hidden;
}

.uploader-grid :deep(.van-uploader__preview-image),
.uploader-grid :deep(.van-uploader__file) {
  width: 100% !important;
  height: 100% !important;
  border-radius: 10px;
}

.uploader-grid :deep(.van-uploader__preview-image img) {
  border-radius: 10px;
}

/* 删除按钮放大（默认 18×18，圆角后显小） */
.uploader-grid :deep(.van-uploader__preview-delete) {
  width: 24px;
  height: 24px;
  border-radius: 0 10px 0 12px;
}

.uploader-grid :deep(.van-uploader__preview-delete-icon) {
  font-size: 14px;
  top: 2px;
  right: 2px;
}

/* 追加分账单 */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px 10px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.child-money-item {
  padding: 0 20px 12px;
}

.child-money-row {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.child-input-group {
  display: flex;
  align-items: center;
  background: var(--color-bg-page);
  padding: 10px 12px;
  border-radius: 10px;
  flex-shrink: 0;
  width: 100px;
}

.child-symbol {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin-right: 4px;
}

.child-money-input {
  flex: 1;
  width: 100%;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  background: transparent;
  border: none;
  outline: none;
}

.child-money-input::placeholder {
  color: var(--color-text-placeholder);
  font-weight: 400;
}

.child-note-input {
  flex: 1;
  min-width: 0;
  font-size: 14px;
  color: var(--color-text-primary);
  background: var(--color-bg-page);
  border: none;
  outline: none;
  padding: 10px 12px;
  border-radius: 10px;
  box-sizing: border-box;
}

.child-note-input::placeholder {
  color: var(--color-text-placeholder);
}

.child-delete {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
  border-radius: 50%;
  background: var(--color-bg-page);
}

.child-delete:active {
  background: var(--color-expense-bg);
  color: var(--color-expense);
}

/* 操作按钮 */
.action-buttons {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.add-child-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  padding: 14px;
  font-size: 15px;
  font-weight: 500;
  color: var(--color-transfer);
  background: var(--color-bg-card);
  border: 1px dashed var(--color-border);
  border-radius: 12px;
  cursor: pointer;
}

.add-child-btn:active {
  opacity: 0.8;
}

/* 按钮行（平分布局） */
.button-row {
  display: flex;
  gap: 12px;
}

.button-row .delete-btn,
.button-row .submit-btn {
  flex: 1;
}

.delete-btn {
  padding: 16px;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-expense);
  background: var(--color-expense-bg);
  border: none;
  border-radius: 14px;
  cursor: pointer;
}

.delete-btn:active {
  opacity: 0.9;
}

.delete-btn:disabled {
  background: var(--color-text-quaternary);
  color: var(--color-text-tertiary);
  cursor: not-allowed;
}

.submit-btn {
  padding: 16px;
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  background: var(--color-transfer);
  border: none;
  border-radius: 14px;
  cursor: pointer;
}

.submit-btn.full {
  width: 100%;
}

.submit-btn:active {
  opacity: 0.9;
}

.submit-btn.disabled {
  background: var(--color-text-quaternary);
  cursor: not-allowed;
}

.submit-btn.disabled:active {
  opacity: 1;
}

/* ActionSheet 列表 */
.sheet-list {
  padding: 16px;
  max-height: 50vh;
  overflow-y: auto;
}

/* 空账户提示 */
.empty-accounts {
  padding: 40px 0;
  text-align: center;
  font-size: 14px;
  color: var(--color-text-tertiary);
}

.sheet-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: var(--color-bg-page);
  border-radius: 12px;
  margin-bottom: 10px;
}

.sheet-item:last-child {
  margin-bottom: 0;
}

.sheet-item.active {
  background: var(--color-transfer);
}

.sheet-item.active.income {
  background: var(--color-income);
}

.sheet-item.active.expense {
  background: var(--color-expense);
}

.sheet-item.active.transfer {
  background: var(--color-transfer);
}

.sheet-item.active .sheet-item-name,
.sheet-item.active .sheet-item-note,
.sheet-item.active .account-balance {
  color: #fff;
}

.sheet-item.active .action-tag {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

.sheet-item.active .exempt-badge {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

.sheet-item:active {
  opacity: 0.8;
}

/* 禁用状态 */
.sheet-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.sheet-item.disabled:active {
  opacity: 0.5;
}

.disabled-reason {
  font-size: 11px;
  color: var(--color-text-tertiary);
  margin-top: 2px;
}

/* 账户选择器项 */
.account-sheet-item {
  gap: 10px;
}

.account-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.account-left .sheet-item-info {
  gap: 2px;
}

.account-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  flex-shrink: 0;
}

.account-exempt {
  font-size: 11px;
  color: var(--color-text-tertiary);
}

.sheet-item.active .account-exempt {
  color: rgba(255, 255, 255, 0.8);
}

.account-type-tag {
  font-size: 10px;
  padding: 4px 6px;
  border-radius: 4px;
  font-weight: 500;
  flex-shrink: 0;
}

.account-type-tag.asset {
  background: var(--color-income-bg);
  color: var(--color-income);
}

.account-type-tag.liability {
  background: var(--color-expense-bg);
  color: var(--color-expense);
}

/* 账户选中状态 - 资产绿色 */
.sheet-item.account-sheet-item.active.asset {
  background: var(--color-income);
}

.sheet-item.account-sheet-item.active.asset .account-type-tag {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

/* 账户选中状态 - 负债红色 */
.sheet-item.account-sheet-item.active.liability {
  background: var(--color-expense);
}

.sheet-item.account-sheet-item.active.liability .account-type-tag {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

.sheet-item-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sheet-item-name {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.sheet-item-tags {
  display: flex;
  align-items: center;
  gap: 6px;
}

.sheet-item-note {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.account-balance {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.check-icon {
  color: #fff;
  font-size: 20px;
}

/* ========== 快记模板弹窗样式重构 ========== */
.template-popup {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-page);
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--color-bg-card);
  border-bottom: 1px solid var(--color-border-light);
}

.template-header-left {
  width: 40px;
  color: var(--color-text-primary);
}

.template-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.template-manage {
  font-size: 14px;
  color: var(--color-transfer);
  padding: 6px 12px;
}

/* 标签筛选 */
.tag-filter-section {
  padding: 16px 20px;
  background: var(--color-bg-card);
}

.tag-filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.filter-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.clear-tag {
  font-size: 13px;
  color: var(--color-transfer);
}

.tag-scroll {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 4px;
  -webkit-overflow-scrolling: touch;
}

.tag-scroll::-webkit-scrollbar {
  display: none;
}

.tag-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 20px;
  font-size: 13px;
  color: var(--color-text-primary);
  background: var(--color-bg-page);
  white-space: nowrap;
  flex-shrink: 0;
}

.tag-chip.active {
  color: #fff;
}

.tag-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

/* 模板列表 */
.template-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.empty-templates {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px 0;
  color: var(--color-text-tertiary);
}

.template-card {
  display: flex;
  align-items: center;
  padding: 16px;
  background: var(--color-bg-card);
  border-radius: 14px;
  margin-bottom: 12px;
}

.template-card:active {
  opacity: 0.85;
}

.template-card-main {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.template-card-left {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.template-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.template-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.type-name {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.template-card-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.template-money {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.template-tag-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.template-card-action {
  padding: 8px;
  margin-left: 8px;
  color: var(--color-text-tertiary);
}

/* 模板详情 */
.template-detail {
  padding: 16px 20px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--color-border-light);
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.detail-value {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: var(--color-text-primary);
}

/* 模板详情中的账户类型标签 */
.template-detail .account-type-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.template-detail .account-type-badge.asset {
  background: var(--color-income-bg);
  color: var(--color-income);
}

.template-detail .account-type-badge.liability {
  background: var(--color-expense-bg);
  color: var(--color-expense);
}
</style>

<!-- 非 scoped 样式 -->
<style>
.flow-add-page .page-header {
  background: rgba(245, 245, 245, 0.8);
}

html.dark .flow-add-page .page-header {
  background: rgba(10, 10, 10, 0.8);
}

/* ActionSheet 暗黑模式 */
html.dark .flow-add-page .van-action-sheet {
  background: var(--color-bg-card);
}

html.dark .flow-add-page .van-action-sheet__header {
  color: var(--color-text-primary);
}

/* 模板弹窗暗黑模式 */
html.dark .flow-add-page .van-popup {
  background: var(--color-bg-page);
}

/* Dialog 暗黑模式 */
html.dark .flow-add-page .van-dialog {
  background: var(--color-bg-card);
}

html.dark .flow-add-page .van-dialog__header {
  color: var(--color-text-primary);
}

/* Uploader 样式：preview 间距由 .uploader-grid 的 grid gap 控制 */
.flow-add-page .van-uploader__upload {
  background: var(--color-bg-page);
  border-radius: 8px;
}

html.dark .flow-add-page .van-uploader__upload {
  background: var(--color-bg-elevated);
}
</style>

<!-- 日历暗黑模式 - 全局样式（因为 teleport 到 body） -->
<style>
/* 日历弹窗暗黑模式 */
html.dark .flow-calendar-popup {
  background: var(--color-bg-card);
}

html.dark .flow-calendar-popup .van-calendar {
  background: var(--color-bg-card);
}

html.dark .flow-calendar-popup .van-calendar__header {
  background: var(--color-bg-card);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

html.dark .flow-calendar-popup .van-calendar__header-title,
html.dark .flow-calendar-popup .van-calendar__header-subtitle {
  color: var(--color-text-primary);
}

html.dark .flow-calendar-popup .van-calendar__weekday {
  color: var(--color-text-secondary);
}

html.dark .flow-calendar-popup .van-calendar__day {
  color: var(--color-text-primary);
}

html.dark .flow-calendar-popup .van-calendar__month-title {
  color: var(--color-text-primary);
}

html.dark .flow-calendar-popup .van-calendar__month-mark {
  color: rgba(255, 255, 255, 0.05);
}

html.dark .flow-calendar-popup .van-calendar__selected-day {
  background: var(--color-transfer);
  color: #fff;
}

html.dark .flow-calendar-popup .van-calendar__day--today {
  color: var(--color-transfer);
}

html.dark .flow-calendar-popup .van-calendar__day--disabled {
  color: var(--color-text-tertiary);
}

html.dark .flow-calendar-popup .van-calendar__bottom-info {
  color: var(--color-text-secondary);
}

html.dark .flow-calendar-popup .van-calendar__footer {
  background: var(--color-bg-card);
}

html.dark .flow-calendar-popup .van-calendar__confirm {
  background: var(--color-transfer);
  color: #fff;
}
</style>
