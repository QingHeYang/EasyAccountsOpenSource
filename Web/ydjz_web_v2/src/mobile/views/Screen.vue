<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast, showLoadingToast, closeToast, showConfirmDialog } from 'vant'
import { screenApi, type ScreenFlowParams } from '@shared/api/screen'
import { actionApi, type Action } from '@shared/api/action'
import { accountApi, type Account } from '@shared/api/account'
import { typeApi, type TypeWithChildren } from '@shared/api/type'
import { flowApi, type Flow } from '@shared/api/flow'
import { useSmartBack } from '@shared/composables/useSmartBack'
import { consumeScreenParams, type ScreenParams } from '@shared/services/screenParams'
import { useScreenFilterStore } from '@mobile/stores/screenFilter'
import FlowItem from '@mobile/components/FlowItem.vue'

const router = useRouter()
const route = useRoute()
const { smartBack } = useSmartBack()
const filterStore = useScreenFilterStore()

// 滚动定位相关
const lastClickedFlowId = ref<number | null>(null)

// ==================== 筛选条件 ====================
const searchNote = ref('')
const fastChoose = ref<number>(0) // 0当月 1上月 2全年 3上年
const startDate = ref('')
const endDate = ref('')
const singleMonth = ref(true)
const accountId = ref<number>(-1)
const accountName = ref('全部账户')
const handleType = ref<number>(3) // 0流入 1流出 2转账 3全部
const collectOnly = ref(false)
const chooseActions = ref<number[]>([])
const chooseTypes = ref<number[]>([])

// ==================== 数据 ====================
const flows = ref<Flow[]>([])
const totalIn = ref('0')
const totalOut = ref('0')
const totalEarn = ref('0')
const typeMoneyList = ref<any[]>([])

const allActions = ref<Action[]>([])
const allAccounts = ref<Account[]>([])
const allTypes = ref<any[]>([])

// ==================== 弹窗状态 ====================
const showFilterPopup = ref(false)
const showDatePicker = ref(false)
const showTypeMoney = ref(false)
const showFullTypeMoney = ref(false) // 分类明细是否显示完整金额
const showExcelDialog = ref(false)
const isStartDate = ref(true)
const excelName = ref('')

// 日期选择器
const minDate = new Date(2021, 0, 1)
const maxDate = new Date()
const currentDate = ref<string[]>([])

// 分类选择
const activeParentType = ref<number | null>(null)

// ==================== 计算属性 ====================
const fastOptions = [
  { label: '当月', value: 0 },
  { label: '上月', value: 1 },
  { label: '全年', value: 2 },
  { label: '上年', value: 3 },
]

const handleOptions = [
  { label: '全部', value: 3 },
  { label: '收入', value: 0 },
  { label: '支出', value: 1 },
  { label: '转账', value: 2 },
]

// 当前筛选条件数量
const filterCount = computed(() => {
  let count = 0
  if (accountId.value !== -1) count++
  if (handleType.value !== 3) count++
  if (collectOnly.value) count++
  if (chooseActions.value.length > 0) count++
  if (chooseTypes.value.length > 0) count++
  return count
})

// 按日期分组的流水
const groupedFlows = computed(() => {
  const groups: { date: string; flows: Flow[] }[] = []
  let currentDate = ''

  flows.value.forEach(flow => {
    if (flow.fdate !== currentDate) {
      currentDate = flow.fdate
      groups.push({ date: currentDate, flows: [] })
    }
    groups[groups.length - 1].flows.push(flow)
  })

  return groups
})

// 当前选中的一级分类
const currentParentType = computed(() => {
  if (!activeParentType.value) return null
  return allTypes.value.find(t => t.id === activeParentType.value) || null
})

