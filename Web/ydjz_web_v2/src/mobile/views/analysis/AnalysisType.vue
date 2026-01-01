<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showLoadingToast, closeToast, showToast } from 'vant'
import { analysisApi, type AnalysisTypeMonthResult, type MonthData } from '@shared/api/analysis'
import { typeApi, type TypeWithChildren } from '@shared/api/type'
import { screenApi, type ScreenFlowParams } from '@shared/api/screen'
import type { Flow } from '@shared/api/flow'
import { useSmartBack } from '@shared/composables/useSmartBack'
import FlowItem from '@mobile/components/FlowItem.vue'
import YearLineChartOverlay from '@mobile/components/YearLineChartOverlay.vue'

const router = useRouter()
const route = useRoute()
const { smartBack } = useSmartBack()

// ==================== 状态 ====================
const loading = ref(false)
const selectedTypeId = ref<number | null>(null)
const selectedTypeName = ref('')
const allTypes = ref<TypeWithChildren[]>([])

// 分类选择弹窗
const showTypePicker = ref(false)
const expandedTypeId = ref<number | null>(null)

// 快捷选项：1近一年 2今年 3上年 4自定义
const fastChoose = ref('1')

// 日期选择
const showDatePicker = ref(false)
const startDate = ref('')
const endDate = ref('')
const chooseStartTime = ref<string[]>([])
const chooseEndTime = ref<string[]>([])
const minDate = new Date(2021, 0, 1)
const maxDate = new Date()

// 数据
const result = ref<AnalysisTypeMonthResult | null>(null)

// 年度金额展开状态（显示完整金额）
const yearAmountExpanded = ref<Set<number>>(new Set())

// 流水弹窗
const showFlowPopup = ref(false)
const flowList = ref<Flow[]>([])
const flowMonth = ref('')
const flowLoading = ref(false)

// 年度图表弹窗
const showYearChart = ref(false)
const chartYear = ref(0)
const chartMonthData = ref<MonthData[]>([])

// ==================== 计算属性 ====================
const typeName = computed(() => selectedTypeName.value || '请选择分类')

// 格式化金额（万以上转换）
function formatAmount(amount: string | number | undefined): string {
  if (!amount) return '0.00'
  const num = typeof amount === 'string' ? parseFloat(amount) : amount
  if (Math.abs(num) >= 10000) {
    return (num / 10000).toFixed(2) + '万'
  }
  return num.toFixed(2)
}

// 显示完整金额
function showFullAmount(label: string, amount: string | number | undefined) {
  const num = amount ? (typeof amount === 'string' ? parseFloat(amount) : amount) : 0
  showToast({
    message: `${label}: ¥${num.toFixed(2)}`,
    position: 'top',
  })
}

// 切换年度金额显示模式
function toggleYearAmount(year: number) {
  if (yearAmountExpanded.value.has(year)) {
    yearAmountExpanded.value.delete(year)
  } else {
    yearAmountExpanded.value.add(year)
  }
  // 触发响应式更新
  yearAmountExpanded.value = new Set(yearAmountExpanded.value)
}

// 打开年度图表
function openYearChart(year: number, monthData: MonthData[]) {
  chartYear.value = year
  chartMonthData.value = monthData
  showYearChart.value = true
}

// 格式化年度金额（根据展开状态）
function formatYearAmount(year: number, amount: string): string {
  if (yearAmountExpanded.value.has(year)) {
    return parseFloat(amount).toFixed(2)
  }
  return formatAmount(amount)
}

// 计算每年的最高和最低月份
function getYearStats(yearData: { year: number; monthData: MonthData[] }) {
  const validMonths = yearData.monthData
    .map((m) => ({
      month: m.month,
      money: (parseFloat(m.income) || 0) + (parseFloat(m.outcome) || 0),
    }))
    .filter((m) => m.money > 0)

  // 只有2条及以上数据才计算最高最低
  if (validMonths.length < 2) {
    return { highest: null, lowest: null }
  }

  const sorted = [...validMonths].sort((a, b) => b.money - a.money)
  return {
    highest: sorted[0].month,
    lowest: sorted[sorted.length - 1].month,
  }
}

