<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { init, type EChartsOption } from '@shared/utils/echarts'
import type { ECharts } from 'echarts/core'
import { useThemeStore } from '@shared/stores/theme'

export interface DayTrendPoint {
  day: number
  date: string
  income: number | null
  outcome: number | null
}

const props = defineProps<{
  show: boolean
  /** yyyy-MM */
  month: string
  chartType: 'outcome' | 'income' | 'both'
  dayData: DayTrendPoint[]
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  'update:month': [value: string]
  'update:chartType': [value: 'outcome' | 'income' | 'both']
}>()

const themeStore = useThemeStore()
const chartRef = ref<HTMLDivElement>()
let chart: ECharts | null = null

// ============= 当前 year / month =============
const currentYear = computed(() => parseInt(props.month.split('-')[0]))
const currentMonth = computed(() => parseInt(props.month.split('-')[1]))

const now = new Date()
const thisYear = now.getFullYear()
const thisMonth = now.getMonth() + 1

const isCurrentMonth = computed(
  () => currentYear.value === thisYear && currentMonth.value === thisMonth
)
const isMinMonth = computed(
  () => currentYear.value === 2021 && currentMonth.value === 1
)

const headerSubtitle = computed(() => {
  if (props.chartType === 'both') return '日收支'
  return props.chartType === 'outcome' ? '日支出' : '日收入'
})

// ============= 切换处理 =============
function gotoPrev() {
  if (isMinMonth.value) return
  let y = currentYear.value
  let m = currentMonth.value - 1
  if (m === 0) {
    y -= 1
    m = 12
  }
  emit('update:month', `${y}-${String(m).padStart(2, '0')}`)
}

function gotoNext() {
  if (isCurrentMonth.value) return
  let y = currentYear.value
  let m = currentMonth.value + 1
  if (m === 13) {
    y += 1
    m = 1
  }
  emit('update:month', `${y}-${String(m).padStart(2, '0')}`)
}

function gotoPrevYear() {
  if (currentYear.value <= 2021) return
  const y = currentYear.value - 1
  emit('update:month', `${y}-${String(currentMonth.value).padStart(2, '0')}`)
}

function gotoNextYear() {
  if (currentYear.value >= thisYear) return
  let y = currentYear.value + 1
  let m = currentMonth.value
  // 切到当年时，如果当前月份超过本月，自动收敛到本月
  if (y === thisYear && m > thisMonth) m = thisMonth
  emit('update:month', `${y}-${String(m).padStart(2, '0')}`)
}

function setChartType(t: 'outcome' | 'income' | 'both') {
  if (t === props.chartType) return
  emit('update:chartType', t)
}