// ==================== 方法 ====================
function formatDate(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

// 格式化金额（超过1万显示为x.xx万）
function formatAmount(amount: string | number | undefined): string {
  if (!amount) return '0.00'
  const num = typeof amount === 'string' ? parseFloat(amount) : amount
  if (Math.abs(num) >= 10000) {
    return (num / 10000).toFixed(2) + '万'
  }
  return num.toFixed(2)
}

// 点击显示原金额
function showFullAmount(label: string, amount: string | number | undefined) {
  const num = amount ? (typeof amount === 'string' ? parseFloat(amount) : amount) : 0
  showToast({ message: `${label}: ¥${num.toFixed(2)}`, position: 'top' })
}

function onFastChoose(value: number) {
  fastChoose.value = value
  const now = new Date()

  switch (value) {
    case 0: // 当月
      startDate.value = formatDate(new Date(now.getFullYear(), now.getMonth(), 1))
      endDate.value = ''
      singleMonth.value = true
      break
    case 1: // 上月
      startDate.value = formatDate(new Date(now.getFullYear(), now.getMonth() - 1, 1))
      endDate.value = ''
      singleMonth.value = true
      break
    case 2: // 全年
      startDate.value = formatDate(new Date(now.getFullYear(), 0, 1))
      endDate.value = formatDate(now)
      singleMonth.value = false
      break
    case 3: // 上年
      startDate.value = formatDate(new Date(now.getFullYear() - 1, 0, 1))
      endDate.value = formatDate(new Date(now.getFullYear() - 1, 11, 31))
      singleMonth.value = false
      break
  }

  fetchFlows()
}

async function fetchFlows() {
  showLoadingToast({ message: '加载中...', forbidClick: true, duration: 0 })

  try {
    const params: ScreenFlowParams = {
      startDate: startDate.value,
      endDate: endDate.value || undefined,
      singleMonth: singleMonth.value,
      accountId: accountId.value === -1 ? undefined : accountId.value,
      chooseHandle: handleType.value,
      collect: collectOnly.value || undefined,
      actions: chooseActions.value.length > 0 ? chooseActions.value : undefined,
      types: chooseTypes.value.length > 0 ? chooseTypes.value : undefined,
      note: searchNote.value || undefined,
    }

    const res = await screenApi.getFlowByScreen(params)
    const data = res.data.data

    flows.value = data.flows || []
    totalIn.value = data.totalIn || '0'
    totalOut.value = data.totalOut || '0'
    totalEarn.value = data.totalEarn || '0'
    typeMoneyList.value = data.typeList || []

    closeToast()
  } catch (err) {
    closeToast()
    showToast('加载失败')
    console.error(err)
  }
}

async function fetchActions() {
  try {
    const res = await actionApi.getAll()
    allActions.value = res.data.data || []
  } catch (err) {
    console.error(err)
  }
}

async function fetchAccounts() {
  try {
    const res = await accountApi.getAll()
    allAccounts.value = [{ id: -1, name: '全部账户', money: '0' } as Account, ...(res.data.data || [])]
  } catch (err) {
    console.error(err)
  }
}

async function fetchTypes() {
  try {
    const res = await typeApi.getAllNoLimit()
    allTypes.value = res.data.data || []
  } catch (err) {
    console.error(err)
  }
}

function onSearch() {
  fetchFlows()
}

function openDatePicker(isStart: boolean) {
  isStartDate.value = isStart
  const dateStr = isStart ? startDate.value : endDate.value
  if (dateStr) {
    currentDate.value = dateStr.split('-')
  } else {
    const now = new Date()
    currentDate.value = [String(now.getFullYear()), String(now.getMonth() + 1), String(now.getDate())]
  }
  showDatePicker.value = true
}

function onDateConfirm({ selectedValues }: { selectedValues: string[] }) {
  const dateStr = `${selectedValues[0]}-${selectedValues[1].padStart(2, '0')}-${selectedValues[2].padStart(2, '0')}`
  if (isStartDate.value) {
    startDate.value = dateStr
  } else {
    endDate.value = dateStr
  }
  showDatePicker.value = false
  fastChoose.value = -1
}

function toggleAction(actionId: number) {
  const idx = chooseActions.value.indexOf(actionId)
  if (idx > -1) {
    chooseActions.value.splice(idx, 1)
  } else {
    chooseActions.value.push(actionId)
  }
}

// 根据 handle 获取样式类
function getHandleClass(handle: number | undefined): string {
  if (handle === 0) return 'income'
  if (handle === 1) return 'expense'
  if (handle === 2) return 'transfer'
  return ''
}

function toggleType(typeId: number) {
  const idx = chooseTypes.value.indexOf(typeId)
  if (idx > -1) {
    chooseTypes.value.splice(idx, 1)
  } else {
    chooseTypes.value.push(typeId)
  }
}

// 获取某个大类下已选中的数量
function getTypeSelectedCount(type: any): number {
  let count = 0
  if (chooseTypes.value.includes(type.id)) count++
  if (type.childrenTypes) {
    type.childrenTypes.forEach((child: any) => {
      if (chooseTypes.value.includes(child.id)) count++
    })
  }
  return count
}

function applyFilter() {
  showFilterPopup.value = false
  fetchFlows()
}

function resetFilter() {
  accountId.value = -1
  accountName.value = '全部账户'
  handleType.value = 3
  collectOnly.value = false
  chooseActions.value = []
  chooseTypes.value = []
  activeParentType.value = null
  fastChoose.value = 0
  onFastChoose(0)
}

function onFlowClick(flow: Flow) {
  // 记录点击的 flow ID，用于返回时滚动定位
  lastClickedFlowId.value = flow.id
  router.push(`/flow/edit/${flow.id}`)
}

async function onFlowCollect(flow: Flow) {
  try {
    await flowApi.toggleCollect(flow.id, !flow.collect)
    flow.collect = !flow.collect
    showToast(flow.collect ? '已收藏' : '已取消收藏')
  } catch (err) {
    showToast('操作失败')
  }
}

async function onFlowDelete(flow: Flow) {
  try {
    await showConfirmDialog({ message: '确定删除该账单吗？' })
    await flowApi.delete(flow.id)
    flows.value = flows.value.filter(f => f.id !== flow.id)
    showToast('删除成功')
    // 重新获取统计数据
    fetchFlows()
  } catch (err) {
    // 取消或失败
  }
}

function onBack() {
  // 智能返回：优先返回上一页，否则返回明细页
  smartBack('/flow')
}

// 滚动到指定 flow 并高亮
async function scrollToFlowAndHighlight(flowId: number) {
  await nextTick()
  const el = document.querySelector(`[data-flow-id="${flowId}"]`) as HTMLElement
  if (el) {
    // 滚动到元素
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })

    // 等滚动完成后再添加高亮动画
    // 使用 scrollend 事件（现代浏览器）或 fallback 延迟
    const addHighlight = () => {
      el.classList.add('highlight')
      el.addEventListener('animationend', () => {
        el.classList.remove('highlight')
      }, { once: true })
    }

    if ('onscrollend' in window) {
      // 现代浏览器支持 scrollend 事件
      window.addEventListener('scrollend', addHighlight, { once: true })
    } else {
      // fallback: 延迟 400ms 等待滚动完成
      setTimeout(addHighlight, 400)
    }
  }
}