// ==================== 方法 ====================
function onBack() {
  smartBack('/analysis')
}

function formatYearMonth(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  return `${y}-${m}`
}

function initDateRange() {
  // 优先使用外部传入的时间
  if (route.query.start && route.query.end) {
    startDate.value = route.query.start as string
    endDate.value = route.query.end as string
    fastChoose.value = '4' // 自定义
  } else {
    // 默认近一年
    onFastDateChoose('1')
  }
  // 初始化时间选择器的值
  chooseStartTime.value = startDate.value.split('-')
  chooseEndTime.value = endDate.value.split('-')
}

function onFastDateChoose(value: string) {
  fastChoose.value = value
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth() + 1

  switch (value) {
    case '1': // 近一年
      startDate.value = `${year - 1}-${String(month).padStart(2, '0')}`
      endDate.value = `${year}-${String(month).padStart(2, '0')}`
      break
    case '2': // 今年
      startDate.value = `${year}-01`
      endDate.value = `${year}-${String(month).padStart(2, '0')}`
      break
    case '3': // 上年
      startDate.value = `${year - 1}-01`
      endDate.value = `${year - 1}-12`
      break
    case '4': // 自定义 - 不改变时间
      return
  }

  chooseStartTime.value = startDate.value.split('-')
  chooseEndTime.value = endDate.value.split('-')

  if (selectedTypeId.value) {
    fetchData()
  }
}

function formatDateDisplay(date: string): string {
  if (!date) return ''
  const [year, month] = date.split('-')
  return `${year}年${month}月`
}

async function fetchTypes() {
  try {
    const res = await typeApi.getAll()
    allTypes.value = res.data.data || []
  } catch (err) {
    console.error('获取分类列表失败', err)
  }
}

async function fetchData() {
  if (!selectedTypeId.value) return

  loading.value = true
  showLoadingToast({ message: '加载中...', forbidClick: true, duration: 0 })

  try {
    const res = await analysisApi.getTypeMonthData({
      typeId: selectedTypeId.value,
      start: startDate.value,
      end: endDate.value,
    })

    result.value = res.data.data
    // 更新分类名称（API返回的可能有完整路径）
    if (res.data.data?.typeName) {
      selectedTypeName.value = res.data.data.typeName.replace(/——/g, '/')
    }
    closeToast()
  } catch (err) {
    closeToast()
    console.error('获取分类统计失败', err)
  } finally {
    loading.value = false
  }
}

// ==================== 日期选择 ====================
function onDateConfirm() {
  // 验证开始时间不能大于结束时间
  const startNum = parseInt(chooseStartTime.value[0]) * 100 + parseInt(chooseStartTime.value[1])
  const endNum = parseInt(chooseEndTime.value[0]) * 100 + parseInt(chooseEndTime.value[1])
  if (startNum > endNum) {
    showToast('开始时间不能大于结束时间')
    return
  }

  startDate.value = `${chooseStartTime.value[0]}-${chooseStartTime.value[1].padStart(2, '0')}`
  endDate.value = `${chooseEndTime.value[0]}-${chooseEndTime.value[1].padStart(2, '0')}`
  showDatePicker.value = false

  if (selectedTypeId.value) {
    fetchData()
  }
}

function onDateCancel() {
  showDatePicker.value = false
}

// ==================== 分类选择 ====================
function toggleTypeExpand(typeId: number) {
  if (expandedTypeId.value === typeId) {
    expandedTypeId.value = null
  } else {
    expandedTypeId.value = typeId
  }
}

function selectType(type: TypeWithChildren, isChild: boolean = false) {
  selectedTypeId.value = type.id
  selectedTypeName.value = type.tname
  showTypePicker.value = false
  expandedTypeId.value = null
  fetchData()
}

// ==================== 月份数据 ====================
function isHighest(yearData: { year: number; monthData: MonthData[] }, month: number): boolean {
  const stats = getYearStats(yearData)
  return stats.highest === month
}

