<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { Close } from '@element-plus/icons-vue'
import { init, type EChartsOption } from '@shared/utils/echarts'
import type { ECharts } from 'echarts/core'
import { useThemeStore } from '@shared/stores/theme'
import type { DayTrendPoint } from './DayTrendSparkline.vue'

const props = defineProps<{
  visible: boolean
  /** yyyy-MM */
  month: string
  chartType: 'outcome' | 'income' | 'both'
  dayData: DayTrendPoint[]
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'update:month': [value: string]
  'update:chartType': [value: 'outcome' | 'income' | 'both']
}>()

const themeStore = useThemeStore()
const chartRef = ref<HTMLDivElement>()
let chart: ECharts | null = null

// ============= 当前 year / month 计算 =============
const currentYear = computed(() => parseInt(props.month.split('-')[0]))
const currentMonth = computed(() => parseInt(props.month.split('-')[1]))

const now = new Date()
const thisYear = now.getFullYear()
const thisMonth = now.getMonth() + 1

const yearOptions = computed(() => {
  const arr: number[] = []
  for (let y = thisYear; y >= 2021; y--) arr.push(y)
  return arr
})

const monthOptions = computed(() => {
  const max = currentYear.value === thisYear ? thisMonth : 12
  const arr: number[] = []
  for (let m = 1; m <= max; m++) arr.push(m)
  return arr
})

const headerSubtitle = computed(() => {
  if (props.chartType === 'both') return '日收支趋势'
  return props.chartType === 'outcome' ? '日支出趋势' : '日收入趋势'
})

// ============= 切换处理 =============
function onYearChange(year: number) {
  let m = currentMonth.value
  if (year === thisYear && m > thisMonth) m = thisMonth
  emit('update:month', `${year}-${String(m).padStart(2, '0')}`)
}

function onMonthChange(m: number) {
  emit('update:month', `${currentYear.value}-${String(m).padStart(2, '0')}`)
}

function onTypeChange(val: string | number | boolean) {
  emit('update:chartType', val as 'outcome' | 'income' | 'both')
}

function close() {
  emit('update:visible', false)
}

// ============= 图表配置 =============
const isDark = () => themeStore.effectiveTheme === 'dark'

function buildBarSeries(
  name: string,
  data: (number | null)[],
  topColor: string,
  bottomColor: string
) {
  return {
    name,
    type: 'bar' as const,
    data,
    barMaxWidth: 24,
    itemStyle: {
      color: {
        type: 'linear' as const,
        x: 0,
        y: 0,
        x2: 0,
        y2: 1,
        colorStops: [
          { offset: 0, color: topColor },
          { offset: 1, color: bottomColor },
        ],
      },
      borderRadius: [4, 4, 0, 0],
    },
    emphasis: {
      itemStyle: { color: topColor },
    },
  }
}

function getChartOption(): EChartsOption {
  const dark = isDark()
  const subTextColor = dark ? '#a3a3a3' : '#4b5563'
  const axisLineColor = dark ? '#404040' : '#d1d5db'

  const outcomeColor = dark ? '#FF6B6B' : '#F5222D'
  const incomeColor = dark ? '#69DB7C' : '#52C41A'
  const outcomeBottom = dark ? 'rgba(255, 107, 107, 0.45)' : 'rgba(245, 34, 45, 0.40)'
  const incomeBottom = dark ? 'rgba(105, 219, 124, 0.45)' : 'rgba(82, 196, 26, 0.40)'

  const days = props.dayData.map((d) => `${d.day}日`)
  const seriesList: any[] = []
  const legendData: string[] = []

  if (props.chartType !== 'income') {
    legendData.push('支出')
    seriesList.push(
      buildBarSeries(
        '支出',
        props.dayData.map((d) => d.outcome),
        outcomeColor,
        outcomeBottom
      )
    )
  }
  if (props.chartType !== 'outcome') {
    legendData.push('收入')
    seriesList.push(
      buildBarSeries(
        '收入',
        props.dayData.map((d) => d.income),
        incomeColor,
        incomeBottom
      )
    )
  }

  const showLegend = props.chartType === 'both'

  return {
    tooltip: {
      trigger: 'axis',
      confine: true,
      backgroundColor: dark ? '#333' : '#fff',
      borderColor: dark ? '#555' : '#e5e7eb',
      textStyle: { color: dark ? '#e5e5e5' : '#1f2937' },
      formatter: (params: any) => {
        const arr = Array.isArray(params) ? params : [params]
        const day = arr[0]?.axisValue
        const valid = arr.filter(
          (p: any) => p.value !== null && p.value !== undefined
        )
        if (valid.length === 0) {
          return `<div style="font-weight:600">${day}</div><div style="opacity:0.7">无记账</div>`
        }
        const lines = valid
          .map(
            (p: any) =>
              `<div style="display:flex;align-items:center;gap:8px;margin-top:4px">
                ${p.marker}
                <span>${p.seriesName}</span>
                <span style="font-weight:600;margin-left:auto">¥${Number(p.value).toFixed(2)}</span>
              </div>`
          )
          .join('')
        return `<div style="font-weight:600;margin-bottom:4px">${day}</div>${lines}`
      },
    },
    legend: showLegend
      ? {
          data: legendData,
          bottom: 8,
          itemWidth: 16,
          itemHeight: 10,
          textStyle: { fontSize: 12, color: subTextColor },
        }
      : undefined,
    grid: { left: 60, right: 30, top: 30, bottom: showLegend ? 50 : 50 },
    xAxis: {
      type: 'category',
      data: days,
      boundaryGap: true,
      axisLabel: { fontSize: 11, color: subTextColor, interval: 'auto' },
      axisLine: { lineStyle: { color: axisLineColor } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        fontSize: 11,
        color: subTextColor,
        formatter: (val: number) =>
          Math.abs(val) >= 10000 ? `${(val / 10000).toFixed(1)}万` : String(val),
      },
      axisLine: { show: false },
      splitLine: { lineStyle: { color: axisLineColor, type: 'dashed' } },
    },
    series: seriesList,
  }
}

