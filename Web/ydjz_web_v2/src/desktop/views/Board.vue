<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowRight, Grid, List } from '@element-plus/icons-vue'
import { homeApi, type HomeInfo } from '@shared/api/home'
import { init, type EChartsOption } from '@shared/utils/echarts'
import type { ECharts } from 'echarts/core'

const router = useRouter()

// 数据
const loading = ref(false)
const homeInfo = ref<HomeInfo | null>(null)
const currentYear = new Date().getFullYear()
const chooseYear = ref(currentYear)
const minYear = 2021

// 布局模式：list | grid
const layoutMode = ref<'list' | 'grid'>('list')

function toggleLayout() {
  layoutMode.value = layoutMode.value === 'list' ? 'grid' : 'list'
}

// 图表相关
const chartRef = ref<HTMLDivElement>()
let chartInstance: ECharts | null = null

// 检测暗黑模式
const isDark = () => document.documentElement.classList.contains('dark')
const getTextColor = () => isDark() ? '#e5e5e5' : '#1f2937'
const getSubTextColor = () => isDark() ? '#a3a3a3' : '#4b5563'
const getAxisLineColor = () => isDark() ? '#404040' : '#d1d5db'

// 生成趋势图配置
function getChartOption(): EChartsOption {
  const monthDetails = homeInfo.value?.monthDetails || []
  const months = monthDetails.map(m => `${m.month}月`)
  const incomes = monthDetails.map(m => parseFloat(m.income) || 0)
  const outcomes = monthDetails.map(m => parseFloat(m.outcome) || 0)
  const balances = monthDetails.map(m => parseFloat(m.balance) || 0)
  const textColor = getTextColor()
  const subTextColor = getSubTextColor()
  const axisLineColor = getAxisLineColor()

  return {
    title: {
      text: `${chooseYear.value}年度趋势`,
      left: 'center',
      top: 16,
      textStyle: {
        fontSize: 16,
        fontWeight: 600,
        color: textColor,
      },
    },
    tooltip: {
      trigger: 'axis',
      confine: true,
    },
    legend: {
      data: ['收入', '支出', '结余'],
      bottom: 16,
      itemWidth: 20,
      itemHeight: 12,
      textStyle: { fontSize: 13, color: subTextColor },
    },
    grid: {
      left: 60,
      right: 30,
      top: 60,
      bottom: 60,
    },
    xAxis: {
      type: 'category',
      data: months,
      axisLabel: { fontSize: 12, color: subTextColor },
      axisLine: { lineStyle: { color: axisLineColor } },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        fontSize: 12,
        color: subTextColor,
        formatter: (val: number) => {
          if (Math.abs(val) >= 10000) {
            return (val / 10000).toFixed(1) + '万'
          }
          return val.toString()
        },
      },
      axisLine: { lineStyle: { color: axisLineColor } },
      splitLine: { lineStyle: { color: axisLineColor, opacity: 0.5 } },
    },
    series: [
      {
        name: '收入',
        type: 'line',
        data: incomes,
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        itemStyle: { color: '#10b981' },
        lineStyle: { width: 2 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(16, 185, 129, 0.3)' },
              { offset: 1, color: 'rgba(16, 185, 129, 0)' },
            ],
          },
        },
      },
      {
        name: '支出',
        type: 'line',
        data: outcomes,
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        itemStyle: { color: '#ef4444' },
        lineStyle: { width: 2 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(239, 68, 68, 0.3)' },
              { offset: 1, color: 'rgba(239, 68, 68, 0)' },
            ],
          },
        },
      },
      {
        name: '结余',
        type: 'line',
        data: balances,
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        itemStyle: { color: '#3b82f6' },
        lineStyle: { width: 2 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
              { offset: 1, color: 'rgba(59, 130, 246, 0)' },
            ],
          },
        },
      },
    ],
  }
}

// 初始化/更新图表
function initChart() {
  if (!chartRef.value) return

  if (!chartInstance) {
    chartInstance = init(chartRef.value)
  }

  chartInstance.setOption(getChartOption())
}

// 监听数据变化更新图表
watch(() => homeInfo.value?.monthDetails, () => {
  nextTick(() => initChart())
}, { deep: true })

// 监听窗口大小变化
function handleResize() {
  chartInstance?.resize()
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  chartInstance = null
})

