<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { init, type EChartsOption } from '@shared/utils/echarts'
import type { ECharts } from 'echarts/core'
import type { AnalysisTypeItem } from '@shared/api'

const props = defineProps<{
  show: boolean
  totalIn: string
  totalOut: string
  inTypeList: AnalysisTypeItem[]
  outTypeList: AnalysisTypeItem[]
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
}>()

// 图表实例
const chartRef = ref<HTMLDivElement>()
let chart: ECharts | null = null

// 当前显示：income | expense
const activeTab = ref<'income' | 'expense'>('expense')

// 检测暗黑模式
const isDark = () => document.documentElement.classList.contains('dark')

// 获取图表文字颜色
const getTextColor = () => isDark() ? '#e5e5e5' : '#1f2937'
const getSubTextColor = () => isDark() ? '#a3a3a3' : '#4b5563'

// 关闭
function close() {
  emit('update:show', false)
}

// 收入饼图颜色（绿色系）
const incomeColors = [
  '#10b981', '#34d399', '#6ee7b7', '#a7f3d0',
  '#059669', '#047857', '#065f46', '#064e3b',
]

// 支出饼图颜色（红色系）
const expenseColors = [
  '#ef4444', '#f87171', '#fca5a5', '#fecaca',
  '#dc2626', '#b91c1c', '#991b1b', '#7f1d1d',
]

// 禁用的分类ID
const disabledIds = ref<Set<number>>(new Set())

// 切换禁用状态
function toggleDisabled(id: number) {
  const newSet = new Set(disabledIds.value)
  if (newSet.has(id)) {
    newSet.delete(id)
  } else {
    newSet.add(id)
  }
  disabledIds.value = newSet
  updateChart()
}

// 当前显示的数据
const currentList = computed(() => {
  const isIncome = activeTab.value === 'income'
  const list = isIncome ? props.inTypeList : props.outTypeList
  const colors = isIncome ? incomeColors : expenseColors

  return list
    .filter(item => parseFloat(item.money) > 0)
    .map((item, idx) => ({
      ...item,
      color: colors[idx % colors.length],
      disabled: disabledIds.value.has(item.id),
    }))
})

const currentTotal = computed(() => {
  return activeTab.value === 'income' ? props.totalIn : props.totalOut
})

// 生成饼图配置
function getChartOption(): EChartsOption {
  const isIncome = activeTab.value === 'income'
  const list = isIncome ? props.inTypeList : props.outTypeList
  const colors = isIncome ? incomeColors : expenseColors
  const subTextColor = getSubTextColor()

  // 先给所有分类分配颜色，再过滤禁用的（保持颜色一致）
  const data = list
    .filter(item => parseFloat(item.money) > 0)
    .map((item, idx) => ({
      id: item.id,
      name: item.name,
      value: parseFloat(item.money),
      color: colors[idx % colors.length],
    }))
    .filter(item => !disabledIds.value.has(item.id))
    .map(item => ({
      name: item.name,
      value: item.value,
      itemStyle: { color: item.color },
    }))

  return {
    tooltip: {
      trigger: 'item',
      confine: true,
      formatter: (params: any) => {
        return `${params.name}<br/>¥${params.value.toFixed(2)} (${params.percent}%)`
      },
    },
    series: [
      {
        type: 'pie',
        radius: ['35%', '65%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 4,
          borderColor: isDark() ? '#1a1a1a' : '#fff',
          borderWidth: 2,
        },
        label: {
          show: true,
          position: 'outside',
          fontSize: 10,
          color: subTextColor,
          formatter: '{b}: {d}%',
        },
        labelLine: {
          show: true,
          length: 10,
          length2: 12,
          lineStyle: {
            color: subTextColor,
          },
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 12,
            fontWeight: 'bold',
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.3)',
          },
        },
        data,
      },
    ],
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

// 更新图表
function updateChart() {
  if (chart) {
    chart.setOption(getChartOption(), true)
  }
}

// 切换 tab
function switchTab(tab: 'income' | 'expense') {
  activeTab.value = tab
  nextTick(() => {
    updateChart()
  })
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

// 监听数据变化
watch([() => props.inTypeList, () => props.outTypeList], () => {
  if (props.show && chart) {
    updateChart()
  }
}, { deep: true })

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
          <!-- 主体内容：左侧饼图 + 右侧信息框 -->
          <div class="chart-body">
            <!-- 左侧饼图区域 -->
            <div class="chart-left">
              <!-- 切换按钮（胶囊滑动样式） -->
              <div class="chart-tabs">
                <div class="chart-tabs-inner">
                  <div
                    class="tab-slider"
                    :class="{
                      'slide-right': activeTab === 'expense',
                      'income': activeTab === 'income',
                      'expense': activeTab === 'expense'
                    }"
                  ></div>
                  <div
                    class="tab-item"
                    :class="{ active: activeTab === 'income' }"
                    @click="switchTab('income')"
                  >
                    收入
                  </div>
                  <div
                    class="tab-item"
                    :class="{ active: activeTab === 'expense' }"
                    @click="switchTab('expense')"
                  >
                    支出
                  </div>
                </div>
              </div>
              <!-- 饼图 -->
              <div ref="chartRef" class="chart-area"></div>
            </div>

            <!-- 右侧信息框 -->
            <div class="info-panel">
              <div class="info-header">
                <div class="info-header-top">
                  <div class="info-title">{{ activeTab === 'income' ? '收入占比' : '支出占比' }}</div>
                  <div class="close-btn" @click="close">
                    <van-icon name="cross" size="16" />
                  </div>
                </div>
                <div class="info-total" :class="activeTab">¥{{ parseFloat(currentTotal).toFixed(2) }}</div>
              </div>
              <div class="info-list">
                <div
                  v-for="item in currentList"
                  :key="item.id"
                  class="info-item"
                  :class="{ disabled: item.disabled }"
                  @click="toggleDisabled(item.id)"
                >
                  <span class="item-dot" :style="{ background: item.color }"></span>
                  <span class="item-name">{{ item.name }}</span>
                </div>
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

.chart-tabs {
  display: flex;
  justify-content: center;
  padding: 4px 0 8px;
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
  border-radius: 17px;
  transition: transform 0.3s ease, background 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.tab-slider.income {
  background: #10b981;
}

.tab-slider.expense {
  background: #ef4444;
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
  color: #fff !important;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.tab-item:active {
  opacity: 0.7;
}

.chart-area {
  flex: 1;
  min-height: 0;
}

/* 右侧信息面板 */
.info-panel {
  width: 160px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-page);
  border-radius: 12px;
  overflow: hidden;
}

.info-header {
  padding: 12px;
  border-bottom: 1px solid var(--color-border);
}

.info-header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.info-title {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.info-total {
  font-size: 16px;
  font-weight: 700;
}

.info-total.income {
  color: #10b981;
}

.info-total.expense {
  color: #ef4444;
}

.info-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 12px;
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
}

.info-list::-webkit-scrollbar {
  display: none; /* Chrome/Safari */
}

.info-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 0;
  font-size: 11px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.info-item:active {
  opacity: 0.6;
}

.info-item.disabled {
  opacity: 0.4;
}

.info-item.disabled .item-dot {
  background: var(--color-text-tertiary) !important;
}

.info-item.disabled .item-name {
  text-decoration: line-through;
}

.item-dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  flex-shrink: 0;
}

.item-name {
  flex: 1;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
