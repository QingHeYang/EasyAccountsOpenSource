<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowRight, TrendCharts, Loading, Close } from '@element-plus/icons-vue'
import { analysisApi, type AnalysisTypeMonthResult, type MonthData } from '@shared/api/analysis'
import { typeApi, type TypeWithChildren } from '@shared/api/type'
import { screenApi, type ScreenFlowParams } from '@shared/api/screen'
import { flowApi, type Flow } from '@shared/api/flow'
import FlowEditor from '@desktop/components/flow/FlowEditor.vue'
import FlowItem from '@desktop/components/FlowItem.vue'

const router = useRouter()

const props = defineProps<{
  initialTypeId: number | null
  initialStartDate: string
  initialEndDate: string
}>()

// ==================== 状态 ====================
const loading = ref(false)
const result = ref<AnalysisTypeMonthResult | null>(null)

// 分类选择
const allTypes = ref<TypeWithChildren[]>([])
const selectedTypeId = ref<number | null>(null)
const selectedTypeName = ref('')
const typeDrawerVisible = ref(false)
const expandedTypeIds = ref<number[]>([])

// 时间筛选
const fastChoose = ref(1) // 1近一年 2今年 3上年 4自定义
const localStartDate = ref('')
const localEndDate = ref('')

// 展开的年份金额（点击切换完整/简化显示）
const expandedYears = ref<Set<number>>(new Set())

// 统计卡片金额展开状态
const incomeExpanded = ref(false)
const outcomeExpanded = ref(false)

// 流水列表抽屉
const flowDrawerVisible = ref(false)
const flowLoading = ref(false)
const flowList = ref<Flow[]>([])
const flowTitle = ref('')
const flowHandle = ref(0)
const currentFlowYear = ref(0)
const currentFlowMonth = ref(0)

// FlowEditor
const flowEditorVisible = ref(false)
const editingFlowId = ref<number | null>(null)

// ==================== 计算属性 ====================
const typeName = computed(() => selectedTypeName.value || '请选择分类')

// 按日期分组的流水（与 FlowList.vue 一致）
const groupedFlows = computed(() => {
  if (!flowList.value?.length) return []

  const groups: { date: string; dateLabel: string; flows: Flow[] }[] = []
  let currentDate = ''

  for (const flow of flowList.value) {
    if (flow.fdate !== currentDate) {
      currentDate = flow.fdate
      const parts = flow.fdate.split('-')
      const dateLabel = `${parseInt(parts[1])}月${parseInt(parts[2])}日`
      groups.push({ date: flow.fdate, dateLabel, flows: [] })
    }
    groups[groups.length - 1].flows.push(flow)
  }

  return groups
})

// ==================== 初始化 ====================
onMounted(async () => {
  await fetchTypes()

  // 使用传入的参数
  if (props.initialTypeId) {
    selectedTypeId.value = props.initialTypeId
    findTypeName(props.initialTypeId)
  }

  if (props.initialStartDate && props.initialEndDate) {
    localStartDate.value = props.initialStartDate
    localEndDate.value = props.initialEndDate
    fastChoose.value = 4 // 自定义
  } else {
    // 默认近一年
    onFastChoose(1)
  }

  if (selectedTypeId.value) {
    loadData()
  }
})

// ==================== 方法 ====================
async function fetchTypes() {
  try {
    const res = await typeApi.getAll()
    allTypes.value = res.data.data || []
  } catch (err) {
    console.error('获取分类列表失败', err)
  }
}

function findTypeName(typeId: number) {
  for (const parent of allTypes.value) {
    if (parent.id === typeId) {
      selectedTypeName.value = parent.tname
      return
    }
    if (parent.childrenTypes) {
      const child = parent.childrenTypes.find(c => c.id === typeId)
      if (child) {
        selectedTypeName.value = `${parent.tname} / ${child.tname}`
        return
      }
    }
  }
}