// 获取首页数据
async function fetchHomeInfo() {
  loading.value = true
  try {
    const res = await homeApi.getHomeInfoByYear(chooseYear.value)
    if (res.data.code === 0) {
      homeInfo.value = res.data.data
      // 数据加载后初始化图表
      nextTick(() => initChart())
    }
  } catch (err) {
    console.error('获取首页数据失败:', err)
  } finally {
    loading.value = false
  }
}

// 年份切换
function onYearPrev() {
  if (chooseYear.value <= minYear) {
    ElMessage.warning('已经到最前了')
    return
  }
  chooseYear.value--
  fetchHomeInfo()
}

function onYearNext() {
  if (chooseYear.value >= currentYear) {
    ElMessage.warning('已经到最后了')
    return
  }
  chooseYear.value++
  fetchHomeInfo()
}

// 格式化金额
function formatAmount(amount: string | number | undefined): string {
  if (!amount) return '0.00'
  const num = typeof amount === 'string' ? parseFloat(amount) : amount
  if (Math.abs(num) >= 10000) {
    return (num / 10000).toFixed(2) + '万'
  }
  return num.toFixed(2)
}

// 判断结余是否为负数
function isNegativeBalance(balance: string | number | undefined): boolean {
  if (!balance) return false
  const num = typeof balance === 'string' ? parseFloat(balance) : balance
  return num < 0
}

// 计算最值月份
const maxIncomeMonth = computed(() => {
  if (!homeInfo.value?.monthDetails?.length) return null
  let max = homeInfo.value.monthDetails[0]
  for (const item of homeInfo.value.monthDetails) {
    if (parseFloat(item.income) > parseFloat(max.income)) {
      max = item
    }
  }
  return parseFloat(max.income) > 0 ? max.month : null
})

const maxExpenseMonth = computed(() => {
  if (!homeInfo.value?.monthDetails?.length) return null
  let max = homeInfo.value.monthDetails[0]
  for (const item of homeInfo.value.monthDetails) {
    if (parseFloat(item.outcome) > parseFloat(max.outcome)) {
      max = item
    }
  }
  return parseFloat(max.outcome) > 0 ? max.month : null
})

const maxBalanceMonth = computed(() => {
  if (!homeInfo.value?.monthDetails?.length) return null
  let max = homeInfo.value.monthDetails[0]
  for (const item of homeInfo.value.monthDetails) {
    if (parseFloat(item.balance) > parseFloat(max.balance)) {
      max = item
    }
  }
  return parseFloat(max.balance) > 0 ? max.month : null
})

function isMaxIncome(month: string) {
  return month === maxIncomeMonth.value
}

function isMaxExpense(month: string) {
  return month === maxExpenseMonth.value
}

function isMaxBalance(month: string) {
  return month === maxBalanceMonth.value
}

// 账户列表
const accountList = computed(() => {
  if (!homeInfo.value?.accounts) return []
  return homeInfo.value.accounts.map(acc => {
    // exemptAsset 为 0 或 0.00 时不显示
    const exempt = parseFloat(acc.exemptAsset || '0')
    const hasExempt = exempt !== 0
    return {
      ...acc,
      realAsset: hasExempt
        ? (parseFloat(acc.accountAsset) - exempt).toFixed(2)
        : null
    }
  })
})

// 是否显示净资产（netAsset 与 totalAsset 不相等时显示）
const showNetAsset = computed(() => {
  if (!homeInfo.value) return false
  return homeInfo.value.netAsset !== homeInfo.value.totalAsset
})

// 跳转
function toFlow(month: string) {
  const monthStr = `${chooseYear.value}-${month.toString().padStart(2, '0')}`
  router.push({ path: '/flow', query: { month: monthStr } })
}

onMounted(() => {
  fetchHomeInfo()
})
</script>

