<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Close,
  Calendar,
  Wallet,
  PriceTag,
  Document,
  Picture,
  Star,
  StarFilled,
  Plus,
  Delete,
  ArrowRight,
  ArrowDown,
  CreditCard,
  ArrowLeft,
  Loading,
} from '@element-plus/icons-vue'
import alipayIcon from '@shared/assets/icons/alipay.svg'
import wechatIcon from '@shared/assets/icons/wechat.svg'
import housingFundIcon from '@shared/assets/icons/housing-fund.svg'
import cashIcon from '@shared/assets/icons/cash.svg'
import { Calendar as VanCalendar } from 'vant'
import 'vant/es/calendar/style'
import { flowApi, type FlowParams, type FlowDetail } from '@shared/api/flow'
import { actionApi, type Action } from '@shared/api/action'
import { accountApi, type Account } from '@shared/api/account'
import { typeApi, type TypeWithChildren } from '@shared/api/type'
import { templateApi, type Template } from '@shared/api/template'
import { tagApi, type Tag } from '@shared/api/tag'
import { imageApi } from '@shared/api/image'
import { compressImage } from '@shared/utils/image-compress'

// ==================== Props & Emits ====================
const props = defineProps<{
  visible: boolean
  flowId?: number | null
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'success': []
}>()

// ==================== 抽屉状态 ====================
const drawerVisible = ref(false)
const loading = ref(false)
const submitting = ref(false)

// 模式判断
const isEdit = computed(() => !!props.flowId)

// 不计入 action 折叠状态（默认隐藏）
const exemptActionsExpanded = ref(false)

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

// 日历面板 - Vant Calendar
const calendarMinDate = computed(() => {
  const d = new Date()
  d.setFullYear(d.getFullYear() - 1)
  return d
})
const calendarMaxDate = computed(() => new Date())
const calendarDefaultDate = computed(() => {
  if (chooseDate.value) {
    return new Date(chooseDate.value.replace(/-/g, '/'))
  }
  return new Date()
})

// 分类面板 - 展开状态
const expandedTypeIds = ref<number[]>([])

// 图片上传
interface FileItem {
  url: string
  status: 'uploading' | 'done' | 'failed'
  serverFileName?: string
  file?: File
}
const fileList = ref<FileItem[]>([])

// 图片预览
const previewVisible = ref(false)
const previewUrl = ref('')

// 追加分账单（编辑模式）
interface ChildMoney {
  index: number
  money: string
  note: string
}
const childMoneyList = ref<ChildMoney[]>([])

// ==================== 列表数据 ====================
const actions = ref<Action[]>([])
const accounts = ref<Account[]>([])
const types = ref<TypeWithChildren[]>([])
const tags = ref<Tag[]>([])
const templates = ref<Template[]>([])

// ==================== 面板状态 ====================
const accountPanelVisible = ref(false)
const accountPanelType = ref<1 | 2>(1) // 1=源账户, 2=目标账户
const typePanelVisible = ref(false)
const datePanelVisible = ref(false)
const datePanelKey = ref(0) // 用于强制日历重新渲染
const templatePanelVisible = ref(false)

// 模板相关
const selectedTag = ref<Tag | null>(null)
const expandedTemplateIds = ref<number[]>([])

// 动态抽屉宽度
const drawerSize = computed(() => {
  let width = 480 // 基础宽度（主编辑区）
  if (accountPanelVisible.value) width += 360
  if (typePanelVisible.value) width += 400
  if (datePanelVisible.value) width += 340
  if (templatePanelVisible.value) width += 400
  return `${width}px`
})

// 关闭所有面板
function closeAllPanels() {
  accountPanelVisible.value = false
  typePanelVisible.value = false
  datePanelVisible.value = false
  templatePanelVisible.value = false
}

// ==================== 计算属性 ====================
const isTransfer = computed(() => selectedAction.value?.handle === 2)

// 普通 action 和 不计入的 action 分开
const normalActions = computed(() => actions.value.filter(a => !a.exempt))
const exemptActions = computed(() => actions.value.filter(a => a.exempt))

// 收支类型分组
const actionGroups = computed(() => {
  const income = actions.value.filter(a => a.handle === 0)
  const expense = actions.value.filter(a => a.handle === 1)
  const transfer = actions.value.filter(a => a.handle === 2)
  return { income, expense, transfer }
})

// 当前收支类型的颜色
const actionColor = computed(() => {
  if (!selectedAction.value) return 'var(--color-transfer)'
  switch (selectedAction.value.handle) {
    case 0: return 'var(--color-income)'
    case 1: return 'var(--color-expense)'
    case 2: return 'var(--color-transfer)'
    default: return 'var(--color-transfer)'
  }
})

// ==================== 监听 ====================
watch(() => props.visible, (val) => {
  drawerVisible.value = val
  if (val) {
    initData()
  }
})

watch(drawerVisible, (val) => {
  emit('update:visible', val)
  if (!val) {
    resetForm()
  }
})