async function loadData() {
  if (!selectedTypeId.value || !localStartDate.value || !localEndDate.value) return

  loading.value = true
  try {
    const res = await analysisApi.getTypeMonthData({
      typeId: selectedTypeId.value,
      start: localStartDate.value,
      end: localEndDate.value,
    })

    if (res.data.code === 0) {
      result.value = res.data.data
      if (res.data.data?.typeName) {
        selectedTypeName.value = res.data.data.typeName.replace(/——/g, ' / ')
      }
    } else {
      ElMessage.error(res.data.msg || '获取分类统计失败')
    }
  } catch (err) {
    console.error('获取分类统计失败', err)
    ElMessage.error('获取分类统计失败')
  } finally {
    loading.value = false
  }
}

// ==================== 分类选择抽屉 ====================
function openTypeDrawer() {
  typeDrawerVisible.value = true
}

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

function selectType(type: TypeWithChildren, parent?: TypeWithChildren) {
  selectedTypeId.value = type.id
  selectedTypeName.value = parent ? `${parent.tname} / ${type.tname}` : type.tname
  typeDrawerVisible.value = false
  loadData()
}

// ==================== 时间筛选 ====================
function onFastChoose(value: number) {
  fastChoose.value = value
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth() + 1

  switch (value) {
    case 1: // 近一年
      localStartDate.value = `${year - 1}-${String(month).padStart(2, '0')}`
      localEndDate.value = `${year}-${String(month).padStart(2, '0')}`
      break
    case 2: // 今年
      localStartDate.value = `${year}-01`
      localEndDate.value = `${year}-${String(month).padStart(2, '0')}`
      break
    case 3: // 上年
      localStartDate.value = `${year - 1}-01`
      localEndDate.value = `${year - 1}-12`
      break
    case 4: // 自定义 - 不改变时间
      return
  }

  if (selectedTypeId.value) {
    loadData()
  }
}

function onStartDateChange(val: string) {
  localStartDate.value = val
  fastChoose.value = 4
  if (selectedTypeId.value && localEndDate.value) {
    loadData()
  }
}

function onEndDateChange(val: string) {
  localEndDate.value = val
  fastChoose.value = 4
  if (selectedTypeId.value && localStartDate.value) {
    loadData()
  }
}

// ==================== 金额格式化 ====================
function formatAmount(amount: string | number | undefined, expanded: boolean = false): string {
  if (!amount) return '0.00'
  const num = typeof amount === 'string' ? parseFloat(amount) : amount
  if (expanded) {
    return num.toFixed(2)
  }
  if (Math.abs(num) >= 10000) {
    return (num / 10000).toFixed(2) + '万'
  }
  return num.toFixed(2)
}

function toggleIncomeExpand() {
  incomeExpanded.value = !incomeExpanded.value
}

function toggleOutcomeExpand() {
  outcomeExpanded.value = !outcomeExpanded.value
}

function toggleYearExpand(year: number) {
  if (expandedYears.value.has(year)) {
    expandedYears.value.delete(year)
  } else {
    expandedYears.value.add(year)
  }
  expandedYears.value = new Set(expandedYears.value)
}

function formatYearAmount(year: number, amount: string): string {
  if (expandedYears.value.has(year)) {
    return parseFloat(amount).toFixed(2)
  }
  return formatAmount(amount)
}

// ==================== 月份数据 ====================
function getMonthTotal(month: MonthData): number {
  return (parseFloat(month.income) || 0) + (parseFloat(month.outcome) || 0)
}

function getYearStats(yearData: { year: number; monthData: MonthData[] }) {
  const validMonths = yearData.monthData
    .map((m) => ({
      month: m.month,
      money: getMonthTotal(m),
    }))
    .filter((m) => m.money > 0)

  if (validMonths.length < 2) {
    return { highest: null, lowest: null }
  }

  const sorted = [...validMonths].sort((a, b) => b.money - a.money)
  return {
    highest: sorted[0].month,
    lowest: sorted[sorted.length - 1].month,
  }
}

function isHighest(yearData: { year: number; monthData: MonthData[] }, month: number): boolean {
  return getYearStats(yearData).highest === month
}