function isLowest(yearData: { year: number; monthData: MonthData[] }, month: number): boolean {
  const stats = getYearStats(yearData)
  return stats.lowest === month
}

function getMonthTotal(month: MonthData): number {
  return (parseFloat(month.income) || 0) + (parseFloat(month.outcome) || 0)
}

// ==================== 流水列表 ====================
// chooseHandle: 0收入 1支出
async function onMonthClick(year: number, month: number, chooseHandle: number) {
  const monthStr = `${year}-${String(month).padStart(2, '0')}`
  flowMonth.value = `${year}年${month}月`
  showFlowPopup.value = true
  flowLoading.value = true
  flowList.value = []

  try {
    const startStr = `${monthStr}-01`

    // 按原接口格式：singleMonth=true, endDate为空
    const params: ScreenFlowParams = {
      singleMonth: true,
      startDate: startStr,
      endDate: '',
      accountId: -1,
      chooseHandle: chooseHandle,
      types: selectedTypeId.value ? [selectedTypeId.value] : [],
      collect: false,
      note: '',
    }

    const res = await screenApi.getFlowByScreen(params)
    flowList.value = res.data.data?.flows || []
  } catch (err) {
    console.error('获取流水列表失败', err)
    showToast('获取流水失败')
  } finally {
    flowLoading.value = false
  }
}

function onFlowClick(flow: Flow) {
  showFlowPopup.value = false
  router.push({ path: `/flow/edit/${flow.id}` })
}

// ==================== 生命周期 ====================
onMounted(async () => {
  initDateRange()
  await fetchTypes()

  // 从路由获取 typeId
  if (route.query.typeId) {
    const typeId = Number(route.query.typeId)
    selectedTypeId.value = typeId

    // 查找分类名称
    for (const parent of allTypes.value) {
      if (parent.id === typeId) {
        selectedTypeName.value = parent.tname
        break
      }
      if (parent.childrenTypes) {
        const child = parent.childrenTypes.find((c) => c.id === typeId)
        if (child) {
          selectedTypeName.value = `${parent.tname}/${child.tname}`
          break
        }
      }
    }

    fetchData()
  }
})
</script>

