<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { init, type EChartsOption } from '@shared/utils/echarts'
import type { ECharts } from 'echarts/core'
import type { HomeMonthDetail, HomeAccount } from '@shared/api'

const props = defineProps<{
  show: boolean
  year: number
  monthDetails: HomeMonthDetail[]
  accounts: HomeAccount[]
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
}>()

// 图表实例
const trendChartRef = ref<HTMLDivElement>()
const accountChartRef = ref<HTMLDivElement>()
let trendChart: ECharts | null = null
let accountChart: ECharts | null = null

// 当前显示的图表：trend | account
const activeChart = ref<'trend' | 'account'>('trend')

// 检测暗黑模式
const isDark = () => document.documentElement.classList.contains('dark')

// 获取图表文字颜色（注意：白天模式用深色文字）
const getTextColor = () => isDark() ? '#e5e5e5' : '#1f2937'
const getSubTextColor = () => isDark() ? '#a3a3a3' : '#4b5563'
const getAxisLineColor = () => isDark() ? '#404040' : '#d1d5db'

// 关闭
function close() {
  emit('update:show', false)
}

// 生成趋势图配置
function getTrendOption(): EChartsOption {
  const months = props.monthDetails.map(m => `${m.month}月`)
  const incomes = props.monthDetails.map(m => parseFloat(m.income) || 0)
  const outcomes = props.monthDetails.map(m => parseFloat(m.outcome) || 0)
  const balances = props.monthDetails.map(m => parseFloat(m.balance) || 0)
  const textColor = getTextColor()
  const subTextColor = getSubTextColor()
  const axisLineColor = getAxisLineColor()

  return {
    title: {
      text: `${props.year}年度趋势`,
      left: 'center',
      top: 10,
      textStyle: {
        fontSize: 14,
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
      bottom: 10,
      itemWidth: 16,
      itemHeight: 10,
      textStyle: { fontSize: 11, color: subTextColor },
    },
    grid: {
      left: 50,
      right: 20,
      top: 50,
      bottom: 50,
    },
    xAxis: {
      type: 'category',
      data: months,
      axisLabel: { fontSize: 10, color: subTextColor },
      axisLine: { lineStyle: { color: axisLineColor } },
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
      axisLine: { lineStyle: { color: axisLineColor } },
      splitLine: { lineStyle: { color: axisLineColor } },
    },
    series: [
      {
        name: '收入',
        type: 'line',
        data: incomes,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        itemStyle: { color: '#10b981' },
        lineStyle: { width: 2 },
      },
      {
        name: '支出',
        type: 'line',
        data: outcomes,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        itemStyle: { color: '#ef4444' },
        lineStyle: { width: 2 },
      },
      {
        name: '结余',
        type: 'line',
        data: balances,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        itemStyle: { color: '#3b82f6' },
        lineStyle: { width: 2 },
      },
    ],
  }
}

// 生成账户柱状图配置（垂直柱状图，旋转后看起来是水平的）
function getAccountOption(): EChartsOption {
  const names = props.accounts.map(a => a.accountName)
  const assets = props.accounts.map(a => parseFloat(a.accountAsset) || 0)
  const textColor = getTextColor()
  const subTextColor = getSubTextColor()
  const axisLineColor = getAxisLineColor()

  return {
    title: {
      text: '账户资产',
      left: 'center',
      top: 10,
      textStyle: {
        fontSize: 14,
        fontWeight: 600,
        color: textColor,
      },
    },
    tooltip: {
      trigger: 'axis',
      confine: true,
      formatter: (params: any) => {
        const item = params[0]
        return `${item.name}<br/>¥ ${item.value.toFixed(2)}`
      },
    },
    grid: {
      left: 20,
      right: 20,
      top: 50,
      bottom: 60,
    },
    xAxis: {
      type: 'category',
      data: names,
      axisLabel: {
        fontSize: 10,
        color: subTextColor,
        interval: 0,
        rotate: 30,
      },
      axisLine: { lineStyle: { color: axisLineColor } },
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
      axisLine: { lineStyle: { color: axisLineColor } },
      splitLine: { lineStyle: { color: axisLineColor } },
    },
    series: [
      {
        type: 'bar',
        data: assets,
        barWidth: '50%',
        itemStyle: { color: '#3b82f6' },
        label: {
          show: true,
          position: 'top',
          fontSize: 9,
          color: subTextColor,
          formatter: (params: any) => {
            const val = params.value
            if (Math.abs(val) >= 10000) {
              return (val / 10000).toFixed(1) + '万'
            }
            return val.toFixed(0)
          },
        },
      },
    ],
  }
}

// 销毁图表
function disposeCharts() {
  if (trendChart) {
    trendChart.dispose()
    trendChart = null
  }
  if (accountChart) {
    accountChart.dispose()
    accountChart = null
  }
}

// 初始化图表
function initCharts() {
  // 先销毁旧的
  disposeCharts()

  // 延迟初始化确保 DOM 已渲染
  setTimeout(() => {
    if (trendChartRef.value) {
      trendChart = init(trendChartRef.value)
      trendChart.setOption(getTrendOption())
    }
    if (accountChartRef.value) {
      accountChart = init(accountChartRef.value)
      accountChart.setOption(getAccountOption())
    }
  }, 100)
}

// 切换图表
function switchChart(type: 'trend' | 'account') {
  activeChart.value = type
  nextTick(() => {
    setTimeout(() => {
      if (type === 'trend' && trendChart) {
        trendChart.resize()
      } else if (type === 'account' && accountChart) {
        accountChart.resize()
      }
    }, 50)
  })
}

// 监听显示状态
watch(() => props.show, (val) => {
  if (val) {
    nextTick(() => {
      initCharts()
    })
  } else {
    disposeCharts()
  }
})

// 处理窗口大小变化
function handleResize() {
  if (props.show) {
    trendChart?.resize()
    accountChart?.resize()
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  disposeCharts()
})
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="chart-overlay" @click.self="close">
        <div class="chart-container">
          <!-- 关闭按钮 -->
          <div class="close-btn" @click="close">
            <van-icon name="cross" size="20" />
          </div>

          <!-- 切换按钮（胶囊滑动样式） -->
          <div class="chart-tabs">
            <div class="chart-tabs-inner">
              <div class="tab-slider" :class="{ 'slide-right': activeChart === 'account' }"></div>
              <div
                class="tab-item"
                :class="{ active: activeChart === 'trend' }"
                @click="switchChart('trend')"
              >
                趋势
              </div>
              <div
                class="tab-item"
                :class="{ active: activeChart === 'account' }"
                @click="switchChart('account')"
              >
                账户
              </div>
            </div>
          </div>

          <!-- 趋势图 -->
          <div
            v-show="activeChart === 'trend'"
            ref="trendChartRef"
            class="chart-area"
          ></div>

          <!-- 账户图 -->
          <div
            v-show="activeChart === 'account'"
            ref="accountChartRef"
            class="chart-area"
          ></div>
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

.close-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-page);
  border-radius: 50%;
  color: var(--color-text-secondary);
  z-index: 10;
}

.close-btn:active {
  opacity: 0.7;
}

.chart-tabs {
  display: flex;
  justify-content: center;
  padding: 16px 50px 12px;
}

.chart-tabs-inner {
  position: relative;
  display: flex;
  background: var(--color-bg-page);
  border-radius: 20px;
  padding: 3px;
}

/* 滑动指示器 */
.tab-slider {
  position: absolute;
  top: 3px;
  left: 3px;
  width: calc(50% - 3px);
  height: calc(100% - 6px);
  background: #3b82f6;
  border-radius: 17px;
  transition: transform 0.3s ease;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
}

.tab-slider.slide-right {
  transform: translateX(100%);
}

.tab-item {
  position: relative;
  z-index: 1;
  padding: 6px 24px;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-secondary);
  background: transparent;
  border-radius: 17px;
  transition: color 0.3s;
}

.tab-item.active {
  color: #ffffff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.tab-item:active {
  opacity: 0.7;
}

.chart-area {
  flex: 1;
  width: 100%;
  min-height: 0;
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