// ==================== 初始化 ====================
async function initData() {
  loading.value = true
  try {
    // 并行加载基础数据
    const [actionsRes, accountsRes] = await Promise.all([
      actionApi.getAll(),
      accountApi.getAll(),
    ])
    actions.value = actionsRes.data.data || []
    accounts.value = accountsRes.data.data || []

    // 如果是编辑模式，加载流水详情
    if (isEdit.value && props.flowId) {
      await loadFlowDetail(props.flowId)
    } else {
      // 新增模式：加载标签和模板
      await loadTagsAndTemplates()
      // 默认日期为今天
      chooseDate.value = formatDate(new Date())
      // 默认选择第一个支出类型
      if (actionGroups.value.expense.length > 0) {
        onSelectAction(actionGroups.value.expense[0])
      }
    }
  } catch (err) {
    console.error('初始化失败', err)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

async function loadFlowDetail(id: number) {
  const res = await flowApi.getById(id)
  const data = res.data.data

  money.value = data.money
  note.value = data.note || ''
  isCollect.value = data.collect
  chooseDate.value = data.fdate

  // 匹配收支
  if (data.action) {
    selectedAction.value = actions.value.find(a => a.id === data.action.id) || null
    if (selectedAction.value) {
      await fetchTypesByAction()
    }
  }

  // 匹配账户
  if (data.account) {
    selectedAccount.value = accounts.value.find(a => a.id === data.account.id) || null
  }

  // 匹配目标账户
  if (data.accountTo) {
    selectedAccountTo.value = accounts.value.find(a => a.id === data.accountTo!.id) || null
  }

  // 匹配分类
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
}

async function loadTagsAndTemplates() {
  try {
    const tagsRes = await tagApi.getAll()
    tags.value = tagsRes.data.data || []
    await fetchTemplates()
  } catch (err) {
    console.error('加载标签模板失败', err)
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

async function fetchTypesByAction() {
  if (!selectedAction.value) return
  try {
    const res = await typeApi.getByActionId(selectedAction.value.id)
    types.value = res.data.data || []
  } catch (err) {
    console.error('获取分类列表失败', err)
  }
}

// ==================== 表单交互 ====================
function onSelectAction(action: Action) {
  if (action.id === selectedAction.value?.id) return
  selectedAction.value = action
  selectedAccountTo.value = null
  selectedType.value = null
  fetchTypesByAction()
}

function openAccountPanel(type: 1 | 2) {
  closeAllPanels()
  accountPanelType.value = type
  accountPanelVisible.value = true
}

function onSelectAccount(account: Account) {
  if (accountPanelType.value === 1) {
    selectedAccount.value = account
  } else {
    selectedAccountTo.value = account
  }
  accountPanelVisible.value = false
}

function openTypePanel() {
  if (!selectedAction.value) {
    ElMessage.warning('请先选择收支类型')
    return
  }
  closeAllPanels()
  typePanelVisible.value = true
}

function onSelectType(type: TypeWithChildren, parent?: TypeWithChildren) {
  selectedType.value = {
    id: type.id,
    tname: parent ? `${parent.tname}/${type.tname}` : type.tname,
  }
  typePanelVisible.value = false
}

function openDatePanel() {
  closeAllPanels()
  datePanelKey.value++ // 强制日历重新渲染
  datePanelVisible.value = true
}

function onSelectDate(date: Date) {
  chooseDate.value = formatDate(date)
  datePanelVisible.value = false
}

function openTemplatePanel() {
  closeAllPanels()
  templatePanelVisible.value = true
  loadTagsAndTemplates()
}

// ==================== 金额处理 ====================
function formatMoneyInput(value: string): string {
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
  money.value = formatMoneyInput(input.value)
  input.value = money.value
}

function onMoneyBlur() {
  if (money.value) {
    money.value = parseFloat(money.value).toFixed(2)
  }
}

// ==================== 快记模板 ====================
function onSelectTag(tag: Tag | null) {
  selectedTag.value = tag
  fetchTemplates()
}

// 判断模板是否有详情可展开
function hasTemplateDetails(item: Template): boolean {
  return !!(
    item.account?.name ||
    item.accountTo?.name ||
    item.type?.tname ||
    (item.dateType !== undefined && item.dateType !== null)
  )
}

// 切换模板展开状态
function toggleTemplateExpand(id: number) {
  const idx = expandedTemplateIds.value.indexOf(id)
  if (idx >= 0) {
    expandedTemplateIds.value.splice(idx, 1)
  } else {
    expandedTemplateIds.value.push(id)
  }
}

function onSelectTemplate(template: Template) {
  templatePanelVisible.value = false
  ElMessage.success(`已应用模板：${template.name}`)

  // 1. 先清空所有模板相关字段（保留 isCollect、fileList）
  money.value = ''
  selectedAction.value = null
  selectedAccount.value = null
  selectedAccountTo.value = null
  selectedType.value = null
  types.value = []
  // 日期保持不变，除非模板有指定

  // 2. 填充模板数据
  if (template.money) {
    money.value = template.money
  }

  // 检查 action 是否有效（hname 存在）
  if (template.action?.id != null && template.action.hname) {
    selectedAction.value = actions.value.find(a => a.id === template.action!.id) || null
    if (selectedAction.value) {
      fetchTypesByAction()
    }
  }

  // 检查 account 是否有效（name 存在）
  if (template.account?.id != null && template.account.name) {
    selectedAccount.value = accounts.value.find(a => a.id === template.account!.id) || null
  }

  // 检查 accountTo 是否有效（转账时，name 存在）
  if (template.action?.handle === 2 && template.accountTo?.id != null && template.accountTo.name) {
    selectedAccountTo.value = accounts.value.find(a => a.id === template.accountTo!.id) || null
  }

  // 检查 type 是否有效（tname 存在）
  if (template.type?.id != null && template.type.tname) {
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

  // 3. 自动填充备注为模板来源
  note.value = `账单来源：${template.name}`
}

// ==================== 图片上传 ====================
async function onUploadImage(e: Event) {
  const input = e.target as HTMLInputElement
  const files = input.files
  if (!files?.length) return

  for (const file of Array.from(files)) {
    if (fileList.value.length >= 3) {
      ElMessage.warning('最多上传3张图片')
      break
    }

    const fileItem: FileItem = {
      url: URL.createObjectURL(file),
      status: 'uploading',
      file,
    }
    const itemIndex = fileList.value.length
    fileList.value.push(fileItem)

    try {
      const compressedFile = await compressImage(file)
      const res = await imageApi.upload(compressedFile)
      if (res.data.code === 0 && res.data.data) {
        // 通过索引更新，确保响应式触发
        fileList.value[itemIndex] = {
          ...fileList.value[itemIndex],
          status: 'done',
          serverFileName: res.data.data.fileName,
          url: imageApi.getUrl(res.data.data.fileName),
        }
      } else {
        fileList.value[itemIndex] = {
          ...fileList.value[itemIndex],
          status: 'failed',
        }
      }
    } catch (err) {
      fileList.value[itemIndex] = {
        ...fileList.value[itemIndex],
        status: 'failed',
      }
      console.error(err)
    }
  }

  input.value = ''
}

function onDeleteImage(index: number) {
  fileList.value.splice(index, 1)
}

function onPreviewImage(file: FileItem) {
  if (file.status === 'done' && file.url) {
    previewUrl.value = file.url
    previewVisible.value = true
  }
}

// ==================== 追加分账单 ====================
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
  item.money = formatMoneyInput(input.value)
  input.value = item.money
}

// ==================== 工具函数 ====================
function formatDate(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function getActionClass(handle: number | undefined): string {
  if (handle === 0) return 'income'
  if (handle === 1) return 'expense'
  if (handle === 2) return 'transfer'
  return ''
}

// 根据账户名获取图标
function getAccountIcon(name: string | undefined): string | null {
  if (!name) return null
  if (name.includes('支付宝')) return alipayIcon
  if (name.includes('微信')) return wechatIcon
  if (name.includes('公积金')) return housingFundIcon
  if (name.includes('现金')) return cashIcon
  return null
}

// 格式化金额显示
function formatMoneyDisplay(money: string | undefined) {
  if (!money || money === '0' || money === '0.00') return '¥0.00'
  return `¥${money}`
}

// 分类展开切换
function toggleTypeExpand(id: number) {
  const idx = expandedTypeIds.value.indexOf(id)
  if (idx >= 0) {
    expandedTypeIds.value.splice(idx, 1)
  } else {
    expandedTypeIds.value.push(id)
  }
}

function isTypeExpanded(id: number) {
  return expandedTypeIds.value.includes(id)
}

function resetForm() {
  money.value = ''
  note.value = ''
  isCollect.value = false
  chooseDate.value = ''
  selectedAction.value = null
  selectedAccount.value = null
  selectedAccountTo.value = null
  selectedType.value = null
  fileList.value = []
  types.value = []
  selectedTag.value = null
  childMoneyList.value = []
  exemptActionsExpanded.value = false
}

// ==================== 表单验证 ====================
function validateForm(): boolean {
  const errors: string[] = []

  if (!money.value) {
    errors.push('金额')
  }
  if (!selectedAction.value) {
    errors.push('收支类型')
  }
  if (!selectedAccount.value) {
    errors.push('账户')
  }
  if (isTransfer.value && !selectedAccountTo.value) {
    errors.push('目标账户')
  }
  if (!selectedType.value) {
    errors.push('分类')
  }
  if (!chooseDate.value) {
    errors.push('日期')
  }

  if (errors.length > 0) {
    ElMessage.error(`请填写必填项：${errors.join('、')}`)
    return false
  }
  return true
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
      submitMoney = childMoneys.reduce((sum, val) => sum + val, submitMoney)

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
    await ElMessageBox.confirm(
      `确认${isEdit.value ? '保存' : '提交'}账单？\n金额: ¥${submitMoney.toFixed(2)}\n${submitNote ? `备注: ${submitNote}` : ''}`,
      isEdit.value ? '保存账单' : '提交账单',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'info',
      }
    )
  } catch {
    return
  }

  submitting.value = true

  // 再次确认必填字段存在（双重保险）
  if (!selectedAction.value || !selectedAccount.value || !selectedType.value || !chooseDate.value) {
    ElMessage.error('数据异常，请刷新页面重试')
    submitting.value = false
    return
  }

  try {
    const uploadedImages = fileList.value
      .filter(item => item.status === 'done' && item.serverFileName)
      .map(item => item.serverFileName!)

    const params: FlowParams = {
      money: submitMoney.toFixed(2),
      fDate: chooseDate.value,
      actionId: selectedAction.value.id,
      accountId: selectedAccount.value.id,
      accountToId: selectedAccountTo.value?.id,
      typeId: selectedType.value.id,
      collect: isCollect.value,
      note: submitNote,
      images: uploadedImages,
    }

    if (isEdit.value && props.flowId) {
      await flowApi.update(props.flowId, params)
    } else {
      await flowApi.add(params)
    }

    ElMessage.success(isEdit.value ? '保存成功' : '添加成功')
    emit('success')
    drawerVisible.value = false
  } catch (err) {
    console.error('操作失败', err)
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

async function onDelete() {
  if (!isEdit.value || !props.flowId) return

  try {
    await ElMessageBox.confirm(
      '确定删除这条账单吗？删除后无法恢复。',
      '删除账单',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await flowApi.delete(props.flowId)
    ElMessage.success('已删除')
    emit('success')
    drawerVisible.value = false
  } catch {
    // 取消
  }
}

function onClose() {
  drawerVisible.value = false
}
</script>

<template>
  <el-drawer
    v-model="drawerVisible"
    direction="rtl"
    :size="drawerSize"
    :z-index="3000"
    :with-header="false"
    class="flow-editor-drawer"
  >
    <!-- 一级 header - 贯穿顶部 -->
    <div class="main-header">
      <span class="main-title">{{ isEdit ? '编辑账单' : '新增账单' }}</span>
      <div class="header-actions">
        <el-button v-if="!isEdit" text @click="openTemplatePanel">快记模板</el-button>
        <el-button :icon="Close" text circle @click="onClose" />
      </div>
    </div>

    <div class="editor-panels-container">
      <!-- 第一层：主编辑面板 -->
      <div class="panel editor-panel">
        <div v-loading="loading" class="panel-body">
      <!-- 金额输入区 -->
      <div class="money-section" :style="{ '--action-color': actionColor }">
        <div class="money-label">账单金额 <span class="required">*</span></div>
        <div class="money-input-wrapper">
          <span class="money-symbol">¥</span>
          <input
            :value="money"
            @input="onMoneyInput"
            @blur="onMoneyBlur"
            type="text"
            inputmode="decimal"
            class="money-input"
            placeholder="0.00"
          />
        </div>

        <!-- 收支类型切换 -->
        <div class="action-label">收支类型 <span class="required">*</span></div>
        <!-- 普通 action -->
        <div class="action-tabs">
          <div
            v-for="action in normalActions"
            :key="action.id"
            class="action-tab"
            :class="{
              active: selectedAction?.id === action.id,
              [getActionClass(action.handle)]: true
            }"
            @click="onSelectAction(action)"
          >
            {{ action.hname }}
          </div>
        </div>

        <!-- 不计入的 action（隐藏区域） -->
        <div v-if="exemptActions.length > 0" class="exempt-actions-section">
          <div class="exempt-toggle" @click="exemptActionsExpanded = !exemptActionsExpanded">
            <span class="exempt-label">不计入统计</span>
            <el-icon class="exempt-icon" :class="{ rotated: exemptActionsExpanded }">
              <ArrowDown />
            </el-icon>
          </div>
          <Transition name="collapse">
            <div v-show="exemptActionsExpanded" class="exempt-actions">
              <div
                v-for="action in exemptActions"
                :key="action.id"
                class="action-tab exempt"
                :class="{
                  active: selectedAction?.id === action.id,
                  [getActionClass(action.handle)]: true
                }"
                @click="onSelectAction(action)"
              >
                {{ action.hname }}
              </div>
            </div>
          </Transition>
        </div>
      </div>

      <!-- 基本信息 -->
      <div class="form-section">
        <!-- 账户 -->
        <div class="form-item">
          <label class="form-label">{{ isTransfer ? '转出账户' : '选择账户' }} <span class="required">*</span></label>
          <div class="form-select" :class="{ active: accountPanelVisible && accountPanelType === 1 }" @click="openAccountPanel(1)">
            <span :class="{ placeholder: !selectedAccount }">
              {{ selectedAccount?.name || '点击选择账户' }}
            </span>
            <el-icon><ArrowRight /></el-icon>
          </div>
        </div>

        <!-- 目标账户（转账时） -->
        <div v-if="isTransfer" class="form-item">
          <label class="form-label">转入账户 <span class="required">*</span></label>
          <div class="form-select" :class="{ active: accountPanelVisible && accountPanelType === 2 }" @click="openAccountPanel(2)">
            <span :class="{ placeholder: !selectedAccountTo }">
              {{ selectedAccountTo?.name || '点击选择目标账户' }}
            </span>
            <el-icon><ArrowRight /></el-icon>
          </div>
        </div>

        <!-- 分类 -->
        <div class="form-item">
          <label class="form-label">账单分类 <span class="required">*</span></label>
          <div class="form-select" :class="{ active: typePanelVisible }" @click="openTypePanel">
            <span :class="{ placeholder: !selectedType }">
              {{ selectedType?.tname || '点击选择分类' }}
            </span>
            <el-icon><ArrowRight /></el-icon>
          </div>
        </div>

        <!-- 日期 -->
        <div class="form-item">
          <label class="form-label">账单日期 <span class="required">*</span></label>
          <div class="form-select" :class="{ active: datePanelVisible }" @click="openDatePanel">
            <span :class="{ placeholder: !chooseDate }">
              {{ chooseDate || '点击选择日期' }}
            </span>
            <el-icon><ArrowRight /></el-icon>
          </div>
        </div>
      </div>

      <!-- 更多选项 -->
      <div class="form-section">
        <!-- 收藏 -->
        <div class="form-item row-item">
          <label class="form-label">收藏账单</label>
          <el-switch v-model="isCollect" />
        </div>

        <!-- 备注 -->
        <div class="form-item">
          <label class="form-label">备注</label>
          <el-input
            v-model="note"
            type="textarea"
            :rows="2"
            placeholder="添加备注..."
            maxlength="200"
            show-word-limit
          />
        </div>

        <!-- 图片上传 -->
        <div class="form-item">
          <label class="form-label">图片</label>
          <div class="upload-area">
            <div
              v-for="(file, index) in fileList"
              :key="index"
              class="upload-preview"
              :class="{ uploading: file.status === 'uploading', failed: file.status === 'failed' }"
            >
              <img :src="file.url" @click="onPreviewImage(file)" />
              <div class="delete-btn" @click.stop="onDeleteImage(index)">
                <el-icon><Delete /></el-icon>
              </div>
              <div v-if="file.status === 'uploading'" class="upload-loading">
                <el-icon class="is-loading"><Loading /></el-icon>
              </div>
            </div>
            <label v-if="fileList.length < 3" class="upload-btn">
              <el-icon><Plus /></el-icon>
              <input
                type="file"
                accept="image/*"
                multiple
                @change="onUploadImage"
              />
            </label>
          </div>
        </div>
      </div>

      <!-- 追加分账单（仅编辑模式） -->
      <template v-if="isEdit">
        <div v-if="childMoneyList.length > 0" class="form-section">
          <div class="section-title">追加分账单</div>
          <div
            v-for="child in childMoneyList"
            :key="child.index"
            class="child-money-item"
          >
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
              placeholder="备注（可选）"
            />
            <el-button
              type="danger"
              text
              :icon="Delete"
              @click="removeChildMoney(child)"
            />
          </div>
        </div>
        <div class="add-child-btn" @click="addChildMoney">
          <el-icon><Plus /></el-icon>
          <span>追加分账单</span>
        </div>
      </template>
        </div>

        <!-- 底部操作 -->
        <div class="panel-footer">
          <el-button v-if="isEdit" type="danger" plain @click="onDelete">删除</el-button>
          <el-button @click="onClose">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="onSubmit">
            {{ isEdit ? '保存' : '提交账单' }}
          </el-button>
        </div>
      </div>

      <!-- 第二层：账户选择面板 -->
      <Transition name="slide-panel">
        <div v-if="accountPanelVisible" class="panel sub-panel account-panel">
          <div class="sub-panel-header">
            <el-button text :icon="ArrowLeft" @click="accountPanelVisible = false">返回</el-button>
            <span class="sub-panel-title">{{ accountPanelType === 1 ? '选择账户' : '选择目标账户' }}</span>
          </div>
          <div class="panel-body">
            <div class="account-list">
              <div
                v-for="account in accounts"
                :key="account.id"
                class="account-item"
                :class="{
                  active: accountPanelType === 1
                    ? selectedAccount?.id === account.id
                    : selectedAccountTo?.id === account.id
                }"
                @click="onSelectAccount(account)"
              >
                <div class="account-icon" :class="{ 'has-svg': getAccountIcon(account.name) }">
                  <img v-if="getAccountIcon(account.name)" :src="getAccountIcon(account.name)!" class="account-svg" />
                  <el-icon v-else :size="24"><CreditCard /></el-icon>
                </div>
                <div class="account-info">
                  <div class="account-name">{{ account.name }}</div>
                  <div v-if="account.card" class="account-card">{{ account.card }}</div>
                </div>
                <div class="account-money">{{ formatMoneyDisplay(account.money) }}</div>
              </div>
              <el-empty v-if="accounts.length === 0" description="暂无账户" />
            </div>
          </div>
        </div>
      </Transition>

      <!-- 第二层：分类选择面板 -->
      <Transition name="slide-panel">
        <div v-if="typePanelVisible" class="panel sub-panel type-panel">
          <div class="sub-panel-header">
            <el-button text :icon="ArrowLeft" @click="typePanelVisible = false">返回</el-button>
            <span class="sub-panel-title">选择分类</span>
          </div>
          <div class="panel-body">
            <div class="type-list">
              <div v-for="parent in types" :key="parent.id" class="type-group">
                <div
                  class="type-parent"
                  :class="{ active: selectedType?.id === parent.id }"
                >
                  <div class="parent-left" @click="toggleTypeExpand(parent.id)">
                    <el-icon class="expand-icon" :class="{ rotated: isTypeExpanded(parent.id) }">
                      <ArrowRight />
                    </el-icon>
                    <span class="parent-name">{{ parent.tname }}</span>
                  </div>
                  <el-button
                    v-if="!parent.childrenTypes?.length"
                    type="primary"
                    text
                    size="small"
                    @click="onSelectType(parent)"
                  >
                    选择
                  </el-button>
                </div>
                <Transition name="expand">
                  <div v-if="isTypeExpanded(parent.id)" class="type-children">
                    <div
                      v-for="child in parent.childrenTypes"
                      :key="child.id"
                      class="type-child"
                      :class="{ active: selectedType?.id === child.id }"
                      @click="onSelectType(child, parent)"
                    >
                      <span class="child-name">{{ child.tname }}</span>
                    </div>
                    <div v-if="!parent.childrenTypes?.length" class="no-children">
                      暂无子分类，可直接选择一级分类
                    </div>
                  </div>
                </Transition>
              </div>
              <el-empty v-if="types.length === 0" description="请先选择收支类型" />
            </div>
          </div>
        </div>
      </Transition>

      <!-- 第二层：日历选择面板 -->
      <Transition name="slide-panel">
        <div v-if="datePanelVisible" class="panel sub-panel date-panel">
          <div class="sub-panel-header">
            <el-button text :icon="ArrowLeft" @click="datePanelVisible = false">返回</el-button>
            <span class="sub-panel-title">选择日期</span>
          </div>
          <div class="panel-body date-panel-body">
            <VanCalendar
              :key="datePanelKey"
              :poppable="false"
              :show-confirm="false"
              :min-date="calendarMinDate"
              :max-date="calendarMaxDate"
              :default-date="calendarDefaultDate"
              color="#1890ff"
              @select="onSelectDate"
            />
          </div>
        </div>
      </Transition>

      <!-- 第二层：快记模板面板 -->
      <Transition name="slide-panel">
        <div v-if="templatePanelVisible" class="panel sub-panel template-panel">
          <div class="sub-panel-header">
            <el-button text :icon="ArrowLeft" @click="templatePanelVisible = false">返回</el-button>
            <span class="sub-panel-title">快记模板</span>
          </div>
          <div class="panel-body">
            <!-- 标签筛选 -->
            <div class="tag-filter">
              <el-tag
                v-for="tag in tags"
                :key="tag.id"
                :effect="selectedTag?.id === tag.id ? 'dark' : 'plain'"
                :color="selectedTag?.id === tag.id ? tag.color : undefined"
                :style="selectedTag?.id === tag.id ? { borderColor: tag.color } : {}"
                class="tag-item"
                @click="onSelectTag(selectedTag?.id === tag.id ? null : tag)"
              >
                <span
                  v-if="selectedTag?.id !== tag.id"
                  class="tag-dot"
                  :style="{ background: tag.color }"
                ></span>
                {{ tag.name }}
              </el-tag>
            </div>

            <!-- 模板列表 -->
            <div class="template-list">
              <div
                v-for="template in templates"
                :key="template.id"
                class="template-item"
              >
                <div class="template-main" @click="onSelectTemplate(template)">
                  <!-- 第一行：名称 + 收支类型 + 金额 -->
                  <div class="template-row-1">
                    <div class="template-left">
                      <span class="template-name">{{ template.name }}</span>
                      <span
                        v-if="template.action"
                        class="action-tag"
                        :class="getActionClass(template.action.handle)"
                      >
                        {{ template.action.hname }}
                      </span>
                    </div>
                    <div class="template-right">
                      <span v-if="template.money" class="template-money">¥{{ template.money }}</span>
                      <span
                        v-if="template.tag"
                        class="template-tag-dot"
                        :style="{ background: template.tag.color }"
                      ></span>
                      <!-- 展开按钮 -->
                      <el-icon
                        v-if="hasTemplateDetails(template)"
                        class="template-expand-icon"
                        :class="{ rotated: expandedTemplateIds.includes(template.id) }"
                        @click.stop="toggleTemplateExpand(template.id)"
                      >
                        <ArrowDown />
                      </el-icon>
                    </div>
                  </div>
                  <!-- 第二行：日期类型 + 分类 -->
                  <div v-if="template.dateType !== undefined && template.dateType !== null || template.type" class="template-row-2">
                    <span
                      v-if="template.dateType !== undefined && template.dateType !== null"
                      class="date-type-tag"
                    >
                      {{ template.dateType === 1 ? '补上月' : '记本月' }}
                    </span>
                    <span v-if="template.type" class="type-name">{{ template.type.tname }}</span>
                  </div>
                </div>
                <!-- 展开详情 -->
                <Transition name="expand">
                  <div v-if="expandedTemplateIds.includes(template.id)" class="template-details">
                    <div v-if="template.account" class="detail-row">
                      <span class="detail-label">{{ template.accountTo ? '源账户' : '账户' }}</span>
                      <span class="detail-value">{{ template.account.name }}</span>
                    </div>
                    <div v-if="template.accountTo" class="detail-row">
                      <span class="detail-label">目标账户</span>
                      <span class="detail-value transfer">{{ template.accountTo.name }}</span>
                    </div>
                    <div v-if="template.type" class="detail-row">
                      <span class="detail-label">分类</span>
                      <span class="detail-value">{{ template.type.tname }}</span>
                    </div>
                    <div v-if="template.dateType !== undefined && template.dateType !== null" class="detail-row">
                      <span class="detail-label">日期</span>
                      <span class="detail-value">{{ template.dateType === 1 ? '补上月' : '记本月' }}</span>
                    </div>
                  </div>
                </Transition>
              </div>
              <el-empty v-if="templates.length === 0" description="暂无模板" />
            </div>
          </div>
        </div>
      </Transition>
    </div>

    <!-- 图片预览 -->
    <el-image-viewer
      v-if="previewVisible"
      :url-list="[previewUrl]"
      @close="previewVisible = false"
    />
  </el-drawer>
</template>

<style scoped>
/* 一级 header - 贯穿顶部 */
.main-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: var(--color-bg-card);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.main-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 面板容器 */
.editor-panels-container {
  display: flex;
  height: calc(100% - 57px); /* 减去一级 header 高度 */
}

/* 通用面板 */
.panel {
  display: flex;
  flex-direction: column;
  background: var(--color-bg-card);
  border-right: 1px solid var(--color-border);
  overflow: hidden;
}

.panel:last-child {
  border-right: none;
}

.editor-panel {
  width: 480px;
  min-width: 480px;
}

.account-panel {
  width: 360px;
  min-width: 360px;
}

.type-panel {
  width: 400px;
  min-width: 400px;
}

.date-panel {
  width: 340px;
  min-width: 340px;
}

.template-panel {
  width: 400px;
  min-width: 400px;
}

/* 子面板样式 */
.sub-panel {
  background: #f7f8fa;
}

.sub-panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(0, 0, 0, 0.03);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
}

.sub-panel-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.panel-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.panel-footer {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--color-border);
  background: var(--color-bg-card);
}

.panel-footer .el-button {
  flex: 1;
  height: 44px;
  border-radius: 12px;
}

.panel-footer .el-button--danger {
  flex: none;
  width: 80px;
}

/* 面板动画 */
.slide-panel-enter-active,
.slide-panel-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-panel-enter-from,
.slide-panel-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

/* 金额区域 */
.money-section {
  background: linear-gradient(135deg, var(--action-color) 0%, color-mix(in srgb, var(--action-color) 70%, #000) 100%);
  border-radius: 20px;
  padding: 24px;
  margin-bottom: 20px;
  color: #fff;
  transition: all 0.3s ease;
}

/* 不计入 action 区域 */
.exempt-actions-section {
  margin-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.15);
  padding-top: 12px;
}

.exempt-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  cursor: pointer;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.exempt-toggle:hover {
  opacity: 0.9;
}

.exempt-label {
  font-size: 12px;
}

.exempt-icon {
  font-size: 14px;
  transition: transform 0.3s;
}

.exempt-icon.rotated {
  transform: rotate(180deg);
}

.exempt-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.action-tab.exempt {
  opacity: 0.7;
}

.action-tab.exempt.active {
  opacity: 1;
}

/* 折叠动画 */
.collapse-enter-active,
.collapse-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.collapse-enter-from,
.collapse-leave-to {
  opacity: 0;
  max-height: 0;
  margin-top: 0;
}

.money-label {
  font-size: 14px;
  opacity: 0.8;
  margin-bottom: 8px;
}

.money-label .required,
.action-label .required {
  color: #ff6b6b;
  font-weight: bold;
}

.action-label {
  font-size: 13px;
  opacity: 0.8;
  margin-bottom: 10px;
}

.money-input-wrapper {
  display: flex;
  align-items: baseline;
  margin-bottom: 20px;
}

.money-symbol {
  font-size: 28px;
  font-weight: 600;
  margin-right: 4px;
}

.money-input {
  flex: 1;
  font-size: 48px;
  font-weight: 700;
  color: #fff;
  background: transparent;
  border: none;
  outline: none;
  letter-spacing: -1px;
}

.money-input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

/* 收支类型切换 */
.action-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.action-tab {
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.action-tab:hover {
  background: rgba(255, 255, 255, 0.25);
}

.action-tab.active {
  background: #fff;
  color: var(--action-color);
}

.action-tab.active.income {
  color: var(--color-income);
}

.action-tab.active.expense {
  color: var(--color-expense);
}

.action-tab.active.transfer {
  color: var(--color-transfer);
}

.exempt-dot {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.6);
}

.action-tab.active .exempt-dot {
  background: currentColor;
}

/* 表单区块 */
.form-section {
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(12px);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
  border: 1px solid var(--color-border);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 16px;
}

.form-item {
  margin-bottom: 20px;
}

.form-item:last-child {
  margin-bottom: 0;
}

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: 10px;
}

.form-label .required {
  color: var(--color-expense);
  margin-left: 2px;
}

.form-select {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid var(--color-border-light);
  font-size: 14px;
  color: var(--color-text-primary);
}

.form-select:hover {
  background: rgba(255, 255, 255, 1);
  border-color: var(--color-border);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
}

.form-select.active {
  border-color: var(--color-transfer);
  background: rgba(24, 144, 255, 0.05);
}

.form-select .placeholder {
  color: var(--color-text-tertiary);
}

/* 横排表单项 */
.form-item.row-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-item.row-item .form-label {
  margin-bottom: 0;
}

/* 日期选择器 - 全宽 */
.date-picker-full {
  width: 100%;
}

.date-picker-full :deep(.el-input__wrapper) {
  padding: 8px 16px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid var(--color-border-light);
  box-shadow: none;
}

.date-picker-full :deep(.el-input__wrapper):hover {
  background: rgba(255, 255, 255, 1);
  border-color: var(--color-border);
}

/* Textarea 样式 */
.form-item :deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid var(--color-border-light);
  border-radius: 12px;
  padding: 12px 16px;
}