<template>
  <div class="analysis-type-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="header-left" @click="onBack">
        <van-icon name="arrow-left" size="20" />
      </div>
      <div class="header-title">分类统计</div>
      <div class="header-right"></div>
    </div>

    <!-- 分类选择（悬浮） -->
    <div class="type-selector-sticky">
      <div class="type-selector" @click="showTypePicker = true">
        <span class="type-label">{{ typeName }}</span>
        <van-icon name="arrow-down" size="16" />
      </div>
    </div>

    <!-- 快捷选项 -->
    <div class="filter-section">
      <div class="quick-filter">
        <div
          class="quick-item"
          :class="{ active: fastChoose === '1' }"
          @click="onFastDateChoose('1')"
        >近一年</div>
        <div
          class="quick-item"
          :class="{ active: fastChoose === '2' }"
          @click="onFastDateChoose('2')"
        >今年</div>
        <div
          class="quick-item"
          :class="{ active: fastChoose === '3' }"
          @click="onFastDateChoose('3')"
        >上年</div>
        <div
          class="quick-item"
          :class="{ active: fastChoose === '4' }"
          @click="fastChoose = '4'"
        >自定义</div>
      </div>
      <!-- 自定义时间折叠显示 -->
      <div v-if="fastChoose === '4'" class="custom-date" @click="showDatePicker = true">
        <van-icon name="clock-o" size="14" />
        <span>{{ formatDateDisplay(startDate) }} 至 {{ formatDateDisplay(endDate) }}</span>
        <van-icon name="arrow" size="12" />
      </div>
    </div>

    <!-- 统计卡片 -->
    <div v-if="result" class="stats-card">
      <div class="stats-row">
        <div class="stats-item" @click="showFullAmount('总收入', result.totalIncome)">
          <span class="stats-label">总收入</span>
          <span class="stats-value income">¥{{ formatAmount(result.totalIncome) }}</span>
        </div>
        <div class="stats-divider"></div>
        <div class="stats-item" @click="showFullAmount('总支出', result.totalOutcome)">
          <span class="stats-label">总支出</span>
          <span class="stats-value expense">¥{{ formatAmount(result.totalOutcome) }}</span>
        </div>
      </div>
    </div>

    <!-- 年度数据 -->
    <div class="year-list">
      <div v-for="year in result?.yearData" :key="year.year" class="year-section">
        <div class="year-header">
          <span class="year-title" @click="toggleYearAmount(year.year)">{{ year.year }}年</span>
          <div class="year-stats">
            <span v-if="parseFloat(year.income) > 0" class="income" @click="toggleYearAmount(year.year)">+{{ formatYearAmount(year.year, year.income) }}</span>
            <span v-if="parseFloat(year.outcome) > 0" class="expense" @click="toggleYearAmount(year.year)">-{{ formatYearAmount(year.year, year.outcome) }}</span>
            <div class="chart-btn" @click="openYearChart(year.year, year.monthData)">
              <van-icon name="chart-trending-o" size="16" />
            </div>
          </div>
        </div>

        <div class="month-grid">
          <div
            v-for="month in year.monthData"
            :key="month.month"
            class="month-item"
            :class="{
              empty: getMonthTotal(month) === 0,
              highest: isHighest(year, month.month),
              lowest: isLowest(year, month.month),
            }"
          >
            <span class="month-label">{{ month.month }}月</span>
            <template v-if="getMonthTotal(month) > 0">
              <span
                v-if="parseFloat(month.income) > 0"
                class="month-income clickable"
                @click="onMonthClick(year.year, month.month, 0)"
              >+{{ month.income }}</span>
              <span
                v-if="parseFloat(month.outcome) > 0"
                class="month-expense clickable"
                @click="onMonthClick(year.year, month.month, 1)"
              >-{{ month.outcome }}</span>
            </template>
            <span v-else class="month-empty">--</span>

            <!-- 最高/最低标签 -->
            <span v-if="isHighest(year, month.month)" class="tag tag-highest">最高</span>
            <span v-else-if="isLowest(year, month.month)" class="tag tag-lowest">最低</span>
          </div>
        </div>
      </div>

      <van-empty v-if="!result && !loading" description="请选择分类查看统计" />
      <van-empty v-else-if="result?.yearData?.length === 0" description="暂无数据" />
    </div>

    <!-- 分类选择器弹窗 -->
    <van-popup
      v-model:show="showTypePicker"
      position="bottom"
      round
      teleport="body"
      :style="{ height: '70%' }"
    >
      <div class="type-picker">
        <div class="picker-header">
          <span class="picker-title">选择分类</span>
          <van-icon name="cross" size="20" @click="showTypePicker = false" />
        </div>
        <div class="type-list">
          <div v-for="type in allTypes" :key="type.id" class="type-group">
            <!-- 一级分类 -->
            <div
              class="type-parent"
              :class="{ expanded: expandedTypeId === type.id, selected: selectedTypeId === type.id }"
              @click="type.childrenTypes?.length ? toggleTypeExpand(type.id) : selectType(type)"
            >
              <div class="type-parent-info">
                <span class="type-name">{{ type.tname }}</span>
                <van-tag
                  v-if="type.action"
                  :type="type.action.handle === 0 ? 'success' : type.action.handle === 2 ? 'primary' : 'danger'"
                >{{ type.action.hname }}</van-tag>
              </div>
              <div class="type-parent-right">
                <span
                  v-if="!type.childrenTypes?.length"
                  class="select-btn"
                  @click.stop="selectType(type)"
                >选择</span>
                <van-icon
                  v-else
                  class="expand-icon"
                  :class="{ rotated: expandedTypeId === type.id }"
                  name="arrow-down"
                  size="16"
                />
              </div>
            </div>
            <!-- 二级分类（标签形式）带动画 -->
            <transition name="slide-fade">
              <div v-if="expandedTypeId === type.id && type.childrenTypes?.length" class="type-children">
                <div
                  class="child-tag"
                  :class="{ selected: selectedTypeId === type.id }"
                  @click="selectType(type)"
                >全部</div>
                <div
                  v-for="child in type.childrenTypes"
                  :key="child.id"
                  class="child-tag"
                  :class="{ selected: selectedTypeId === child.id }"
                  @click="selectType(child, true)"
                >{{ child.tname }}</div>
              </div>
            </transition>
          </div>
        </div>
      </div>
    </van-popup>

    <!-- 日期选择器（双列） -->
    <van-popup v-model:show="showDatePicker" position="bottom" round teleport="body">
      <van-picker-group
        title="选择时间段"
        :tabs="['开始月份', '结束月份']"
        @confirm="onDateConfirm"
        @cancel="onDateCancel"
      >
        <van-date-picker
          v-model="chooseStartTime"
          :min-date="minDate"
          :max-date="maxDate"
          :columns-type="['year', 'month']"
        />
        <van-date-picker
          v-model="chooseEndTime"
          :min-date="minDate"
          :max-date="maxDate"
          :columns-type="['year', 'month']"
        />
      </van-picker-group>
    </van-popup>

    <!-- 流水列表弹窗 -->
    <van-action-sheet v-model:show="showFlowPopup" :title="flowMonth + '流水'" teleport="body">
      <div class="flow-popup-content">
        <van-loading v-if="flowLoading" size="24px" vertical>加载中...</van-loading>
        <template v-else-if="flowList.length > 0">
          <div class="flow-items">
            <FlowItem
              v-for="flow in flowList"
              :key="flow.id"
              :flow="flow"
              show-remark
              disable-actions
              @click="onFlowClick"
            />
          </div>
        </template>
        <van-empty v-else description="暂无流水" />
      </div>
    </van-action-sheet>

    <!-- 年度图表弹窗 -->
    <YearLineChartOverlay
      v-model:show="showYearChart"
      :year="chartYear"
      :type-name="selectedTypeName"
      :month-data="chartMonthData"
    />
  </div>