function isLowest(yearData: { year: number; monthData: MonthData[] }, month: number): boolean {
  return getYearStats(yearData).lowest === month
}

// ==================== 月份点击 ====================
function onMonthItemClick(year: number, month: MonthData) {
  const total = getMonthTotal(month)
  if (total === 0) return

  // 如果只有收入，显示收入流水；只有支出，显示支出流水；都有则默认显示支出
  const hasIncome = parseFloat(month.income) > 0
  const hasOutcome = parseFloat(month.outcome) > 0

  if (hasIncome && !hasOutcome) {
    onMonthClick(year, month.month, 0) // 收入
  } else {
    onMonthClick(year, month.month, 1) // 支出（默认）
  }
}

// ==================== 流水列表 ====================
async function onMonthClick(year: number, month: number, handle: number) {
  flowHandle.value = handle
  currentFlowYear.value = year
  currentFlowMonth.value = month
  const handleText = handle === 0 ? '收入' : '支出'
  flowTitle.value = `${year}年${month}月${handleText}流水`
  flowDrawerVisible.value = true
  flowLoading.value = true
  flowList.value = []
  // 关闭 FlowEditor
  flowEditorVisible.value = false
  editingFlowId.value = null

  try {
    const monthStr = `${year}-${String(month).padStart(2, '0')}`
    const startStr = `${monthStr}-01`

    const params: ScreenFlowParams = {
      singleMonth: true,
      startDate: startStr,
      endDate: '',
      accountId: -1,
      chooseHandle: handle,
      types: selectedTypeId.value ? [selectedTypeId.value] : [],
      collect: false,
      note: '',
    }

    const res = await screenApi.getFlowByScreen(params)
    flowList.value = res.data.data?.flows || []
  } catch (err) {
    console.error('获取流水列表失败', err)
    ElMessage.error('获取流水列表失败')
  } finally {
    flowLoading.value = false
  }
}

function onFlowClick(flow: Flow) {
  editingFlowId.value = flow.id
  flowEditorVisible.value = true
}

function onFlowEditorSuccess() {
  flowEditorVisible.value = false
  editingFlowId.value = null
  // 重新加载流水列表
  onMonthClick(currentFlowYear.value, currentFlowMonth.value, flowHandle.value)
  // 重新加载统计数据
  loadData()
}

async function onFlowCollect(flow: Flow) {
  try {
    await flowApi.toggleCollect(flow.id, !flow.collect)
    // 更新列表中的收藏状态
    const item = flowList.value.find(f => f.id === flow.id)
    if (item) {
      item.collect = !item.collect
    }
    ElMessage.success(flow.collect ? '已取消收藏' : '已收藏')
  } catch (err) {
    console.error('收藏操作失败', err)
    ElMessage.error('操作失败')
  }
}

async function onFlowDelete(flow: Flow) {
  try {
    await ElMessageBox.confirm('确定删除这条流水吗？', '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await flowApi.delete(flow.id)
    ElMessage.success('删除成功')
    // 重新加载列表
    onMonthClick(currentFlowYear.value, currentFlowMonth.value, flowHandle.value)
    loadData()
  } catch (err: any) {
    if (err !== 'cancel') {
      console.error('删除失败', err)
      ElMessage.error('删除失败')
    }
  }
}

function formatFlowDate(dateStr: string): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

function formatFlowTime(dateStr: string): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}
</script>