.form-item :deep(.el-textarea__inner):focus {
  background: rgba(255, 255, 255, 1);
  border-color: var(--color-transfer);
}

/* 图片上传 */

.upload-area {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.upload-preview {
  width: 80px;
  height: 80px;
  border-radius: 10px;
  overflow: hidden;
  position: relative;
}

.upload-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  cursor: pointer;
}

.upload-preview .delete-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
  cursor: pointer;
  color: #fff;
  font-size: 12px;
}

.upload-preview:hover .delete-btn {
  opacity: 1;
}

.upload-preview .delete-btn:hover {
  background: var(--color-expense);
}

.upload-preview.uploading::after {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
}

.upload-loading {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  z-index: 1;
  font-size: 24px;
}

.upload-loading .is-loading {
  animation: rotating 1.5s linear infinite;
}

@keyframes rotating {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.upload-btn {
  width: 80px;
  height: 80px;
  border: 2px dashed var(--color-border);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all 0.2s;
}

.upload-btn:hover {
  border-color: var(--color-transfer);
  color: var(--color-transfer);
}

.upload-btn input {
  display: none;
}

/* 追加分账单 */
.child-money-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--color-bg-page);
  border-radius: 12px;
  margin-bottom: 12px;
}

.child-money-item:last-of-type {
  margin-bottom: 0;
}

