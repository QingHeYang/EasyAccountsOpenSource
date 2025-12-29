<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { init, type EChartsOption } from '@shared/utils/echarts'
import type { ECharts } from 'echarts/core'
import type { MonthData } from '@shared/api/analysis'

const props = defineProps<{
  show: boolean
  year: number
  typeName: string
  monthData: MonthData[]
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
}>()

// 图表实例
const chartRef = ref<HTMLDivElement>()
let chart: ECharts | null = null

// 检测暗黑模式
const isDark = () => document.documentElement.classList.contains('dark')

// 获取图表文字颜色
const getTextColor = () => isDark() ? '#e5e5e5' : '#1f2937'
const getSubTextColor = () => isDark() ? '#a3a3a3' : '#4b5563'
const getAxisLineColor = () => isDark() ? '#404040' : '#d1d5db'

// 关闭
function close() {
  emit('update:show', false)
}

// 生成折线图配置
function getChartOption(): EChartsOption {
  const textColor = getTextColor()
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
      symbolSize: 6,
      itemStyle: { color: '#10b981' },
      lineStyle: { width: 2 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(16, 185, 129, 0.3)' },
            { offset: 1, color: 'rgba(16, 185, 129, 0.05)' },
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
      symbolSize: 6,
      itemStyle: { color: '#ef4444' },
      lineStyle: { width: 2 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(239, 68, 68, 0.3)' },
            { offset: 1, color: 'rgba(239, 68, 68, 0.05)' },
          ],
        },
      },
    })
  }

  return {
    tooltip: {
      trigger: 'axis',
      confine: true,
      formatter: (params: any) => {
        let result = params[0].axisValue
        params.forEach((item: any) => {
          result += `<br/>${item.marker}${item.seriesName}: ¥${item.value.toFixed(2)}`
        })
        return result
      },
    },
    legend: {
      data: legendData,
      bottom: 12,
      itemWidth: 16,
      itemHeight: 10,
      textStyle: { fontSize: 12, color: subTextColor },
    },
    grid: {
      left: 50,
      right: 24,
      top: 24,
      bottom: 70,
    },
    xAxis: {
      type: 'category',
      data: months,
      axisLabel: { fontSize: 11, color: subTextColor },
      axisLine: { lineStyle: { color: axisLineColor } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        fontSize: 10,
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
watch(() => props.show, (val) => {
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
  if (props.show) {
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
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="chart-overlay" @click.self="close">
        <div class="chart-container">
          <!-- 主体内容 -->
          <div class="chart-body">
            <!-- 左侧图表区域 -->
            <div class="chart-left">
              <div ref="chartRef" class="chart-area"></div>
            </div>

            <!-- 右侧信息面板 -->
            <div class="info-panel">
              <div class="info-header">
                <div class="info-header-top">
                  <div class="info-year">{{ year }}年</div>
                  <div class="close-btn" @click="close">
                    <van-icon name="cross" size="16" />
                  </div>
                </div>
                <div class="info-type">{{ typeName }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.chart-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  overflow: hidden;
}

.chart-container {
  /* 竖屏时横向显示 */
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

/* 横屏设备不需要旋转 */
@media (orientation: landscape) {
  .chart-container {
    width: 100vw;
    height: 100vh;
    transform: translate(-50%, -50%);
  }
}

/* 主体布局：左右分栏 */
.chart-body {
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
  width: 120px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-page);
  border-radius: 12px;
  overflow: hidden;
}

.info-header {
  padding: 12px;
}

.info-header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.info-year {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.close-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-card);
  border-radius: 50%;
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.close-btn:active {
  opacity: 0.7;
}

.info-type {
  font-size: 13px;
  color: var(--color-text-secondary);
  word-break: break-all;
  line-height: 1.4;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
