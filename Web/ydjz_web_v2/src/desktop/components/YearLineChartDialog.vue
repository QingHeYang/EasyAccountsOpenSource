<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { Close } from '@element-plus/icons-vue'
import { init, type EChartsOption } from '@shared/utils/echarts'
import type { ECharts } from 'echarts/core'
import type { MonthData } from '@shared/api/analysis'

const props = defineProps<{
  visible: boolean
  year: number
  typeName: string
  monthData: MonthData[]
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
}>()

// 图表实例
const chartRef = ref<HTMLDivElement>()
let chart: ECharts | null = null

// 检测暗黑模式
const isDark = () => document.documentElement.classList.contains('dark')

// 获取图表颜色
const getTextColor = () => isDark() ? '#e5e5e5' : '#1f2937'
const getSubTextColor = () => isDark() ? '#a3a3a3' : '#4b5563'
const getAxisLineColor = () => isDark() ? '#404040' : '#d1d5db'

// 关闭
function close() {
  emit('update:visible', false)
}

// 生成折线图配置
function getChartOption(): EChartsOption {
  const subTextColor = getSubTextColor()
  const axisLineColor = getAxisLineColor()

  const months = props.monthData.map(m => `${m.month}月`)
  const incomes = props.monthData.map(m => parseFloat(m.income) || 0)
  const outcomes = props.monthData.map(m => parseFloat(m.outcome) || 0)

  // 判断是否有收入/支出数据
  const hasIncome = incomes.some(v => v > 0)
  const hasOutcome = outcomes.some(v => v > 0)

  const series: any[] = []
  const legendData: string[] = []

  if (hasIncome) {
    legendData.push('收入')
    series.push({
      name: '收入',
      type: 'line',
      data: incomes,
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      itemStyle: { color: '#10b981' },
      lineStyle: { width: 2.5 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(16, 185, 129, 0.25)' },
            { offset: 1, color: 'rgba(16, 185, 129, 0.02)' },
          ],
        },
      },
    })
  }

  if (hasOutcome) {
    legendData.push('支出')
    series.push({
      name: '支出',
      type: 'line',
      data: outcomes,
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      itemStyle: { color: '#ef4444' },
      lineStyle: { width: 2.5 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(239, 68, 68, 0.25)' },
            { offset: 1, color: 'rgba(239, 68, 68, 0.02)' },
          ],
        },
      },
    })
  }

  return {
    tooltip: {
      trigger: 'axis',
      confine: true,
      backgroundColor: isDark() ? '#333' : '#fff',
      borderColor: isDark() ? '#555' : '#e5e7eb',
      textStyle: {
        color: isDark() ? '#e5e5e5' : '#1f2937',
      },
      formatter: (params: any) => {
        let result = `<div style="font-weight: 600; margin-bottom: 8px;">${params[0].axisValue}</div>`
        params.forEach((item: any) => {
          result += `<div style="display: flex; align-items: center; gap: 8px; margin: 4px 0;">
            ${item.marker}
            <span>${item.seriesName}</span>
            <span style="font-weight: 600;">¥${item.value.toFixed(2)}</span>
          </div>`
        })
        return result
      },
    },
    legend: {
      data: legendData,
      bottom: 16,
      itemWidth: 20,
      itemHeight: 12,
      textStyle: { fontSize: 13, color: subTextColor },
    },
    grid: {
      left: 60,
      right: 40,
      top: 40,
      bottom: 80,
    },
    xAxis: {
      type: 'category',
      data: months,
      axisLabel: { fontSize: 12, color: subTextColor },
      axisLine: { lineStyle: { color: axisLineColor } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        fontSize: 11,
        color: subTextColor,
        formatter: (val: number) => {
          if (Math.abs(val) >= 10000) {
            return (val / 10000).toFixed(1) + '万'
          }
          return val.toString()
        },
      },
      axisLine: { show: false },
      splitLine: { lineStyle: { color: axisLineColor, type: 'dashed' } },
    },
    series,
  }
}

// 销毁图表
function disposeChart() {
  if (chart) {
    chart.dispose()
    chart = null
  }
}

// 初始化图表
function initChart() {
  disposeChart()

  setTimeout(() => {
    if (chartRef.value) {
      chart = init(chartRef.value)
      chart.setOption(getChartOption())
    }
  }, 100)
}

// 监听显示状态
watch(() => props.visible, (val) => {
  if (val) {
    nextTick(() => {
      initChart()
    })
  } else {
    disposeChart()
  }
})

// 处理窗口大小变化
function handleResize() {
  if (props.visible) {
    chart?.resize()
  }
}

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
    class="year-chart-dialog"
    @update:model-value="emit('update:visible', $event)"
  >
    <template #header>
      <div class="dialog-header">
        <div class="header-info">
          <span class="header-year">{{ year }}年</span>
          <span class="header-type">{{ typeName }}</span>
        </div>
        <button class="close-btn" @click="close">
          <el-icon :size="18"><Close /></el-icon>
        </button>
      </div>
    </template>

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

.header-year {
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.header-type {
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

.chart-container {
  padding: 8px 0 16px;
}

.chart-area {
  width: 100%;
  height: 400px;
}
</style>

<!-- 全局样式 -->
<style>
.year-chart-dialog {
  --el-dialog-bg-color: var(--color-bg-card);
  border-radius: 16px !important;
}

.year-chart-dialog .el-dialog__header {
  padding: 20px 24px 16px;
  margin: 0;
  border-bottom: 1px solid var(--color-border-light);
}

.year-chart-dialog .el-dialog__body {
  padding: 16px 24px 24px;
}

html.dark .year-chart-dialog {
  --el-dialog-bg-color: #1e1e1e;
}

html.dark .year-chart-dialog .el-dialog__header {
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .close-btn {
  background: rgba(60, 60, 60, 0.4);
}

html.dark .close-btn:hover {
  background: rgba(80, 80, 80, 0.6);
}
</style>