.child-input-group {
  display: flex;
  align-items: center;
  background: var(--color-bg-card);
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  width: 120px;
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
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  outline: none;
  padding: 10px 12px;
  border-radius: 8px;
}

.child-note-input:focus {
  border-color: var(--color-transfer);
}

.child-note-input::placeholder {
  color: var(--color-text-placeholder);
}

.add-child-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 14px;
  margin: 0 0 16px 0;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-transfer);
  background: var(--color-bg-card);
  border: 1px dashed var(--color-border);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.add-child-btn:hover {
  border-color: var(--color-transfer);
  background: var(--color-transfer-bg);
}

/* 账户列表 - 参考 AccountManager */
.account-list {
  min-height: 200px;
}

.account-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
  margin-bottom: 10px;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.25s ease;
  border: 1.5px solid rgba(0, 0, 0, 0.04);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.account-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
  border-color: rgba(0, 0, 0, 0.06);
}

.account-item.active {
  border-color: var(--color-transfer);
  background: linear-gradient(135deg, rgba(24, 144, 255, 0.08) 0%, rgba(24, 144, 255, 0.04) 100%);
  box-shadow: 0 4px 16px rgba(24, 144, 255, 0.15);
}

.account-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-transfer-bg);
  color: var(--color-transfer);
  border-radius: 12px;
  flex-shrink: 0;
}