function disposeChart() {
  chart?.dispose()
  chart = null
}

function initChart() {
  disposeChart()
  setTimeout(() => {
    if (chartRef.value) {
      chart = init(chartRef.value)
      chart.setOption(getChartOption())
    }
  }, 100)
}

function handleResize() {
  if (props.visible) chart?.resize()
}

// ============= 监听 =============
watch(
  () => props.visible,
  (val) => {
    if (val) {
      nextTick(initChart)
    } else {
      disposeChart()
    }
  }
)

watch(
  () => [props.dayData, props.chartType, themeStore.effectiveTheme],
  () => {
    if (props.visible && chart) {
      chart.setOption(getChartOption(), true)
    }
  },
  { deep: true }
)

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  disposeChart()
})
</script>

<template>
  <el-dialog
    :model-value="visible"
    :show-close="false"
    width="800px"
    top="10vh"
    class="day-trend-dialog"
    @update:model-value="(val) => emit('update:visible', val as boolean)"
  >
    <template #header>
      <div class="dialog-header">
        <div class="header-info">
          <span class="header-month">{{ currentYear }}年{{ currentMonth }}月</span>
          <span class="header-sub">{{ headerSubtitle }}</span>
        </div>
        <button class="close-btn" @click="close">
          <el-icon :size="18"><Close /></el-icon>
        </button>
      </div>
    </template>

    <div class="control-row">
      <div class="control-group">
        <span class="control-label">年份</span>
        <el-select
          :model-value="currentYear"
          size="default"
          style="width: 110px"
          @update:model-value="onYearChange"
        >
          <el-option v-for="y in yearOptions" :key="y" :label="`${y}年`" :value="y" />
        </el-select>
      </div>

      <div class="control-group">
        <span class="control-label">月份</span>
        <el-select
          :model-value="currentMonth"
          size="default"
          style="width: 90px"
          @update:model-value="onMonthChange"
        >
          <el-option v-for="m in monthOptions" :key="m" :label="`${m}月`" :value="m" />
        </el-select>
      </div>

      <div class="control-group">
        <span class="control-label">类型</span>
        <el-radio-group
          :model-value="chartType"
          size="default"
          @update:model-value="onTypeChange"
        >
          <el-radio-button value="outcome">支出</el-radio-button>
          <el-radio-button value="income">收入</el-radio-button>
          <el-radio-button value="both">全部</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <div class="chart-container">
      <div ref="chartRef" class="chart-area"></div>
    </div>
  </el-dialog>
</template>

<style scoped>
.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-info {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.header-month {
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.header-sub {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
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

.control-row {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 4px 0 16px;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-label {
  font-size: 13px;
  color: var(--color-text-tertiary);
  font-weight: 500;
}

.chart-container {
  padding: 4px 0 8px;
}

.chart-area {
  width: 100%;
  height: 400px;
}
</style>

<style>
.day-trend-dialog {
  --el-dialog-bg-color: var(--color-bg-card);
  border-radius: 16px !important;
}

.day-trend-dialog .el-dialog__header {
  padding: 20px 24px 16px;
  margin: 0;
  border-bottom: 1px solid var(--color-border-light);
}

.day-trend-dialog .el-dialog__body {
  padding: 16px 24px 24px;
}

html.dark .day-trend-dialog {
  --el-dialog-bg-color: #1e1e1e;
}

html.dark .day-trend-dialog .el-dialog__header {
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .day-trend-dialog .close-btn {
  background: rgba(60, 60, 60, 0.4);
}

html.dark .day-trend-dialog .close-btn:hover {
  background: rgba(80, 80, 80, 0.6);
}
</style>