// 生成 Excel
async function onMakeExcel() {
  if (!excelName.value.trim()) {
    showToast('请输入Excel标题')
    return
  }

  showLoadingToast({ message: '生成中...', forbidClick: true, duration: 0 })

  try {
    const params: ScreenFlowParams = {
      startDate: startDate.value,
      endDate: endDate.value || undefined,
      singleMonth: singleMonth.value,
      accountId: accountId.value === -1 ? undefined : accountId.value,
      chooseHandle: handleType.value,
      collect: collectOnly.value || undefined,
      actions: chooseActions.value.length > 0 ? chooseActions.value : undefined,
      types: chooseTypes.value.length > 0 ? chooseTypes.value : undefined,
    }

    const res = await screenApi.makeExcel(excelName.value, params)
    closeToast()
    showExcelDialog.value = false
    excelName.value = ''

    const result = res.data.data
    await showConfirmDialog({
      title: result.success ? '生成成功' : '生成失败',
      message: result.log,
      showCancelButton: false,
    })
  } catch (err) {
    closeToast()
    showToast('生成失败')
    console.error(err)
  }
}

// 应用 AI 传递的筛选参数
function applyExternalParams(params: ScreenParams) {
  // 先重置所有筛选条件
  startDate.value = ''
  endDate.value = ''
  singleMonth.value = false  // 默认不限月份
  accountId.value = -1
  accountName.value = '全部账户'
  handleType.value = 3
  collectOnly.value = false
  chooseActions.value = []
  chooseTypes.value = []
  searchNote.value = ''
  fastChoose.value = -1

  // 应用新参数
  if (params.startDate) startDate.value = params.startDate
  if (params.endDate) endDate.value = params.endDate
  if (params.singleMonth !== undefined) singleMonth.value = params.singleMonth
  if (params.accountId !== undefined && params.accountId !== -1) accountId.value = params.accountId
  if (params.chooseHandle !== undefined) handleType.value = params.chooseHandle
  if (params.collect) collectOnly.value = params.collect === true || params.collect === 'true'
  if (params.actions?.length) chooseActions.value = [...params.actions]
  if (params.types?.length) chooseTypes.value = [...params.types]
  if (params.note) searchNote.value = params.note
}