.account-icon.has-svg {
  background: transparent;
}

.account-svg {
  width: 40px;
  height: 40px;
}

.account-info {
  flex: 1;
  min-width: 0;
}

.account-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.account-card {
  margin-top: 4px;
  font-size: 13px;
  color: var(--color-text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.account-money {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

/* 分类列表 - 参考 TypeManager */
.type-list {
  min-height: 200px;
}

.type-group {
  margin-bottom: 10px;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border-radius: 14px;
  border: 1.5px solid rgba(0, 0, 0, 0.04);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.type-parent {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.type-parent:hover {
  background: rgba(0, 0, 0, 0.02);
}

.type-parent.active {
  background: linear-gradient(135deg, rgba(24, 144, 255, 0.08) 0%, rgba(24, 144, 255, 0.04) 100%);
}

.parent-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.expand-icon {
  font-size: 12px;
  color: var(--color-text-tertiary);
  transition: transform 0.2s;
}

.expand-icon.rotated {
  transform: rotate(90deg);
}

.parent-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

/* 二级分类 */
.type-children {
  border-top: 1px solid var(--color-border-light);
  padding: 12px 16px 16px;
  background: rgba(0, 0, 0, 0.02);
}

.type-child {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  margin-top: 8px;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-light);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.type-child:first-child {
  margin-top: 0;
}

.type-child:hover {
  background: #fff;
  border-color: var(--color-border);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.type-child.active {
  background: linear-gradient(135deg, rgba(24, 144, 255, 0.08) 0%, rgba(24, 144, 255, 0.04) 100%);
  border: 1.5px solid var(--color-transfer);
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.15);
}

.child-name {
  font-size: 14px;
  color: var(--color-text-primary);
}

.no-children {
  padding: 16px;
  text-align: center;
  font-size: 13px;
  color: var(--color-text-tertiary);
}

/* 展开动画 */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}

/* Vant 日历样式 */
.date-panel-body {
  padding: 0;
  display: flex;
  flex-direction: column;
}

.date-panel-body :deep(.van-calendar) {
  height: 100%;
  background: transparent;
}

.date-panel-body :deep(.van-calendar__header) {
  box-shadow: none;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.date-panel-body :deep(.van-calendar__month-title) {
  font-weight: 600;
  color: var(--color-text-primary);
}

.date-panel-body :deep(.van-calendar__day) {
  font-weight: 500;
}

.date-panel-body :deep(.van-calendar__selected-day) {
  border-radius: 8px;
}

/* 标签筛选 */
.tag-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-border);
}

.tag-item {
  cursor: pointer;
}

.tag-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
}

/* 模板列表 - 卡片风格 */
.template-list {
  min-height: 200px;
}

.template-item {
  margin-bottom: 10px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 14px;
  transition: all 0.25s ease;
  border: 1.5px solid rgba(0, 0, 0, 0.04);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.template-item:hover {
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
  border-color: rgba(0, 0, 0, 0.06);
}

.template-main {
  padding: 16px 18px;
  cursor: pointer;
  transition: background 0.2s;
}

.template-main:hover {
  background: rgba(0, 0, 0, 0.02);
}

/* 第一行：名称 + 收支类型 + 金额 */
.template-row-1 {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.template-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.template-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 第二行：日期类型 + 分类 */
.template-row-2 {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
}

.action-tag {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 6px;
  font-weight: 500;
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

.type-name {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.date-type-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--color-transfer-bg);
  color: var(--color-transfer);
  font-weight: 500;
}

.template-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.template-money {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.template-tag-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.template-expand-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all 0.2s;
}

.template-expand-icon:hover {
  background: rgba(0, 0, 0, 0.06);
  color: var(--color-text-secondary);
}

.template-expand-icon.rotated {
  transform: rotate(180deg);
}

/* 模板详情展开区域 */
.template-details {
  padding: 12px 18px 16px;
  border-top: 1px dashed var(--color-border-light);
  background: rgba(0, 0, 0, 0.02);
}

.template-details .detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--color-border-light);
}

.template-details .detail-row:last-child {
  border-bottom: none;
}

.template-details .detail-label {
  font-size: 13px;
  color: var(--color-text-tertiary);
}

.template-details .detail-value {
  font-size: 13px;
  color: var(--color-text-primary);
}

.template-details .detail-value.transfer {
  color: var(--color-transfer);
}
</style>

<!-- 全局样式 -->
<style>
.flow-editor-drawer .el-drawer__body {
  padding: 0;
  overflow: hidden;
}

/* 暗色模式 */
html.dark .money-section {
  background: linear-gradient(135deg, var(--action-color) 0%, color-mix(in srgb, var(--action-color) 50%, #000) 100%);
}

html.dark .form-section {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.08);
}

html.dark .form-select {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .form-select:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.15);
}

html.dark .date-picker-full :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .form-item :deep(.el-textarea__inner),
html.dark .form-item :deep(.el-textarea .el-textarea__inner) {
  background-color: rgba(255, 255, 255, 0.05) !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
  color: #e5e5e5 !important;
  box-shadow: none !important;
}

html.dark .form-item :deep(.el-textarea__inner)::placeholder {
  color: rgba(255, 255, 255, 0.4) !important;
}

html.dark .form-item :deep(.el-textarea__inner):focus {
  background-color: rgba(255, 255, 255, 0.08) !important;
  border-color: var(--color-transfer) !important;
}

html.dark .form-item :deep(.el-input__count) {
  background: transparent !important;
  color: rgba(255, 255, 255, 0.4) !important;
}

html.dark .panel-footer {
  background: var(--color-bg-card);
}

html.dark .picker-item:hover,
html.dark .template-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

html.dark .type-parent {
  background: rgba(255, 255, 255, 0.05);
}

html.dark .type-child {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .child-money-item {
  background: rgba(255, 255, 255, 0.05);
}

html.dark .child-input-group {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .child-note-input {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .add-child-btn {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .add-child-btn:hover {
  background: rgba(24, 144, 255, 0.1);
}

/* 暗色模式 - 子面板 */
html.dark .sub-panel {
  background: #1f1f1f;
}

html.dark .sub-panel-header {
  background: rgba(255, 255, 255, 0.03);
  border-bottom-color: rgba(255, 255, 255, 0.06);
}

html.dark .account-item,
html.dark .template-item {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.06);
}

html.dark .account-item:hover,
html.dark .template-item:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .type-group {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.06);
}

html.dark .type-children {
  background: rgba(0, 0, 0, 0.2);
}

html.dark .type-child {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.06);
}

html.dark .template-main:hover {
  background: rgba(255, 255, 255, 0.04);
}

html.dark .template-expand-icon:hover {
  background: rgba(255, 255, 255, 0.1);
}

html.dark .template-details {
  background: rgba(0, 0, 0, 0.2);
  border-top-color: rgba(255, 255, 255, 0.08);
}

html.dark .template-details .detail-row {
  border-bottom-color: rgba(255, 255, 255, 0.06);
}
</style>