<template>
  <div class="type-detail-page">
    <div class="detail-container">
      <!-- 主内容区 -->
      <div class="main-content">
        <div class="detail-layout">
          <!-- 左侧主区域 -->
          <div class="main-area">
            <!-- 统计卡片（始终显示） -->
            <div class="stats-cards">
              <div class="stats-card income" @click="toggleIncomeExpand" title="点击切换完整金额">
                <div class="card-label">总收入</div>
                <div class="card-value">
                  <span class="currency">¥</span>
                  <span class="amount">{{ result ? formatAmount(result.totalIncome, incomeExpanded) : '0.00' }}</span>
                </div>
              </div>

              <div class="stats-card expense" @click="toggleOutcomeExpand" title="点击切换完整金额">
                <div class="card-label">总支出</div>
                <div class="card-value">
                  <span class="currency">¥</span>
                  <span class="amount">{{ result ? formatAmount(result.totalOutcome, outcomeExpanded) : '0.00' }}</span>
                </div>
              </div>
            </div>

            <!-- 加载中 -->
            <div v-if="loading" class="loading-state">
              <el-icon class="is-loading" :size="32"><Loading /></el-icon>
              <span>加载中...</span>
            </div>

            <!-- 年度数据 -->
            <template v-else-if="result">
              <div class="year-list">
                <template v-if="result.yearData?.length">
                  <div v-for="year in result.yearData" :key="year.year" class="year-section">
                    <!-- 年份标题 -->
                    <div class="year-header">
                      <span class="year-title" @click="toggleYearExpand(year.year)">
                        {{ year.year }}年
                      </span>
                      <div class="year-stats">
                        <span v-if="parseFloat(year.income) > 0" class="income" @click="toggleYearExpand(year.year)">
                          +{{ formatYearAmount(year.year, year.income) }}
                        </span>
                        <span v-if="parseFloat(year.outcome) > 0" class="expense" @click="toggleYearExpand(year.year)">
                          -{{ formatYearAmount(year.year, year.outcome) }}
                        </span>
                        <button class="chart-btn" title="查看图表">
                          <el-icon :size="16"><TrendCharts /></el-icon>
                        </button>
                      </div>
                    </div>

                    <!-- 月份网格 -->
                    <div class="month-grid">
                      <div
                        v-for="month in year.monthData"
                        :key="month.month"
                        class="month-item"
                        :class="{
                          empty: getMonthTotal(month) === 0,
                          highest: isHighest(year, month.month),
                          lowest: isLowest(year, month.month),
                          clickable: getMonthTotal(month) > 0,
                        }"
                        @click="onMonthItemClick(year.year, month)"
                      >
                        <span class="month-label">{{ month.month }}月</span>
                        <template v-if="getMonthTotal(month) > 0">
                          <span v-if="parseFloat(month.income) > 0" class="month-income">+{{ month.income }}</span>
                          <span v-if="parseFloat(month.outcome) > 0" class="month-expense">-{{ month.outcome }}</span>
                        </template>
                        <span v-else class="month-empty">--</span>

                        <!-- 标签 -->
                        <span v-if="isHighest(year, month.month)" class="tag tag-high">最高</span>
                        <span v-else-if="isLowest(year, month.month)" class="tag tag-low">最低</span>
                      </div>
                    </div>
                  </div>
                </template>

                <el-empty v-else description="暂无数据" :image-size="80" />
              </div>
            </template>

            <!-- 未选择分类时的空状态 -->
            <div v-else class="empty-state">
              <el-empty description="" :image-size="120">
                <template #description>
                  <p class="empty-title">请选择分类查看统计</p>
                  <p class="empty-hint">点击右上角「选择分类」开始</p>
                </template>
              </el-empty>
            </div>
          </div>

          <!-- 右侧筛选面板 -->
          <div class="side-panel">
            <!-- 分类选择（置顶） -->
            <div class="filter-card">
              <div class="card-title">选择分类</div>
              <div class="type-selector" @click="openTypeDrawer">
                <span :class="{ placeholder: !selectedTypeName }">{{ typeName }}</span>
                <el-icon><ArrowRight /></el-icon>
              </div>
            </div>

            <!-- 快速筛选 -->
            <div class="filter-card">
              <div class="card-title">快速筛选</div>
              <div class="quick-options">
                <button
                  v-for="opt in [
                    { label: '近一年', value: 1 },
                    { label: '今年', value: 2 },
                    { label: '上年', value: 3 },
                  ]"
                  :key="opt.value"
                  class="quick-btn"
                  :class="{ active: fastChoose === opt.value }"
                  @click="onFastChoose(opt.value)"
                >
                  {{ opt.label }}
                </button>
              </div>
            </div>

            <!-- 自定义日期 -->
            <div class="filter-card">
              <div class="card-title">自定义时间</div>
              <div class="date-row">
                <div class="date-item">
                  <span class="date-label">开始</span>
                  <el-date-picker
                    :model-value="localStartDate"
                    type="month"
                    placeholder="开始月份"
                    format="YYYY-MM"
                    value-format="YYYY-MM"
                    class="date-picker"
                    @update:model-value="onStartDateChange"
                  />
                </div>
                <div class="date-item">
                  <span class="date-label">结束</span>
                  <el-date-picker
                    :model-value="localEndDate"
                    type="month"
                    placeholder="结束月份"
                    format="YYYY-MM"
                    value-format="YYYY-MM"
                    class="date-picker"
                    @update:model-value="onEndDateChange"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>

    <!-- 分类选择抽屉 -->
    <el-drawer
      v-model="typeDrawerVisible"
      title="选择分类"
      direction="rtl"
      size="400px"
    >
      <div class="type-list">
        <div v-for="parent in allTypes" :key="parent.id" class="type-group">
          <div
            class="type-parent"
            :class="{ active: selectedTypeId === parent.id }"
          >
            <div class="parent-left" @click="toggleTypeExpand(parent.id)">
              <el-icon class="expand-icon" :class="{ rotated: isTypeExpanded(parent.id) }">
                <ArrowRight />
              </el-icon>
              <span class="parent-name">{{ parent.tname }}</span>
              <el-tag
                v-if="parent.action"
                :type="parent.action.handle === 0 ? 'success' : parent.action.handle === 2 ? 'primary' : 'danger'"
                size="small"
              >{{ parent.action.hname }}</el-tag>
            </div>
            <el-button
              type="primary"
              text
              size="small"
              @click="selectType(parent)"
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
                :class="{ active: selectedTypeId === child.id }"
                @click="selectType(child, parent)"
              >
                <span class="child-name">{{ child.tname }}</span>
              </div>
              <div v-if="!parent.childrenTypes?.length" class="no-children">
                暂无子分类，可直接选择一级分类
              </div>
            </div>
          </Transition>
        </div>
        <el-empty v-if="allTypes.length === 0" description="暂无分类数据" />
      </div>
    </el-drawer>

    <!-- 流水列表抽屉 -->
    <el-drawer
      v-model="flowDrawerVisible"
      direction="rtl"
      size="1000px"
      :z-index="1500"
      :with-header="false"
      class="flow-list-drawer"
    >
      <div class="flow-drawer-content">
        <!-- 自定义头部 -->
        <div class="drawer-header">
          <div class="header-left">
            <h3 class="drawer-title">{{ flowTitle }}</h3>
            <span class="drawer-count">共 {{ flowList.length }} 条记录</span>
          </div>
          <button class="close-btn" @click="flowDrawerVisible = false">
            <el-icon :size="20"><Close /></el-icon>
          </button>
        </div>

        <!-- 流水列表卡片 -->
        <div class="flow-panel">
          <div v-if="flowLoading" class="flow-loading">
            <el-icon class="is-loading" :size="24"><Loading /></el-icon>
            <span>加载中...</span>
          </div>
          <template v-else-if="groupedFlows.length > 0">
            <!-- 表头 -->
            <div class="list-header">
              <span class="col-date">日期</span>
              <span class="col-type">分类</span>
              <span class="col-account">账户</span>
              <span class="col-remark">备注</span>
              <span class="col-money">金额</span>
            </div>
            <!-- 分组列表 -->
            <div class="flow-list-wrapper">
              <div class="flow-list">
                <div class="flow-group" v-for="group in groupedFlows" :key="group.date">
                  <div class="group-header">{{ group.dateLabel }}</div>
                  <div class="group-items">
                    <FlowItem
                      v-for="flow in group.flows"
                      :key="flow.id"
                      :flow="flow"
                      :show-actions="false"
                      @click="onFlowClick"
                    />
                  </div>
                </div>
              </div>
            </div>
          </template>
          <el-empty v-else description="暂无流水" :image-size="80" />
        </div>
      </div>
    </el-drawer>

    <!-- FlowEditor 抽屉（z-index 更高，覆盖在流水列表上层） -->
    <FlowEditor
      v-model:visible="flowEditorVisible"
      :flow-id="editingFlowId"
      @success="onFlowEditorSuccess"
    />
  </div>