<template>
  <div class="board-page" v-loading="loading">
    <h1 class="page-title">总览</h1>

    <!-- 主布局容器 -->
    <div class="board-layout">
      <!-- 左列 -->
      <div class="left-column">
        <!-- 总资产卡片 -->
        <div class="asset-card">
          <div class="asset-label">总资产</div>
          <div class="asset-amount">¥ {{ homeInfo?.totalAsset || '0.00' }}</div>
          <div class="asset-net" v-if="showNetAsset">净资产 ¥ {{ homeInfo?.netAsset || '0.00' }}</div>
        </div>

        <!-- 年度统计卡片 -->
        <div class="year-card">
          <div class="year-header">
            <el-button :icon="ArrowLeft" circle size="small" @click="onYearPrev" />
            <span class="year-title">{{ chooseYear }}年度</span>
            <el-button :icon="ArrowRight" circle size="small" @click="onYearNext" />
          </div>
          <div class="year-stats">
            <div class="stat-item">
              <span class="stat-label">收入</span>
              <span class="stat-value income">{{ formatAmount(homeInfo?.yearIncome) }}</span>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
              <span class="stat-label">支出</span>
              <span class="stat-value expense">{{ formatAmount(homeInfo?.yearOutCome) }}</span>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
              <span class="stat-label">结余</span>
              <span class="stat-value balance">{{ formatAmount(homeInfo?.yearBalance) }}</span>
            </div>
          </div>
        </div>

        <!-- 月度概览 -->
        <div class="month-section">
          <div class="section-header">
            <h2 class="section-title">月度概览</h2>
            <el-button
              :icon="layoutMode === 'list' ? Grid : List"
              circle
              size="small"
              @click="toggleLayout"
            />
          </div>

          <!-- List 布局 -->
          <div class="month-list" v-if="homeInfo?.monthDetails?.length && layoutMode === 'list'">
            <div
              class="month-row"
              v-for="item in homeInfo.monthDetails"
              :key="item.month"
              @click="toFlow(item.month)"
            >
              <span class="month-label">{{ item.month }}月</span>
              <span class="stat-num income">
                <span :class="{ 'tag-max': isMaxIncome(item.month) }">+{{ formatAmount(item.income) }}</span>
              </span>
              <span class="stat-num expense">
                <span :class="{ 'tag-max': isMaxExpense(item.month) }">-{{ formatAmount(item.outcome) }}</span>
              </span>
              <span class="stat-num balance">
                <span :class="{ 'tag-max': isMaxBalance(item.month), 'tag-negative': isNegativeBalance(item.balance) }">
                  {{ formatAmount(item.balance) }}
                </span>
              </span>
            </div>
          </div>

          <!-- Grid 布局 -->
          <div class="month-grid" v-else-if="homeInfo?.monthDetails?.length && layoutMode === 'grid'">
            <div
              class="grid-item"
              v-for="item in homeInfo.monthDetails"
              :key="item.month"
              @click="toFlow(item.month)"
            >
              <div class="grid-month">{{ item.month }}月</div>
              <div class="grid-stats">
                <div class="grid-stat income">
                  <span class="grid-label">收入</span>
                  <span class="grid-value">
                    <span :class="{ 'tag-max': isMaxIncome(item.month) }">+{{ formatAmount(item.income) }}</span>
                  </span>
                </div>
                <div class="grid-stat expense">
                  <span class="grid-label">支出</span>
                  <span class="grid-value">
                    <span :class="{ 'tag-max': isMaxExpense(item.month) }">-{{ formatAmount(item.outcome) }}</span>
                  </span>
                </div>
                <div class="grid-stat balance">
                  <span class="grid-label">结余</span>
                  <span class="grid-value">
                    <span :class="{ 'tag-max': isMaxBalance(item.month), 'tag-negative': isNegativeBalance(item.balance) }">
                      {{ formatAmount(item.balance) }}
                    </span>
                  </span>
                </div>
              </div>
            </div>
          </div>

          <el-empty v-else description="暂无数据" :image-size="60" />
        </div>
      </div>

      <!-- 右列 -->
      <div class="right-column">
        <!-- 年度趋势图表（与左侧总资产+年度卡片对齐） -->
        <div class="chart-card">
          <div ref="chartRef" class="chart-container"></div>
        </div>

        <!-- 账户明细 -->
        <div class="account-section">
          <h2 class="section-title">账户明细</h2>
          <div class="account-list" v-if="accountList.length">
            <div
              class="account-item"
              v-for="acc in accountList"
              :key="acc.id"
            >
              <div class="account-info">
                <div class="account-name">{{ acc.accountName }}</div>
                <div class="account-note" v-if="acc.note">{{ acc.note }}</div>
              </div>
              <div class="account-amount">
                <div class="account-asset">¥ {{ acc.accountAsset }}</div>
                <div class="account-real" v-if="acc.realAsset">净 ¥ {{ acc.realAsset }}</div>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无账户" :image-size="60" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.board-page {
  padding: 20px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 24px 0;
}

/* 主布局：左右两列 */
.board-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.left-column,
.right-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 420px;
}