</template>

<style scoped>
.analysis-type-page {
  min-height: 100vh;
  background: var(--color-bg-page);
  padding-bottom: 40px;
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
}

.header-right {
  background: transparent;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

/* 分类选择器（悬浮） */
.type-selector-sticky {
  position: sticky;
  top: 72px;
  z-index: 40;
  padding: 0 16px 12px;
  background: var(--color-bg-page);
}

.type-selector {
  padding: 14px 16px;
  background: var(--color-bg-card);
  border-radius: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.type-label {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-primary);
}

/* 快捷选项区域 */
.filter-section {
  margin: 0 16px 16px;
  padding: 12px 16px;
  background: var(--color-bg-card);
  border-radius: 12px;
}

.quick-filter {
  display: flex;
  gap: 10px;
}

.quick-item {
  padding: 6px 14px;
  background: var(--color-bg-page);
  border-radius: 16px;
  font-size: 13px;
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.quick-item.active {
  background: var(--color-transfer);
  color: #fff;
}

.custom-date {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
  padding: 8px 12px;
  background: var(--color-bg-page);
  border-radius: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.custom-date span {
  flex: 1;
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
  text-align: center;
  padding: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.stats-item:active {
  background: var(--color-bg-page);
}

.stats-label {
  display: block;
  font-size: 13px;
  color: var(--color-text-tertiary);
  margin-bottom: 6px;
}

.stats-value {
  font-size: 20px;
  font-weight: 600;
}

.stats-value.income {
  color: var(--color-income);
}

.stats-value.expense {
  color: var(--color-expense);
}

.stats-divider {
  width: 1px;
  height: 40px;
  background: var(--color-border);
  margin: 0 16px;
}

/* 年度数据 */
.year-list {
  padding: 0 16px;
}

.year-section {
  background: var(--color-bg-card);
  border-radius: 16px;
  margin-bottom: 16px;
  overflow: hidden;
}

.year-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--color-border);
}

.year-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.year-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
}

.year-stats .income {
  color: var(--color-income);
}

.year-stats .expense {
  color: var(--color-expense);
}

.chart-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-page);
  border-radius: 8px;
  color: var(--color-text-secondary);
  margin-left: 8px;
}