</template>

<style scoped>
.type-detail-page {
  /* 页面容器 */
}

.detail-container {
  display: flex;
  gap: 0;
}

.main-content {
  flex: 1;
  min-width: 0;
  transition: width 0.3s ease;
}

.detail-layout {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 24px;
  align-items: start;
}

.main-area {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.side-panel {
  position: sticky;
  top: 100px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 分类选择器 */
.type-selector {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: var(--color-bg-page);
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s;
  font-size: 14px;
  color: var(--color-text-primary);
}

.type-selector:hover {
  background: rgba(0, 0, 0, 0.08);
}

.type-selector .placeholder {
  color: var(--color-text-tertiary);
}

/* 统计卡片（与 StatsCards 一致） */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.stats-card {
  padding: 24px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.2s;
  cursor: pointer;
}

.stats-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.stats-card:active {
  transform: translateY(0);
}

.card-label {
  font-size: 14px;
  color: var(--color-text-tertiary);
  margin-bottom: 8px;
}

.card-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.currency {
  font-size: 16px;
  font-weight: 500;
}

.amount {
  font-size: 28px;
  font-weight: 600;
}

.stats-card.income .card-value {
  color: var(--color-income);
}

.stats-card.expense .card-value {
  color: var(--color-expense);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px;
  color: var(--color-text-tertiary);
}

/* 年度数据 */
.year-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.year-section {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  overflow: hidden;
}

.year-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.year-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  cursor: pointer;
}

.year-title:hover {
  color: var(--color-transfer);
}

.year-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
}

