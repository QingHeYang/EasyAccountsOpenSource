<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { PieChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { AnalysisTypeItem } from '@shared/api/analysis'

// 注册 ECharts 组件
use([PieChart, TitleComponent, TooltipComponent, CanvasRenderer])

// 暗色模式检测
const isDark = ref(false)
let observer: MutationObserver | null = null

function updateDarkMode() {
  isDark.value = document.documentElement.classList.contains('dark')
}

onMounted(() => {
  updateDarkMode()
  observer = new MutationObserver(updateDarkMode)
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
})

onUnmounted(() => {
  observer?.disconnect()
})

const props = defineProps<{
  tabIndex: number
  typeList: (AnalysisTypeItem & { disabled?: boolean })[]
  loading?: boolean
}>()

const emit = defineEmits<{
  tabChange: [index: number]
  typeToggle: [typeId: number]
}>()

const tabs = [
  { label: '收入', value: 0 },
  { label: '支出', value: 1 },
]

// 预定义颜色（使用项目配色）
const incomeColors = [
  '#10b981', '#34d399', '#6ee7b7', '#a7f3d0',
  '#059669', '#047857', '#065f46', '#064e3b'
]

const expenseColors = [
  '#ef4444', '#f87171', '#fca5a5', '#fecaca',
  '#dc2626', '#b91c1c', '#991b1b', '#7f1d1d'
]

// 启用的分类（用于图表展示）
const enabledList = computed(() => {
  return props.typeList.filter(item => !item.disabled)
})

// 总金额
const totalAmount = computed(() => {
  return enabledList.value.reduce((sum, item) => sum + parseFloat(item.money || '0'), 0)
})

// 带颜色的分类列表（用于自定义图例）
const coloredTypeList = computed(() => {
  const colors = props.tabIndex === 0 ? incomeColors : expenseColors
  return props.typeList.map((item, index) => ({
    ...item,
    color: colors[index % colors.length]
  }))
})

// 格式化金额（简化显示）
function formatAmount(amount: number): string {
  if (Math.abs(amount) >= 10000) {
    return (amount / 10000).toFixed(2) + '万'
  }
  return amount.toFixed(2)
}

// 点击显示完整金额
function showFullAmountMessage() {
  const label = props.tabIndex === 0 ? '收入' : '支出'
  const amount = totalAmount.value.toFixed(2)
  ElMessage.info({
    message: `当前筛选${label}合计: ¥${amount}`,
    duration: 2000,
    showClose: true
  })
}

// 切换分类禁用状态
function toggleType(typeId: number) {
  emit('typeToggle', typeId)
}

// ECharts 配置（不含图例，图例用自定义UI）
const chartOption = computed(() => {
  const colors = props.tabIndex === 0 ? incomeColors : expenseColors
  const borderColor = isDark.value ? '#1f1f1f' : '#fff'
  const textColor = isDark.value ? '#e5e5e5' : '#333'
  const subTextColor = isDark.value ? '#a3a3a3' : '#666'

  // 只显示启用的分类
  const data = props.typeList
    .filter(item => !item.disabled && parseFloat(item.money || '0') > 0)
    .map((item, index) => {
      // 查找原始索引以保持颜色一致
      const originalIndex = props.typeList.findIndex(t => t.id === item.id)
      return {
        name: item.name,
        value: parseFloat(item.money || '0'),
        itemStyle: {
          color: colors[originalIndex % colors.length]
        }
      }
    })

  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: isDark.value ? '#333' : '#fff',
      borderColor: isDark.value ? '#555' : '#ccc',
      textStyle: {
        color: textColor
      },
      formatter: (params: any) => {
        const value = params.value.toFixed(2)
        return `${params.name}<br/>¥${value} (${params.percent}%)`
      }
    },
    series: [
      {
        type: 'pie',
        radius: ['35%', '55%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 4,
          borderColor: borderColor,
          borderWidth: 2
        },
        label: {
          show: true,
          position: 'outside',
          fontSize: 12,
          color: subTextColor,
          formatter: '{b}: {d}%'
        },
        labelLine: {
          show: true,
          length: 15,
          length2: 20,
          lineStyle: {
            color: subTextColor
          }
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold',
            color: textColor
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.3)'
          }
        },
        data
      }
    ]
  }
})