// ==================== 生命周期 ====================
onMounted(async () => {
  // 判断来源：sessionStorage 标记表示新进入页面
  const isNewEntry = sessionStorage.getItem('screenFrom') === 'new'
  sessionStorage.removeItem('screenFrom')

  // 检查是否有 AI 传递的参数
  const externalParams = consumeScreenParams()

  // 加载基础数据
  fetchActions()
  fetchAccounts()
  fetchTypes()

  if (externalParams) {
    // AI 传递的参数优先级最高
    filterStore.reset()
    applyExternalParams(externalParams)
    await fetchFlows()
  } else if (isNewEntry || !filterStore.initialized) {
    // 新进入页面或未初始化，使用默认值或路由参数
    filterStore.reset()
    const now = new Date()
    startDate.value = formatDate(new Date(now.getFullYear(), now.getMonth(), 1))

    // 检查路由参数
    if (route.query.acid) {
      accountId.value = Number(route.query.acid)
    }
    await fetchFlows()
  } else {
    // 从 FlowAdd 返回，恢复 store 状态
    searchNote.value = filterStore.searchNote
    fastChoose.value = filterStore.fastChoose
    startDate.value = filterStore.startDate
    endDate.value = filterStore.endDate
    singleMonth.value = filterStore.singleMonth
    accountId.value = filterStore.accountId
    accountName.value = filterStore.accountName
    handleType.value = filterStore.handleType
    collectOnly.value = filterStore.collectOnly
    chooseActions.value = [...filterStore.chooseActions]
    chooseTypes.value = [...filterStore.chooseTypes]
    lastClickedFlowId.value = filterStore.lastClickedFlowId

    // 重新请求数据（可能有修改）
    await fetchFlows()

    // 滚动到之前点击的 flow 并高亮
    if (lastClickedFlowId.value) {
      scrollToFlowAndHighlight(lastClickedFlowId.value)
    }
  }
})

// 离开页面前保存状态
onBeforeUnmount(() => {
  filterStore.save({
    searchNote: searchNote.value,
    fastChoose: fastChoose.value,
    startDate: startDate.value,
    endDate: endDate.value,
    singleMonth: singleMonth.value,
    accountId: accountId.value,
    accountName: accountName.value,
    handleType: handleType.value,
    collectOnly: collectOnly.value,
    chooseActions: chooseActions.value,
    chooseTypes: chooseTypes.value,
    lastClickedFlowId: lastClickedFlowId.value,
  })
})
</script>