.year-stats .income {
  color: var(--color-income);
  cursor: pointer;
}

.year-stats .expense {
  color: var(--color-expense);
  cursor: pointer;
}

.chart-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: var(--color-bg-page);
  border-radius: 8px;
  color: var(--color-text-secondary);
  cursor: pointer;
  margin-left: 8px;
  transition: all 0.2s;
}

.chart-btn:hover {
  background: rgba(0, 0, 0, 0.08);
  color: var(--color-transfer);
}

/* 月份网格 */
.month-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 1px;
  background: var(--color-border);
}

.month-item {
  background: #fff;
  padding: 12px 8px;
  text-align: center;
  position: relative;
  min-height: 70px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 2px;
  transition: all 0.2s;
}

.month-item:hover {
  background: #f9fafb;
}

.month-item.clickable {
  cursor: pointer;
}

.month-item.clickable:hover {
  background: rgba(99, 102, 241, 0.08);
  transform: scale(1.02);
}

.month-item.clickable:active {
  transform: scale(0.98);
}

.month-item.empty {
  opacity: 0.5;
  cursor: default;
}

.month-item.highest {
  background: rgba(59, 130, 246, 0.1);
}

.month-item.lowest {
  background: rgba(249, 115, 22, 0.1);
}

.month-label {
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-bottom: 2px;
}

.month-income {
  font-size: 12px;
  color: var(--color-income);
}

.month-expense {
  font-size: 12px;
  color: var(--color-expense);
}

.month-empty {
  font-size: 12px;
  color: var(--color-text-quaternary);
}

/* 空状态 */
.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 60px 20px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
}

.empty-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 8px;
}

.empty-hint {
  font-size: 14px;
  color: var(--color-text-tertiary);
}

.tag {
  position: absolute;
  top: 4px;
  right: 4px;
  font-size: 10px;
  padding: 1px 4px;
  border-radius: 4px;
  color: #fff;
}

