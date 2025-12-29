<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { showLoadingToast, closeToast } from 'vant'
import { analysisApi, type AnalysisTypeItem } from '@shared/api/analysis'
import AnalysisChartOverlay from '@mobile/components/AnalysisChartOverlay.vue'

const router = useRouter()

// ==================== 状态 ====================
const loading = ref(false)
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
const showFilterPopup = ref(false)
const showDatePicker = ref(false) // 日期选择器弹窗
const showChartOverlay = ref(false) // 图表弹窗

// 日期选择器
const chooseStartTime = ref<string[]>([])
const chooseEndTime = ref<string[]>([])
const minDate = new Date(2021, 0, 1)
const maxDate = new Date()

// 结束日期的最小值（不能早于开始日期）
const endMinDate = computed(() => {
  if (chooseStartTime.value.length === 2) {
    const year = parseInt(chooseStartTime.value[0])
    const month = parseInt(chooseStartTime.value[1]) - 1
    return new Date(year, month, 1)
  }
  return minDate
})

// ==================== 计算属性 ====================
const fastOptions = [
  { label: '当月', value: 0 },
  { label: '上月', value: 1 },
  { label: '近3月', value: 2 },
  { label: '近6月', value: 3 },
  { label: '近1年', value: 4 },
  { label: '当年', value: 5 },
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

function formatYearMonth(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  return `${y}-${m}`
}

function onFastChoose(value: number) {
  fastChoose.value = value
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth()

  switch (value) {
    case 0: // 当月
      startDate.value = formatYearMonth(now)
      endDate.value = formatYearMonth(now)
      break
    case 1: // 上月
      const lastMonth = new Date(year, month - 1, 1)
      startDate.value = formatYearMonth(lastMonth)
      endDate.value = formatYearMonth(lastMonth)
      break
    case 2: // 近3月
      const threeMonthsAgo = new Date(year, month - 2, 1)
      startDate.value = formatYearMonth(threeMonthsAgo)
      endDate.value = formatYearMonth(now)
      break
    case 3: // 近6月
      const sixMonthsAgo = new Date(year, month - 5, 1)
      startDate.value = formatYearMonth(sixMonthsAgo)
      endDate.value = formatYearMonth(now)
      break
    case 4: // 近1年
      const oneYearAgo = new Date(year - 1, month, 1)
      startDate.value = formatYearMonth(oneYearAgo)
      endDate.value = formatYearMonth(now)
      break
    case 5: // 当年
      startDate.value = `${year}-01`
      endDate.value = formatYearMonth(now)
      break
    case 6: // 上年
      startDate.value = `${year - 1}-01`
      endDate.value = `${year - 1}-12`
      break
  }

  fetchData()
}

async function fetchData() {
  loading.value = true
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

    closeToast()
  } catch (err) {
    closeToast()
    console.error('获取统计数据失败', err)
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

function openDatePicker() {
  // 初始化日期选择器的值
  if (startDate.value) {
    chooseStartTime.value = startDate.value.split('-')
  } else {
    const now = new Date()
    chooseStartTime.value = [String(now.getFullYear()), String(now.getMonth() + 1).padStart(2, '0')]
  }
  if (endDate.value) {
    chooseEndTime.value = endDate.value.split('-')
  } else {
    const now = new Date()
    chooseEndTime.value = [String(now.getFullYear()), String(now.getMonth() + 1).padStart(2, '0')]
  }
  showDatePicker.value = true
}

function onDatePickerConfirm() {
  // 应用自定义时间
  startDate.value = `${chooseStartTime.value[0]}-${chooseStartTime.value[1].padStart(2, '0')}`
  endDate.value = `${chooseEndTime.value[0]}-${chooseEndTime.value[1].padStart(2, '0')}`
  fastChoose.value = -1 // 标记为自定义
  showDatePicker.value = false
  fetchData() // 直接刷新数据
}

function applyFilter() {
  showFilterPopup.value = false
  fetchData()
}

function openChart() {
  showChartOverlay.value = true
}

// ==================== 生命周期 ====================
onMounted(() => {
  // 默认当月
  onFastChoose(0)
})
</script>

<template>
  <div class="analysis-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="header-title">统计</div>
      <div class="header-actions">
        <div class="header-btn" @click="showFilterPopup = true">
          <van-icon name="setting-o" size="20" />
        </div>
        <div class="header-btn" @click="openChart">
          <van-icon name="chart-trending-o" size="20" />
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

      <van-empty v-if="currentTypeList.length === 0 && !loading" description="暂无数据" />
    </div>

    <!-- 筛选弹窗 -->
    <van-popup
      v-model:show="showFilterPopup"
      position="bottom"
      round
      teleport="body"
    >
      <div class="filter-popup">
        <div class="filter-header">
          <span class="filter-title">统计条件</span>
        </div>

        <div class="filter-content">
          <!-- 选项 -->
          <div class="filter-section">
            <div class="section-title">显示选项</div>
            <div class="option-row">
              <span>合并子分类</span>
              <van-switch v-model="combineSubType" size="20" />
            </div>
            <div class="option-row">
              <span>显示全部分类</span>
              <van-switch v-model="showDisableAnalysisType" size="20" />
            </div>
          </div>

          <!-- 自定义时间 -->
          <div class="filter-section">
            <div class="section-title">自定义时间</div>
            <div class="date-row" @click="openDatePicker">
              <div class="date-display">
                <span class="date-value">{{ startDate || '开始' }}</span>
                <span class="date-sep">至</span>
                <span class="date-value">{{ endDate || '结束' }}</span>
              </div>
              <van-icon name="arrow" color="var(--color-text-tertiary)" />
            </div>
          </div>
        </div>

        <div class="filter-footer">
          <button class="apply-btn" @click="applyFilter">应用筛选</button>
        </div>
      </div>
    </van-popup>

    <!-- 日期范围选择器（独立弹窗） -->
    <van-popup v-model:show="showDatePicker" position="bottom" round teleport="body">
      <van-picker-group
        title="选择时间范围"
        :tabs="['开始月份', '结束月份']"
        @confirm="onDatePickerConfirm"
        @cancel="showDatePicker = false"
      >
        <van-date-picker
          v-model="chooseStartTime"
          :min-date="minDate"
          :max-date="maxDate"
          :columns-type="['year', 'month']"
        />
        <van-date-picker
          v-model="chooseEndTime"
          :min-date="endMinDate"
          :max-date="maxDate"
          :columns-type="['year', 'month']"
        />
      </van-picker-group>
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

/* 快速筛选 */
.quick-filter {
  display: flex;
  gap: 8px;
  padding: 0 16px 12px;
  overflow-x: auto;
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

/* 筛选弹窗 */
.filter-popup {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-page);
}

.filter-header {
  padding: 20px;
  background: var(--color-bg-card);
  text-align: center;
}

.filter-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.filter-content {
  flex: 1;
  overflow-y: auto;
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

.option-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  font-size: 14px;
  color: var(--color-text-primary);
}

.date-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: var(--color-bg-page);
  border-radius: 10px;
  cursor: pointer;
}

.date-display {
  display: flex;
  align-items: center;
  gap: 8px;
}

.date-value {
  font-size: 14px;
  color: var(--color-text-primary);
}

.date-sep {
  font-size: 13px;
  color: var(--color-text-tertiary);
}

.filter-footer {
  padding: 16px 20px;
  background: var(--color-bg-card);
}

.apply-btn {
  width: 100%;
  padding: 14px;
  background: var(--color-transfer);
  color: #fff;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 500;
}
</style>

<!-- 暗色模式 -->
<style>
.analysis-page .page-header {
  background: rgba(245, 245, 245, 0.8);
}

html.dark .analysis-page .page-header {
  background: rgba(10, 10, 10, 0.8);
}
</style>