<template>
  <div class="screen-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="header-left" @click="onBack">
        <van-icon name="arrow-left" size="20" />
      </div>
      <div class="header-title">筛选</div>
      <div class="header-right" @click="showFilterPopup = true">
        <van-icon name="filter-o" size="20" />
        <span v-if="filterCount > 0" class="filter-badge">{{ filterCount }}</span>
      </div>
    </div>

    <!-- 搜索栏 -->
    <div class="search-section">
      <van-search
        v-model="searchNote"
        shape="round"
        placeholder="搜索备注关键词"
        @search="onSearch"
      />
    </div>

    <!-- 快速筛选 -->
    <div class="quick-filter">
      <div
        v-for="opt in fastOptions"
        :key="opt.value"
        class="quick-item"
        :class="{ active: fastChoose === opt.value }"
        @click="onFastChoose(opt.value)"
      >
        {{ opt.label }}
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-card">
      <div class="stats-row">
        <div class="stats-item" @click="showFullAmount('收入', totalIn)">
          <span class="stats-label">收入</span>
          <span class="stats-value income">¥{{ formatAmount(totalIn) }}</span>
        </div>
        <div class="stats-divider"></div>
        <div class="stats-item" @click="showFullAmount('支出', totalOut)">
          <span class="stats-label">支出</span>
          <span class="stats-value expense">¥{{ formatAmount(totalOut) }}</span>
        </div>
        <div class="stats-divider"></div>
        <div class="stats-item" @click="showFullAmount('结余', totalEarn)">
          <span class="stats-label">结余</span>
          <span class="stats-value">¥{{ formatAmount(totalEarn) }}</span>
        </div>
      </div>
      <div class="stats-action" @click="showTypeMoney = true">
        <span>查看分类明细</span>
        <van-icon name="arrow" size="14" />
      </div>
    </div>

    <!-- 流水列表 -->
    <div class="flow-list">
      <template v-if="groupedFlows.length > 0">
        <div v-for="group in groupedFlows" :key="group.date" class="flow-group">
          <div class="group-header">
            <span class="group-date">{{ group.date }}</span>
            <span class="group-count">{{ group.flows.length }}笔</span>
          </div>
          <div class="group-items">
            <FlowItem
              v-for="flow in group.flows"
              :key="flow.id"
              :flow="flow"
              show-remark
              @click="onFlowClick"
              @collect="onFlowCollect"
              @delete="onFlowDelete"
            />
          </div>
        </div>
      </template>
      <van-empty v-else description="暂无账单" />
    </div>

    <!-- 返回顶部 -->
    <van-back-top right="16" bottom="80" />

    <!-- 筛选弹窗 -->
    <van-popup
      v-model:show="showFilterPopup"
      position="right"
      teleport="body"
      :style="{ width: '85%', height: '100%' }"
    >
      <div class="filter-popup">
        <div class="filter-header">
          <span class="filter-title">筛选条件</span>
          <span class="filter-reset" @click="resetFilter">重置</span>
        </div>

        <!-- 可滚动内容区 -->
        <div class="filter-body">
          <!-- 账户（单选） -->
        <div class="filter-section">
          <div class="section-title">账户</div>
          <div class="section-content">
            <div class="account-tags">
              <div
                v-for="account in allAccounts"
                :key="account.id"
                class="account-tag"
                :class="{ active: accountId === account.id }"
                @click="accountId = account.id; accountName = account.name"
              >
                {{ account.name }}
              </div>
            </div>
          </div>
        </div>

        <!-- 时间 -->
        <div class="filter-section">
          <div class="section-title">时间范围</div>
          <div class="section-content">
            <div class="date-row">
              <div class="date-btn" @click="openDatePicker(true)">
                {{ startDate || '开始日期' }}
              </div>
              <span class="date-sep">至</span>
              <div class="date-btn" @click="openDatePicker(false)">
                {{ endDate || '结束日期' }}
              </div>
            </div>
            <div class="switch-row">
              <span>整月模式</span>
              <van-switch v-model="singleMonth" size="20" />
            </div>
            <div class="switch-row">
              <span>只看收藏</span>
              <van-switch v-model="collectOnly" size="20" />
            </div>
          </div>
        </div>

        <!-- 资金流向 -->
        <div class="filter-section">
          <div class="section-title">资金流向</div>
          <div class="section-content">
            <div class="handle-options">
              <div
                v-for="opt in handleOptions"
                :key="opt.value"
                class="handle-item"
                :class="[
                  getHandleClass(opt.value),
                  { active: handleType === opt.value }
                ]"
                @click="handleType = opt.value"
              >
                {{ opt.label }}
              </div>
            </div>
          </div>
        </div>

        <!-- 收支类型 -->
        <div class="filter-section">
          <div class="section-title">收支类型</div>
          <div class="section-content">
            <div class="action-options">
              <div
                v-for="action in allActions"
                :key="action.id"
                class="action-item"
                :class="[
                  getHandleClass(action.handle),
                  { active: chooseActions.includes(action.id) }
                ]"
                @click="toggleAction(action.id)"
              >
                {{ action.hname }}
              </div>
            </div>
          </div>
        </div>

        <!-- 分类选择 - 两栏布局 -->
        <div class="filter-section type-section">
          <div class="section-title">
            <span>分类</span>
            <span v-if="chooseTypes.length > 0" class="selected-count">已选 {{ chooseTypes.length }}</span>
          </div>
          <div class="type-picker">
            <!-- 左侧：一级分类 -->
            <div class="type-left">
              <div
                v-for="type in allTypes"
                :key="type.id"
                class="type-parent-item"
                :class="{ active: activeParentType === type.id }"
                @click="activeParentType = type.id"
              >
                <span class="parent-name">{{ type.tname }}</span>
                <span
                  v-if="getTypeSelectedCount(type) > 0"
                  class="parent-badge"
                >{{ getTypeSelectedCount(type) }}</span>
              </div>
            </div>
            <!-- 右侧：二级分类 -->
            <div class="type-right">
              <template v-if="currentParentType">
                <div
                  class="type-tag"
                  :class="{ active: chooseTypes.includes(currentParentType.id) }"
                  @click="toggleType(currentParentType.id)"
                >
                  全部
                </div>
                <div
                  v-for="child in currentParentType.childrenTypes"
                  :key="child.id"
                  class="type-tag"
                  :class="{ active: chooseTypes.includes(child.id) }"
                  @click="toggleType(child.id)"
                >
                  {{ child.tname }}
                </div>
              </template>
              <div v-else class="type-empty">请选择分类</div>
            </div>
          </div>
        </div>
        </div>

        <!-- 底部按钮（固定） -->
        <div class="filter-footer">
          <button class="excel-btn" @click="showExcelDialog = true">
            <van-icon name="down" size="16" />
            生成Excel
          </button>
          <button class="apply-btn" @click="applyFilter">应用筛选</button>
        </div>
      </div>
    </van-popup>

    <!-- 日期选择器 -->
    <van-popup v-model:show="showDatePicker" position="bottom" round teleport="body">
      <van-date-picker
        v-model="currentDate"
        :title="isStartDate ? '选择开始日期' : '选择结束日期'"
        :min-date="minDate"
        :max-date="maxDate"
        @confirm="onDateConfirm"
        @cancel="showDatePicker = false"
      />
    </van-popup>

    <!-- 分类明细弹窗 -->
    <van-action-sheet
      v-model:show="showTypeMoney"
      title="分类收支明细"
      teleport="body"
      class="type-money-sheet"
    >
      <span
        class="toggle-full-btn"
        @click="showFullTypeMoney = !showFullTypeMoney"
      >{{ showFullTypeMoney ? '缩略' : '完整' }}</span>
      <div class="type-money-list">
        <template v-if="typeMoneyList.length > 0">
          <div v-for="type in typeMoneyList" :key="type.typeId" class="type-money-item">
            <div class="type-money-header">
              <span class="type-name">{{ type.typeName }}</span>
              <span class="type-total">¥{{ showFullTypeMoney ? type.money : formatAmount(type.money) }}</span>
            </div>
            <div v-if="type.children?.length" class="type-children">
              <div v-for="child in type.children" :key="child.typeId" class="child-item">
                <span class="child-name">{{ child.typeName }}</span>
                <span class="child-money">¥{{ showFullTypeMoney ? child.money : formatAmount(child.money) }}</span>
              </div>
            </div>
          </div>
        </template>
        <van-empty v-else description="暂无分类数据" />
      </div>
    </van-action-sheet>

    <!-- Excel 对话框 -->
    <van-dialog
      v-model:show="showExcelDialog"
      title="生成Excel"
      show-cancel-button
      @confirm="onMakeExcel"
    >
      <div class="excel-dialog-content">
        <van-field
          v-model="excelName"
          label="标题"
          placeholder="请输入Excel标题"
          :border="false"
        />
      </div>
    </van-dialog>
  </div>
