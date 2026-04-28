<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
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
  dayData: DayTrendPoint[]
  chartType: 'outcome' | 'income' | 'both'
}>()

const emit = defineEmits<{
  click: []
}>()

const themeStore = useThemeStore()
const chartRef = ref<HTMLDivElement>()
let chart: ECharts | null = null

const title = computed(() => {
  if (props.chartType === 'both') return '日收支趋势'
  return props.chartType === 'outcome' ? '日支出趋势' : '日收入趋势'
})

const isDark = () => themeStore.effectiveTheme === 'dark'

function buildLineSeries(
  name: string,
  data: (number | null)[],
  color: string,
  fillTop: string,
  fillBottom: string
) {
  return {
    name,
    type: 'line' as const,
    data,
    smooth: false,
    symbol: 'none' as const,
    connectNulls: false,
    lineStyle: { color, width: 2 },
    itemStyle: { color },
    areaStyle: {
      color: {
        type: 'linear' as const,
        x: 0,
        y: 0,
        x2: 0,
        y2: 1,
        colorStops: [
          { offset: 0, color: fillTop },
          { offset: 1, color: fillBottom },
        ],
      },
    },
  }
}

function getOption(): EChartsOption {
  const dark = isDark()

  const outcomeColor = dark ? '#FF6B6B' : '#F5222D'
  const incomeColor = dark ? '#69DB7C' : '#52C41A'
  const outcomeFillTop = dark ? 'rgba(255, 107, 107, 0.30)' : 'rgba(245, 34, 45, 0.18)'
  const outcomeFillBottom = dark ? 'rgba(255, 107, 107, 0.02)' : 'rgba(245, 34, 45, 0.02)'
  const incomeFillTop = dark ? 'rgba(105, 219, 124, 0.30)' : 'rgba(82, 196, 26, 0.18)'
  const incomeFillBottom = dark ? 'rgba(105, 219, 124, 0.02)' : 'rgba(82, 196, 26, 0.02)'

  const seriesList: any[] = []
  if (props.chartType !== 'income') {
    seriesList.push(
      buildLineSeries(
        '支出',
        props.dayData.map((d) => d.outcome),
        outcomeColor,
        outcomeFillTop,
        outcomeFillBottom
      )
    )
  }
  if (props.chartType !== 'outcome') {
    seriesList.push(
      buildLineSeries(
        '收入',
        props.dayData.map((d) => d.income),
        incomeColor,
        incomeFillTop,
        incomeFillBottom
      )
    )
  }

  return {
    grid: { left: 0, right: 0, top: 4, bottom: 4 },
    xAxis: {
      type: 'category',
      show: false,
      data: props.dayData.map((d) => String(d.day)),
      boundaryGap: false,
    },
    yAxis: { type: 'value', show: false },
    tooltip: {
      trigger: 'axis',
      confine: true,
      backgroundColor: dark ? '#333' : '#fff',
      borderColor: dark ? '#555' : '#e5e7eb',
      textStyle: { color: dark ? '#e5e5e5' : '#1f2937', fontSize: 12 },
      formatter: (params: any) => {
        const arr = Array.isArray(params) ? params : [params]
        const day = arr[0]?.name
        const lines = arr
          .filter((p: any) => p.value !== null && p.value !== undefined)
          .map((p: any) => `${p.marker} ${p.seriesName} ¥${Number(p.value).toFixed(2)}`)
        if (lines.length === 0) return `${day}日 · 无记账`
        return `<div style="font-weight:600;margin-bottom:4px">${day}日</div>${lines.join('<br/>')}`
      },
    },
    series: seriesList,
  }
}

function refreshChart() {
  if (!chartRef.value) return
  if (!chart) chart = init(chartRef.value)
  chart.setOption(getOption(), true)
}

function handleResize() {
  chart?.resize()
}

watch(
  () => [props.dayData, props.chartType, themeStore.effectiveTheme],
  () => nextTick(refreshChart),
  { deep: true }
)

onMounted(() => {
  nextTick(refreshChart)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div class="day-trend-spark" @click="emit('click')">
    <div class="spark-header">
      <span class="spark-title">{{ title }}</span>
    </div>
    <div ref="chartRef" class="spark-chart"></div>
  </div>
</template>

<style scoped>
.day-trend-spark {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  padding: 12px 16px 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.day-trend-spark:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.spark-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.spark-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.spark-chart {
  width: 100%;
  height: 64px;
}
</style>

<style>
html.dark .day-trend-spark {
  background: rgba(40, 40, 40, 0.6);
  border-color: rgba(255, 255, 255, 0.1);
}
</style>