.tag-high {
  background: #3b82f6;
}

.tag-low {
  background: #f97316;
}

/* 右侧筛选面板 */
.filter-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  padding: 16px;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 12px;
}

.quick-options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.quick-btn {
  padding: 8px 14px;
  border: none;
  background: var(--color-bg-page);
  border-radius: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.quick-btn:hover {
  background: rgba(0, 0, 0, 0.08);
}

.quick-btn.active {
  background: var(--color-transfer);
  color: #fff;
}

/* 日期选择 */
.date-row {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.date-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.date-label {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.date-picker {
  width: 100%;
}

.date-picker :deep(.el-input__wrapper) {
  border-radius: 8px;
}

/* 分类列表 */
.type-list {
  min-height: 200px;
}

.type-group {
  margin-bottom: 10px;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(8px);
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

/* 流水列表抽屉 */
.flow-drawer-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 24px;
  background: var(--color-bg-page);
}

/* 自定义头部 */
.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.drawer-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}

.drawer-count {
  font-size: 14px;
  color: var(--color-text-tertiary);
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: var(--color-bg-page);
  border-radius: 8px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(0, 0, 0, 0.08);
  color: var(--color-text-primary);
}

/* 流水列表卡片 - 与 FlowList.vue left-panel 一致 */
.flow-panel {
  flex: 1;
  min-height: 0;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  display: flex;
  flex-direction: column;
}

.flow-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 60px;
  color: var(--color-text-tertiary);
}

/* 列表头 - 与 FlowList.vue 一致 */
.list-header {
  display: grid;
  grid-template-columns: 60px 180px 240px 1fr 120px;
  gap: 16px;
  padding: 12px 16px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-tertiary);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.col-money {
  text-align: right;
}

/* 流水列表容器 */
.flow-list-wrapper {
  flex: 1;
  overflow-y: auto;
  margin-top: 8px;
}

/* 流水列表 - 与 FlowList.vue 一致 */
.flow-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.flow-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.group-header {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-tertiary);
  padding: 12px 16px 8px;
  background: var(--color-bg-page);
  border-radius: 8px 8px 0 0;
  margin-top: 8px;
}

.flow-group:first-child .group-header {
  margin-top: 0;
}

.group-items {
  display: flex;
  flex-direction: column;
  background: var(--color-bg-card);
  border-radius: 0 0 8px 8px;
}

/* 覆盖 FlowItem 的 grid 布局（无操作列） */
:deep(.group-items .flow-item) {
  grid-template-columns: 60px 180px 240px 1fr 120px;
}

/* 暗色模式 */
html.dark .stats-card,
html.dark .year-section,
html.dark .filter-card {
  background: rgba(40, 40, 40, 0.6);
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .type-selector {
  background: rgba(60, 60, 60, 0.4);
}

html.dark .type-selector:hover {
  background: rgba(80, 80, 80, 0.6);
}

html.dark .year-header {
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .month-item {
  background: rgba(40, 40, 40, 0.6);
}

html.dark .month-item:hover {
  background: rgba(50, 50, 50, 0.8);
}

html.dark .month-grid {
  background: rgba(255, 255, 255, 0.1);
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

html.dark .empty-state {
  background: rgba(40, 40, 40, 0.6);
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .month-item.clickable:hover {
  background: rgba(99, 102, 241, 0.15);
}

/* 流水列表暗色模式 - 与 FlowList.vue 一致 */
html.dark .close-btn {
  background: rgba(60, 60, 60, 0.4);
}

html.dark .close-btn:hover {
  background: rgba(80, 80, 80, 0.6);
}

html.dark .flow-panel {
  background: rgba(40, 40, 40, 0.6);
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .group-header {
  background: rgba(30, 30, 30, 0.6);
}

html.dark .group-items {
  background: rgba(40, 40, 40, 0.4);
}
</style>

<!-- 全局样式 -->
<style>
.flow-list-drawer {
  --el-drawer-bg-color: var(--color-bg-card);
}
</style>