function onTabClick(index: number) {
  emit('tabChange', index)
}
</script>

<template>
  <div class="type-chart-section">
    <!-- Tab 切换 -->
    <div class="chart-header">
      <div class="tab-group">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          class="tab-btn"
          :class="{ active: tabIndex === tab.value }"
          @click="onTabClick(tab.value)"
        >
          {{ tab.label }}
        </button>
      </div>
      <div class="total-amount" @click="showFullAmountMessage" title="点击显示完整金额">
        <span class="total-label">{{ tabIndex === 0 ? '总收入' : '总支出' }}</span>
        <span class="total-value" :class="tabIndex === 0 ? 'income' : 'expense'">
          ¥{{ formatAmount(totalAmount) }}
        </span>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="chart-container">
      <div v-if="loading" class="chart-loading">
        <el-icon class="is-loading" :size="32">
          <Loading />
        </el-icon>
      </div>
      <div v-else-if="typeList.length === 0" class="chart-empty">
        暂无数据
      </div>
      <div v-else class="chart-body">
        <!-- 左侧饼图 -->
        <div class="chart-wrapper">
          <VChart
            :option="chartOption"
            autoresize
            class="pie-chart"
          />
        </div>

        <!-- 右侧自定义图例 -->
        <div class="legend-panel">
          <div class="legend-title">分类图例</div>
          <div class="legend-tip">点击可排除/恢复分类</div>
          <div class="legend-list">
            <div
              v-for="item in coloredTypeList"
              :key="item.id"
              class="legend-item"
              :class="{ disabled: item.disabled }"
              @click="toggleType(item.id)"
            >
              <span class="legend-dot" :style="{ background: item.disabled ? '#999' : item.color }"></span>
              <span class="legend-name">{{ item.name }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.type-chart-section {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.tab-group {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: var(--color-bg-page);
  border-radius: 10px;
}

.tab-btn {
  padding: 8px 20px;
  border: none;
  background: transparent;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn:hover {
  color: var(--color-text-primary);
}

.tab-btn.active {
  background: #fff;
  color: var(--color-text-primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.total-amount {
  display: flex;
  align-items: baseline;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  transition: background 0.2s;
}

.total-amount:hover {
  background: rgba(0, 0, 0, 0.04);
}

.total-label {
  font-size: 14px;
  color: var(--color-text-tertiary);
}

.total-value {
  font-size: 20px;
  font-weight: 600;
}

.total-value.income {
  color: var(--color-income);
}

.total-value.expense {
  color: var(--color-expense);
}

.chart-container {
  padding: 24px;
  min-height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-loading,
.chart-empty {
  color: var(--color-text-tertiary);
  font-size: 14px;
}

.chart-body {
  display: flex;
  width: 100%;
  height: 320px;
  gap: 24px;
}

.chart-wrapper {
  flex: 1;
  min-width: 0;
}

.pie-chart {
  width: 100%;
  height: 100%;
}

/* 自定义图例面板 */
.legend-panel {
  width: 200px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-page);
  border-radius: 12px;
  padding: 16px;
}

.legend-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}

.legend-tip {
  font-size: 12px;
  color: var(--color-text-quaternary);
  margin-bottom: 12px;
}

.legend-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.legend-item:hover {
  background: rgba(255, 255, 255, 0.9);
}

.legend-item.disabled {
  opacity: 0.5;
}

.legend-item.disabled .legend-name {
  text-decoration: line-through;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  flex-shrink: 0;
}

.legend-name {
  font-size: 13px;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 暗色模式 */
html.dark .type-chart-section {
  background: rgba(40, 40, 40, 0.6);
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .chart-header {
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .tab-btn.active {
  background: rgba(60, 60, 60, 0.8);
}

html.dark .total-amount:hover {
  background: rgba(255, 255, 255, 0.08);
}

html.dark .legend-panel {
  background: rgba(50, 50, 50, 0.6);
}

html.dark .legend-item {
  background: rgba(60, 60, 60, 0.4);
}

html.dark .legend-item:hover {
  background: rgba(70, 70, 70, 0.6);
}
</style>