.chart-btn:active {
  opacity: 0.7;
}

/* 月份网格 */
.month-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1px;
  background: var(--color-border);
}

.month-item {
  background: var(--color-bg-card);
  padding: 12px 8px;
  text-align: center;
  position: relative;
  min-height: 70px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 2px;
}

.month-item.empty {
  opacity: 0.5;
}

/* 最高最低使用中性色，避免与收支颜色混淆 */
.month-item.highest {
  background: rgba(59, 130, 246, 0.1); /* 蓝色背景 */
}

.month-item.lowest {
  background: rgba(249, 115, 22, 0.1); /* 橙色背景 */
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

.month-income.clickable,
.month-expense.clickable {
  padding: 2px 6px;
  border-radius: 4px;
  cursor: pointer;
}

.month-income.clickable:active {
  background: var(--color-income-bg);
}

.month-expense.clickable:active {
  background: var(--color-expense-bg);
}

.month-empty {
  font-size: 12px;
  color: var(--color-text-quaternary);
}

/* 最高/最低标签（中性色） */
.tag {
  position: absolute;
  top: 4px;
  right: 4px;
  font-size: 10px;
  padding: 1px 4px;
  border-radius: 4px;
}

.tag-highest {
  background: #3b82f6; /* 蓝色 */
  color: #fff;
}

.tag-lowest {
  background: #f97316; /* 橙色 */
  color: #fff;
}

/* 分类选择器弹窗 */
.type-picker {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-page);
}

.picker-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--color-bg-card);
  border-bottom: 1px solid var(--color-border);
}

.picker-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.type-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.type-group {
  margin-bottom: 2px;
}

.type-parent {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: var(--color-bg-card);
  transition: background 0.2s;
}

.type-parent.expanded {
  background: var(--color-bg-card);
  border-left: 3px solid var(--color-transfer);
}

.type-parent.selected {
  background: rgba(var(--color-transfer-rgb, 99, 102, 241), 0.08);
}

.type-parent-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.type-name {
  font-size: 15px;
  color: var(--color-text-primary);
}

.type-parent-right {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text-tertiary);
}

.select-btn {
  font-size: 13px;
  color: var(--color-transfer);
  padding: 4px 12px;
  background: rgba(var(--color-transfer-rgb, 99, 102, 241), 0.1);
  border-radius: 12px;
}

.expand-icon {
  transition: transform 0.3s ease;
}

.expand-icon.rotated {
  transform: rotate(180deg);
}

/* 展开折叠动画 */
.slide-fade-enter-active {
  transition: all 0.3s ease;
}

.slide-fade-leave-active {
  transition: all 0.2s ease;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.slide-fade-enter-to,
.slide-fade-leave-from {
  opacity: 1;
  max-height: 200px;
}

/* 二级分类标签区域 */
.type-children {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 16px;
  background: var(--color-bg-card);
  border-top: 1px solid var(--color-border);
}

.child-tag {
  padding: 6px 14px;
  background: var(--color-bg-page);
  border-radius: 16px;
  font-size: 13px;
  color: var(--color-text-secondary);
  transition: all 0.2s;
}

.child-tag:active {
  opacity: 0.7;
}

.child-tag.selected {
  background: var(--color-transfer);
  color: #fff;
}

/* 流水弹窗 */
.flow-popup-content {
  max-height: 60vh;
  min-height: 200px;
  overflow-y: auto;
  padding: 12px 16px;
  background: var(--color-bg-page);
}

.flow-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* action-sheet 背景 */
:deep(.van-action-sheet__content) {
  background: var(--color-bg-page);
}
</style>