</template>

<style scoped>
.screen-page {
  min-height: 100vh;
  background: var(--color-bg-page);
  padding-bottom: 20px;
}

/* 顶部导航 */
.page-header {
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--color-bg-page);
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
  position: relative;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.filter-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 16px;
  height: 16px;
  background: var(--color-expense);
  color: #fff;
  font-size: 10px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 搜索栏 */
.search-section {
  padding: 0 16px;
}

.search-section :deep(.van-search) {
  padding: 0;
  background: transparent;
}

.search-section :deep(.van-search__content) {
  background: var(--color-bg-card);
}

/* 快速筛选 */
.quick-filter {
  display: flex;
  gap: 10px;
  padding: 12px 16px;
  overflow-x: auto;
}

.quick-item {
  padding: 8px 16px;
  background: var(--color-bg-card);
  border-radius: 20px;
  font-size: 13px;
  color: var(--color-text-secondary);
  white-space: nowrap;
  flex-shrink: 0;
}

.quick-item.active {
  background: var(--color-transfer);
  color: #fff;
}

/* 统计卡片 */
.stats-card {
  margin: 0 16px 16px;
  padding: 20px;
  background: var(--color-bg-card);
  border-radius: 16px;
}

.stats-row {
  display: flex;
  align-items: center;
}