/* 总资产卡片 */
.asset-card {
  background: linear-gradient(135deg, var(--color-transfer) 0%, #5b9cf8 100%);
  border-radius: 20px;
  padding: 28px;
  color: #fff;
}

.asset-label {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 12px;
}

.asset-amount {
  font-size: 36px;
  font-weight: 700;
  word-break: break-all;
}

.asset-net {
  font-size: 14px;
  opacity: 0.85;
  margin-top: 8px;
}

/* 年度统计卡片 */
.year-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.year-header {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.year-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.year-stats {
  display: flex;
  justify-content: space-around;
  align-items: center;
}

.stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.stat-divider {
  width: 1px;
  height: 50px;
  background: var(--color-border);
}

.stat-label {
  font-size: 14px;
  color: var(--color-text-tertiary);
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
}

.stat-value.income {
  color: var(--color-income);
}

.stat-value.expense {
  color: var(--color-expense);
}

.stat-value.balance {
  color: var(--color-transfer);
}

/* 图表卡片 - 高度与左侧总资产+年度卡片对齐 */
.chart-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  /* 高度 = 总资产卡片高度 + 年度卡片高度 + gap */
  height: calc(116px + 166px + 20px);
  display: flex;
  flex-direction: column;
}

.chart-container {
  flex: 1;
  width: 100%;
  min-height: 0;
}

/* 月度概览 */
.month-section {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 20px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  flex: 1;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}

/* 月度列表 */
.month-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.month-row {
  display: grid;
  grid-template-columns: 50px 1fr 1fr 1fr;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.month-row:hover {
  background: var(--color-bg-page);
}

.month-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.stat-num {
  font-size: 13px;
  font-weight: 500;
  text-align: right;
}

.stat-num.income {
  color: var(--color-income);
}

.stat-num.expense {
  color: var(--color-expense);
}

.stat-num.balance {
  color: var(--color-text-secondary);
}

/* 最高值标签 - 贴着文本 */
.stat-num .tag-max {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  color: #fff;
}

.stat-num.income .tag-max {
  background: var(--color-income);
}

.stat-num.expense .tag-max {
  background: var(--color-expense);
}

.stat-num.balance .tag-max {
  background: var(--color-transfer);
}

/* 负数结余 - 贴着文本 */
.stat-num .tag-negative {
  display: inline-block;
  border: 1px solid var(--color-expense);
  border-radius: 4px;
  padding: 1px 5px;
}

/* tag-max 和 tag-negative 同时存在时，优先显示 tag-max */
.stat-num .tag-max.tag-negative {
  border: none;
  padding: 2px 6px;
}

/* Grid 布局 */
.month-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.grid-item {
  background: var(--color-bg-page);
  border-radius: 12px;
  padding: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.grid-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.grid-month {
  font-size: 16px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 10px;
}

.grid-stats {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.grid-stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.grid-label {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.grid-value {
  font-size: 13px;
  font-weight: 600;
}

.grid-stat.income .grid-value {
  color: var(--color-income);
}

.grid-stat.expense .grid-value {
  color: var(--color-expense);
}

.grid-stat.balance .grid-value {
  color: var(--color-text-secondary);
}

/* Grid 标签样式 - 贴着文本 */
.grid-value .tag-max {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  color: #fff;
}

.grid-stat.income .grid-value .tag-max {
  background: var(--color-income);
}

.grid-stat.expense .grid-value .tag-max {
  background: var(--color-expense);
}

.grid-stat.balance .grid-value .tag-max {
  background: var(--color-transfer);
}

.grid-value .tag-negative {
  display: inline-block;
  border: 1px solid var(--color-expense);
  border-radius: 4px;
  padding: 1px 4px;
}

.grid-value .tag-max.tag-negative {
  border: none;
  padding: 2px 6px;
}

/* 账户明细 */
.account-section {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 20px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  flex: 1;
}

.account-section .section-title {
  margin-bottom: 16px;
}

.account-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.account-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: var(--color-bg-page);
  border-radius: 12px;
}

.account-name {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.account-note {
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-top: 4px;
}

.account-amount {
  text-align: right;
}

.account-asset {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.account-real {
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-top: 2px;
}
</style>

<!-- 暗色模式 -->
<style>
html.dark .year-card,
html.dark .month-section,
html.dark .chart-card,
html.dark .account-section {
  background: rgba(40, 40, 40, 0.6);
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .grid-item,
html.dark .account-item {
  background: rgba(50, 50, 50, 0.6);
}

html.dark .grid-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

html.dark .month-row:hover {
  background: rgba(50, 50, 50, 0.6);
}
</style>
