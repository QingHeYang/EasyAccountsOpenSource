<script setup lang="ts">
import { ref, computed, onMounted, watch, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { showLoadingToast, closeToast, showToast } from 'vant'
import { analysisApi, type AnalysisTypeItem } from '@shared/api/analysis'
import { useAnalysisFilterStore } from '@mobile/stores/analysisFilter'
import AnalysisChartOverlay from '@mobile/components/AnalysisChartOverlay.vue'

const router = useRouter()
const filterStore = useAnalysisFilterStore()

// ==================== 状态 ====================
const loading = ref(false)
const loadFailed = ref(false)
const tabIndex = ref(0) // 0收入 1支出
const showFullAmount = ref(false) // 是否显示完整金额

// 时间筛选
const fastChoose = ref(0) // 0当月 1上月 2近3月 3近6月 4近1年 5当年 6上年 7自定义
const startDate = ref('')
const endDate = ref('')

// 筛选选项
const combineSubType = ref(false) // 合并子分类
const showDisableAnalysisType = ref(true) // 显示全部分类

// 数据
const totalIn = ref('0.00')
const totalOut = ref('0.00')
const showInTypeList = ref<AnalysisTypeItem[]>([])
const showOutTypeList = ref<AnalysisTypeItem[]>([])
const allInTypeList = ref<AnalysisTypeItem[]>([])
const allOutTypeList = ref<AnalysisTypeItem[]>([])

// 禁用的分类ID（不参与百分比计算）
const disabledTypeIds = ref<Set<number>>(new Set())

// 弹窗状态
const filterExpanded = ref(false)
const showStartPicker = ref(false)
const showEndPicker = ref(false)
const showChartOverlay = ref(false) // 图表弹窗

// 日期选择器
const chooseStartTime = ref<string[]>([])
const chooseEndTime = ref<string[]>([])
const minDate = new Date(2021, 0, 1)
const maxDate = new Date()

// ==================== 计算属性 ====================
const fastOptions = [
  { label: '本月', value: 0 },
  { label: '上月', value: 1 },
  { label: '近3月', value: 2 },
  { label: '近6月', value: 3 },
  { label: '近1年', value: 4 },
  { label: '本年', value: 5 },
  { label: '上年', value: 6 },
]

// 当前显示的分类列表（带重新计算的百分比）
const currentTypeList = computed(() => {
  const list = tabIndex.value === 0 ? allInTypeList.value : allOutTypeList.value

  // 计算启用项的总金额
  const enabledTotal = list
    .filter(item => !disabledTypeIds.value.has(item.id))
    .reduce((sum, item) => sum + parseFloat(item.money || '0'), 0)

  // 重新计算百分比
  return list.map(item => {
    const isDisabled = disabledTypeIds.value.has(item.id)
    const money = parseFloat(item.money || '0')
    const newPercent = isDisabled || enabledTotal === 0
      ? 0
      : Math.round((money / enabledTotal) * 100)

    return {
      ...item,
      percent: newPercent,
      disabled: isDisabled
    }
  })
})

// 当前总计
const currentTotal = computed(() => {
  return tabIndex.value === 0 ? totalIn.value : totalOut.value
})

// 主题色
const themeColor = computed(() => {
  return tabIndex.value === 0 ? 'var(--color-income)' : 'var(--color-expense)'
})

// ==================== 方法 ====================
// 简化金额显示（上万显示为 x.xx万）
function formatLargeAmount(amount: string): string {
  const num = parseFloat(amount)
  if (isNaN(num)) return '0.00'
  if (Math.abs(num) >= 10000) {
    return (num / 10000).toFixed(2) + '万'
  }
  return amount
}

function formatYMD(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function onFastChoose(value: number) {
  fastChoose.value = value
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth()
  const today = formatYMD(now)
  const lastDayOf = (y: number, mIndex: number) => new Date(y, mIndex + 1, 0)

  switch (value) {
    case 0: // 本月
      startDate.value = formatYMD(new Date(year, month, 1))
      endDate.value = today
      break
    case 1: // 上月
      startDate.value = formatYMD(new Date(year, month - 1, 1))
      endDate.value = formatYMD(lastDayOf(year, month - 1))
      break
    case 2: // 近3月
      startDate.value = formatYMD(new Date(year, month - 2, 1))
      endDate.value = today
      break
    case 3: // 近6月
      startDate.value = formatYMD(new Date(year, month - 5, 1))
      endDate.value = today
      break
    case 4: // 近1年
      startDate.value = formatYMD(new Date(year - 1, month, 1))
      endDate.value = today
      break
    case 5: // 本年
      startDate.value = `${year}-01-01`
      endDate.value = today
      break
    case 6: // 上年
      startDate.value = `${year - 1}-01-01`
      endDate.value = `${year - 1}-12-31`
      break
  }

  fetchData()
}

async function fetchData() {
  loading.value = true
  loadFailed.value = false
  showLoadingToast({ message: '加载中...', forbidClick: true, duration: 0 })

  try {
    const res = await analysisApi.getTypeList({
      start: startDate.value,
      end: endDate.value,
      combineSubType: combineSubType.value,
      showDisableAnalysisType: showDisableAnalysisType.value,
    })

    const data = res.data.data
    totalIn.value = data.totalIn
    totalOut.value = data.totalOut
    showInTypeList.value = data.showInTypeList
    showOutTypeList.value = data.showOutTypeList
    allInTypeList.value = data.allInTypeList
    allOutTypeList.value = data.allOutTypeList

    // 成功才关 loading toast；失败让全局 onError 弹的 fail toast 自然显示
    closeToast()
  } catch (err) {
    console.error('获取统计数据失败', err)
    // 网络错误：清空 + 标记失败，列表显示"加载失败"占位
    totalIn.value = '0.00'
    totalOut.value = '0.00'
    showInTypeList.value = []
    showOutTypeList.value = []
    allInTypeList.value = []
    allOutTypeList.value = []
    loadFailed.value = true
  } finally {
    loading.value = false
  }
}

function onTabClick(index: number) {
  if (tabIndex.value === index) {
    // 点击已选中的 tab，切换金额显示模式
    showFullAmount.value = !showFullAmount.value
  } else {
    tabIndex.value = index
  }
}

function toTypeDetail(typeId: number) {
  // 标记是从统计页面进入的
  sessionStorage.setItem('analysisTypeFrom', 'analysis')
  router.push({
    path: '/analysis/type',
    query: {
      typeId: String(typeId),
      start: startDate.value,
      end: endDate.value,
    },
  })
}

// 切换分类的禁用状态
function toggleTypeDisabled(typeId: number) {
  const newSet = new Set(disabledTypeIds.value)
  if (newSet.has(typeId)) {
    newSet.delete(typeId)
  } else {
    newSet.add(typeId)
  }
  disabledTypeIds.value = newSet
}

function initPickerArr(date: string): string[] {
  // 期望 yyyy-MM-dd，向后兼容 yyyy-MM（旧 store 数据自动补 01）
  const parts = date.split('-')
  if (parts.length === 3) return parts
  if (parts.length === 2) return [parts[0], parts[1], '01']
  const now = new Date()
  return [
    String(now.getFullYear()),
    String(now.getMonth() + 1).padStart(2, '0'),
    String(now.getDate()).padStart(2, '0'),
  ]
}

function openStartPicker() {
  chooseStartTime.value = initPickerArr(startDate.value)
  showStartPicker.value = true
}

function openEndPicker() {
  chooseEndTime.value = initPickerArr(endDate.value)
  showEndPicker.value = true
}

function onStartConfirm() {
  const [y, m, d] = chooseStartTime.value
  const newStart = `${y}-${m.padStart(2, '0')}-${d.padStart(2, '0')}`
  if (endDate.value && newStart > endDate.value) {
    showToast('开始日期不能晚于结束日期')
    return
  }
  startDate.value = newStart
  fastChoose.value = -1
  showStartPicker.value = false
  fetchData()
}

function onEndConfirm() {
  const [y, m, d] = chooseEndTime.value
  const newEnd = `${y}-${m.padStart(2, '0')}-${d.padStart(2, '0')}`
  if (startDate.value && newEnd < startDate.value) {
    showToast('结束日期不能早于开始日期')
    return
  }
  endDate.value = newEnd
  fastChoose.value = -1
  showEndPicker.value = false
  fetchData()
}

// 是否有非默认筛选值（用于头部按钮 dot 提示）
const hasCustomFilter = computed(
  () => combineSubType.value || !showDisableAnalysisType.value || fastChoose.value === -1
)

function openChart() {
  showChartOverlay.value = true
}

// ==================== 生命周期 ====================
onMounted(() => {
  // 从 store 恢复状态（如果有保存的状态）
  if (filterStore.initialized) {
    fastChoose.value = filterStore.fastChoose
    startDate.value = filterStore.startDate
    endDate.value = filterStore.endDate
    tabIndex.value = filterStore.tabIndex
    combineSubType.value = filterStore.combineSubType
    showDisableAnalysisType.value = filterStore.showDisableAnalysisType
    // 使用保存的时间范围获取数据
    fetchData()
  } else {
    // 首次进入，默认当月
    onFastChoose(0)
  }
})

// 离开页面前保存状态
onBeforeUnmount(() => {
  filterStore.save({
    fastChoose: fastChoose.value,
    startDate: startDate.value,
    endDate: endDate.value,
    tabIndex: tabIndex.value,
    combineSubType: combineSubType.value,
    showDisableAnalysisType: showDisableAnalysisType.value,
  })
})
</script>

<template>
  <div class="analysis-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="header-title">统计</div>
      <div class="header-actions">
        <div class="header-btn" @click="filterExpanded = !filterExpanded">
          <van-icon name="filter-o" size="20" />
          <span v-if="hasCustomFilter" class="filter-dot"></span>
        </div>
        <div class="header-btn" @click="openChart">
          <van-icon name="chart-trending-o" size="20" />
        </div>
      </div>
    </div>

    <!-- 折叠筛选面板 -->
    <div class="filter-bar" :class="{ expanded: filterExpanded }">
      <!-- 快捷时间 chip -->
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

      <div class="option-pair">
        <div class="filter-row option-row">
          <span class="option-label">合并子分类</span>
          <van-switch v-model="combineSubType" size="18" @change="fetchData" />
        </div>
        <div class="filter-row option-row">
          <span class="option-label">显示全部</span>
          <van-switch v-model="showDisableAnalysisType" size="18" @change="fetchData" />
        </div>
      </div>
      <div class="option-pair">
        <div class="filter-row date-row" @click="openStartPicker">
          <span class="option-label">开始</span>
          <div class="date-display">
            <span class="date-value">{{ startDate || '请选择' }}</span>
            <van-icon name="arrow" size="12" class="date-arrow" />
          </div>
        </div>
        <div class="filter-row date-row" @click="openEndPicker">
          <span class="option-label">结束</span>
          <div class="date-display">
            <span class="date-value">{{ endDate || '请选择' }}</span>
            <van-icon name="arrow" size="12" class="date-arrow" />
          </div>
        </div>
      </div>
    </div>

    <!-- Tab 切换 -->
    <div class="tab-section">
      <div
        class="tab-item"
        :class="{ active: tabIndex === 0 }"
        @click="onTabClick(0)"
      >
        <span class="tab-label">收入</span>
        <span class="tab-value income">¥{{ showFullAmount ? totalIn : formatLargeAmount(totalIn) }}</span>
      </div>
      <div
        class="tab-item"
        :class="{ active: tabIndex === 1 }"
        @click="onTabClick(1)"
      >
        <span class="tab-label">支出</span>
        <span class="tab-value expense">¥{{ showFullAmount ? totalOut : formatLargeAmount(totalOut) }}</span>
      </div>
    </div>

    <!-- 分类列表 -->
    <div class="type-grid">
      <div
        v-for="item in currentTypeList"
        :key="item.id"
        class="type-card"
        :class="{ disabled: item.disabled }"
        @click="toTypeDetail(item.id)"
        @contextmenu.prevent="toggleTypeDisabled(item.id)"
      >
        <div class="type-name">{{ item.name }}</div>
        <div class="card-footer">
          <span class="card-money">¥{{ item.money }}</span>
          <span v-if="!item.disabled" class="type-percent" :class="tabIndex === 0 ? 'income' : 'expense'">
            {{ item.percent }}%
          </span>
          <span v-else class="type-percent disabled">--</span>
        </div>
      </div>

      <van-empty
        v-if="currentTypeList.length === 0 && !loading"
        :image="loadFailed ? 'network' : 'default'"
        :description="loadFailed ? '加载失败，请调整筛选或重试' : '暂无数据'"
      />
    </div>


    <!-- 开始日期选择器 -->
    <van-popup v-model:show="showStartPicker" position="bottom" round teleport="body">
      <van-date-picker
        v-model="chooseStartTime"
        title="选择开始日期"
        :min-date="minDate"
        :max-date="maxDate"
        :columns-type="['year', 'month', 'day']"
        @confirm="onStartConfirm"
        @cancel="showStartPicker = false"
      />
    </van-popup>

    <!-- 结束日期选择器 -->
    <van-popup v-model:show="showEndPicker" position="bottom" round teleport="body">
      <van-date-picker
        v-model="chooseEndTime"
        title="选择结束日期"
        :min-date="minDate"
        :max-date="maxDate"
        :columns-type="['year', 'month', 'day']"
        @confirm="onEndConfirm"
        @cancel="showEndPicker = false"
      />
    </van-popup>

    <!-- 图表弹窗 -->
    <AnalysisChartOverlay
      v-model:show="showChartOverlay"
      :total-in="totalIn"
      :total-out="totalOut"
      :in-type-list="allInTypeList"
      :out-type-list="allOutTypeList"
    />
  </div>
</template>

<style scoped>
.analysis-page {
  min-height: 100vh;
  background: transparent;
  padding-top: 72px;
  padding-bottom: 100px;
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

.header-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.header-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: var(--color-bg-card);
  color: var(--color-text-primary);
}

/* Tab 切换 */
.tab-section {
  display: flex;
  gap: 12px;
  padding: 0 16px;
  margin-top: 10px;
  margin-bottom: 12px;
}

.tab-item {
  flex: 1;
  padding: 16px;
  background: var(--color-bg-card);
  border-radius: 16px;
  text-align: center;
  border: 2px solid transparent;
  transition: all 0.2s;
}

.tab-item.active {
  border-color: var(--color-transfer);
}

.tab-label {
  display: block;
  font-size: 13px;
  color: var(--color-text-tertiary);
  margin-bottom: 6px;
}

.tab-value {
  display: block;
  font-size: 20px;
  font-weight: 600;
}

.tab-value.income {
  color: var(--color-income);
}

.tab-value.expense {
  color: var(--color-expense);
}

/* 快速筛选（在 filter-bar 内）*/
.quick-filter {
  display: flex;
  gap: 8px;
  padding: 4px 0 8px;
  margin-bottom: 6px;
  overflow-x: auto;
  overflow-y: hidden;
  -webkit-overflow-scrolling: touch;
  touch-action: pan-x;
  scrollbar-width: none;
}

.quick-filter::-webkit-scrollbar {
  display: none;
}

.quick-item {
  padding: 8px 14px;
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

/* 分类网格 */
.type-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  padding: 0 16px;
}

.type-grid :deep(.van-empty) {
  grid-column: span 2;
  padding-top: 40px;
}

.type-card {
  background: var(--color-bg-card);
  border-radius: 16px;
  padding: 16px;
}

.type-card:active {
  opacity: 0.8;
}

.type-card.disabled {
  opacity: 0.5;
}

.type-percent.disabled {
  color: var(--color-text-tertiary);
  font-weight: 400;
}

.type-name {
  font-size: 14px;
  color: var(--color-text-primary);
  font-weight: 500;
  margin-bottom: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.card-money {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.type-percent {
  font-size: 16px;
  font-weight: 600;
}

.type-percent.income {
  color: var(--color-income);
}

.type-percent.expense {
  color: var(--color-expense);
}

/* === 折叠筛选面板（流式布局，展开时下层内容跟着下推，不浮在上方） === */
.filter-bar {
  padding: 0 16px;
  max-height: 0;
  overflow-x: visible;
  overflow-y: hidden;
  transition: max-height 0.3s ease, padding 0.3s ease, margin 0.3s ease;
  margin-top: 0;
}

.filter-bar.expanded {
  max-height: 260px;
  padding: 8px 16px 4px;
}

.filter-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  margin-bottom: 6px;
  background: var(--color-bg-card);
  border-radius: 10px;
}

.filter-row:last-child {
  margin-bottom: 0;
}

/* 两个 switch 选项一行 */
.option-pair {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  margin-bottom: 6px;
}

.option-pair .filter-row {
  margin-bottom: 0;
  padding: 6px 10px;
}

.option-pair .option-label {
  font-size: 13px;
}

.option-label {
  font-size: 14px;
  color: var(--color-text-primary);
}

.date-row {
  cursor: pointer;
}

.date-row:active {
  opacity: 0.7;
}

.date-display {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--color-text-secondary);
}

.date-value {
  font-size: 13px;
  color: var(--color-text-primary);
  font-variant-numeric: tabular-nums;
}

.date-sep {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.date-arrow {
  color: var(--color-text-tertiary);
}

/* 头部按钮上的红点（有非默认筛选时显示） */
.filter-dot {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-transfer);
}

.header-btn {
  position: relative;
}
</style>

<!-- 暗色模式 -->
<style>
.analysis-page .page-header,
.analysis-page .filter-bar {
  background: rgba(245, 245, 245, 0.8);
}

html.dark .analysis-page .page-header,
html.dark .analysis-page .filter-bar {
  background: rgba(10, 10, 10, 0.8);
}
</style>