.stats-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.stats-label {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.stats-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.stats-value.income {
  color: var(--color-income);
}

.stats-value.expense {
  color: var(--color-expense);
}

.stats-divider {
  width: 1px;
  height: 30px;
  background: var(--color-border-light);
}

.stats-action {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border-light);
  font-size: 13px;
  color: var(--color-transfer);
}

/* 流水列表 */
.flow-list {
  padding: 0 16px;
}

.flow-group {
  margin-bottom: 16px;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 4px;
}

.group-date {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.group-count {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.group-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 筛选弹窗 */
.filter-popup {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-page);
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: var(--color-bg-card);
  flex-shrink: 0;
}

.filter-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.filter-reset {
  font-size: 14px;
  color: var(--color-transfer);
}

.filter-body {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 16px;
}

.filter-section {
  margin-top: 12px;
  background: var(--color-bg-card);
  padding: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 12px;
}

.section-content {
  /* content */
}

.date-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.date-btn {
  flex: 1;
  padding: 10px 12px;
  background: var(--color-bg-page);
  border-radius: 8px;
  font-size: 14px;
  color: var(--color-text-primary);
  text-align: center;
}

.date-sep {
  font-size: 14px;
  color: var(--color-text-tertiary);
}

.switch-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  font-size: 14px;
  color: var(--color-text-primary);
}

/* 账户标签 */
.account-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  max-height: 120px;
  overflow-y: auto;
}