function close() {
  emit('update:show', false)
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
    barMaxWidth: 22,
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

  const days = props.dayData.map((d) => `${d.day}`)
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
      textStyle: { color: dark ? '#e5e5e5' : '#1f2937', fontSize: 12 },
      formatter: (params: any) => {
        const arr = Array.isArray(params) ? params : [params]
        const day = arr[0]?.axisValue
        const valid = arr.filter(
          (p: any) => p.value !== null && p.value !== undefined
        )
        if (valid.length === 0) {
          return `${day}日 · 无记账`
        }
        const lines = valid
          .map(
            (p: any) =>
              `<div style="display:flex;align-items:center;gap:6px;margin-top:2px">
                ${p.marker}
                <span>${p.seriesName}</span>
                <span style="font-weight:600;margin-left:auto">¥${Number(p.value).toFixed(2)}</span>
              </div>`
          )
          .join('')
        return `<div style="font-weight:600;margin-bottom:2px">${day}日</div>${lines}`
      },
    },
    legend: showLegend
      ? {
          data: legendData,
          bottom: 8,
          itemWidth: 14,
          itemHeight: 8,
          textStyle: { fontSize: 11, color: subTextColor },
        }
      : undefined,
    grid: { left: 50, right: 24, top: 24, bottom: showLegend ? 50 : 30 },
    xAxis: {
      type: 'category',
      data: days,
      boundaryGap: true,
      axisLabel: { fontSize: 10, color: subTextColor, interval: 'auto' },
      axisLine: { lineStyle: { color: axisLineColor } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        fontSize: 10,
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
  if (props.show) chart?.resize()
}

watch(
  () => props.show,
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
    if (props.show && chart) {
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
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="trend-overlay" @click.self="close">
        <div class="trend-container">
          <div class="trend-body">
            <!-- 左侧图表区 -->
            <div class="chart-left">
              <div ref="chartRef" class="chart-area"></div>
            </div>

            <!-- 右侧信息面板 -->
            <div class="info-panel">
              <div class="info-top">
                <div class="info-year-row">
                  <div class="year-arrow" :class="{ disabled: currentYear <= 2021 }" @click="gotoPrevYear">
                    <van-icon name="arrow-left" size="14" />
                  </div>
                  <div class="info-year">{{ currentYear }}</div>
                  <div class="year-arrow" :class="{ disabled: currentYear >= thisYear }" @click="gotoNextYear">
                    <van-icon name="arrow" size="14" />
                  </div>
                </div>
                <div class="info-month">{{ currentMonth }}月 · {{ headerSubtitle }}</div>
              </div>

              <div class="info-month-row">
                <div class="month-arrow" :class="{ disabled: isMinMonth }" @click="gotoPrev">
                  <van-icon name="arrow-left" size="16" />
                </div>
                <div class="month-arrow" :class="{ disabled: isCurrentMonth }" @click="gotoNext">
                  <van-icon name="arrow" size="16" />
                </div>
              </div>

              <div class="info-chips">
                <div
                  class="info-chip"
                  :class="{ active: chartType === 'outcome' }"
                  @click="setChartType('outcome')"
                >支出</div>
                <div
                  class="info-chip"
                  :class="{ active: chartType === 'income' }"
                  @click="setChartType('income')"
                >收入</div>
                <div
                  class="info-chip"
                  :class="{ active: chartType === 'both' }"
                  @click="setChartType('both')"
                >全部</div>
              </div>

              <div class="close-btn" @click="close">
                <van-icon name="cross" size="16" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.trend-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  overflow: hidden;
}

.trend-container {
  /* 竖屏旋转 90deg：让横长图表占满屏幕 */
  position: absolute;
  top: 50%;
  left: 50%;
  width: 100vh;
  height: 100vw;
  transform: translate(-50%, -50%) rotate(90deg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--color-bg-card);
}

@media (orientation: landscape) {
  .trend-container {
    width: 100vw;
    height: 100vh;
    transform: translate(-50%, -50%);
  }
}

.trend-body {
  flex: 1;
  display: flex;
  min-height: 0;
  padding: 12px 24px 24px 12px;
  gap: 12px;
}

.chart-left {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chart-area {
  flex: 1;
  min-height: 0;
}

/* 右侧信息面板 */
.info-panel {
  width: 130px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-page);
  border-radius: 12px;
  overflow: hidden;
  padding: 12px;
  position: relative;
}

.info-top {
  margin-bottom: 12px;
}

.info-year-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.year-arrow {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-card);
  border-radius: 6px;
  color: var(--color-text-secondary);
}

.year-arrow.disabled {
  opacity: 0.3;
  pointer-events: none;
}

.year-arrow:active {
  opacity: 0.7;
}

.info-year {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.info-month {
  font-size: 13px;
  color: var(--color-text-secondary);
  text-align: center;
}

.info-month-row {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
}

.month-arrow {
  flex: 1;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-card);
  border-radius: 8px;
  color: var(--color-text-primary);
}

.month-arrow.disabled {
  opacity: 0.3;
  pointer-events: none;
}

.month-arrow:active {
  opacity: 0.7;
}

.info-chips {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-chip {
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-card);
  color: var(--color-text-secondary);
  border-radius: 8px;
  font-size: 13px;
  transition: all 0.15s;
}

.info-chip.active {
  background: var(--color-transfer);
  color: #fff;
  font-weight: 600;
}

.info-chip:active {
  opacity: 0.85;
}

.close-btn {
  position: absolute;
  bottom: 12px;
  left: 12px;
  right: 12px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-card);
  border-radius: 8px;
  color: var(--color-text-secondary);
}

.close-btn:active {
  opacity: 0.7;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