.account-tag {
  padding: 6px 12px;
  background: var(--color-bg-page);
  border-radius: 6px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.account-tag.active {
  background: var(--color-transfer);
  color: #fff;
}

.handle-options,
.action-options {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.handle-item,
.action-item {
  padding: 8px 16px;
  background: var(--color-bg-page);
  border-radius: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
  border: 1px solid transparent;
}

/* 默认选中 - 灰色（放在前面，优先级低） */
.handle-item.active,
.action-item.active {
  background: var(--color-text-secondary);
  color: #fff;
}

/* 收入 - 绿色 */
.handle-item.income,
.action-item.income {
  color: var(--color-income);
  border-color: var(--color-income-bg);
  background: var(--color-income-bg);
}

.handle-item.income.active,
.action-item.income.active {
  background: var(--color-income);
  color: #fff;
  border-color: var(--color-income);
}

/* 支出 - 红色 */
.handle-item.expense,
.action-item.expense {
  color: var(--color-expense);
  border-color: var(--color-expense-bg);
  background: var(--color-expense-bg);
}

.handle-item.expense.active,
.action-item.expense.active {
  background: var(--color-expense);
  color: #fff;
  border-color: var(--color-expense);
}

/* 转账 - 蓝色 */
.handle-item.transfer,
.action-item.transfer {
  color: var(--color-transfer);
  border-color: var(--color-transfer-bg);
  background: var(--color-transfer-bg);
}

.handle-item.transfer.active,
.action-item.transfer.active {
  background: var(--color-transfer);
  color: #fff;
  border-color: var(--color-transfer);
}

/* 分类选择 - 两栏布局 */
.section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.selected-count {
  font-size: 12px;
  color: var(--color-transfer);
  font-weight: 400;
}

.type-section {
  padding-bottom: 0;
}

.type-picker {
  display: flex;
  height: 200px;
  border-radius: 10px;
  overflow: hidden;
  background: var(--color-bg-page);
}

.type-left {
  width: 100px;
  flex-shrink: 0;
  overflow-y: auto;
  background: var(--color-bg-page);
}

.type-parent-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 10px;
  font-size: 13px;
  color: var(--color-text-secondary);
  border-left: 3px solid transparent;
}

.type-parent-item.active {
  background: var(--color-bg-card);
  color: var(--color-text-primary);
  border-left-color: var(--color-transfer);
  font-weight: 500;
}

.parent-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.parent-badge {
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  background: var(--color-transfer);
  color: #fff;
  font-size: 10px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.type-right {
  flex: 1;
  padding: 12px;
  overflow-y: auto;
  background: var(--color-bg-card);
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-content: flex-start;
}

.type-tag {
  padding: 6px 12px;
  background: var(--color-bg-page);
  border-radius: 6px;
  font-size: 13px;
  color: var(--color-text-secondary);
  height: fit-content;
}

.type-tag.active {
  background: var(--color-transfer);
  color: #fff;
}

.type-empty {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
  font-size: 13px;
}

.filter-footer {
  padding: 16px 20px;
  background: var(--color-bg-card);
  flex-shrink: 0;
  display: flex;
  gap: 12px;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05);
}

.excel-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 14px 16px;
  background: var(--color-bg-page);
  color: var(--color-text-primary);
  border: none;
  border-radius: 12px;
  font-size: 14px;
  white-space: nowrap;
}

.apply-btn {
  flex: 1;
  padding: 14px;
  background: var(--color-transfer);
  color: #fff;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 500;
}

.excel-dialog-content {
  padding: 16px;
}

.excel-dialog-content :deep(.van-field) {
  background: var(--color-bg-page);
  border-radius: 8px;
}

/* 分类明细 */
.type-money-sheet {
  position: relative;
}

.type-money-sheet .toggle-full-btn {
  position: absolute;
  top: 16px;
  left: 16px;
  z-index: 1;
  font-size: 13px;
  color: var(--color-transfer);
  padding: 4px 10px;
  background: var(--color-transfer-bg);
  border-radius: 12px;
  font-weight: 400;
}

.type-money-list {
  padding: 16px;
  max-height: 60vh;
  overflow-y: auto;
}

.type-money-item {
  margin-bottom: 16px;
}

.type-money-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--color-bg-card);
  border-radius: 10px;
}

.type-name {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.type-total {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.type-children {
  margin-top: 8px;
  padding-left: 20px;
}

.child-item {
  display: flex;
  justify-content: space-between;
  padding: 10px 16px;
  background: var(--color-bg-page);
  border-radius: 8px;
  margin-bottom: 6px;
}

.child-name {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.child-money {
  font-size: 14px;
  color: var(--color-text-primary);
}
</style>
