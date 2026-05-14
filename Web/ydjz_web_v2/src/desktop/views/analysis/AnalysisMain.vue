<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { analysisApi, type AnalysisTypeItem } from '@shared/api/analysis'
import StatsCards from './StatsCards.vue'
import TypeChart from './TypeChart.vue'
import TypeGrid from './TypeGrid.vue'
import FilterPanel from './FilterPanel.vue'
import './styles.css'

const emit = defineEmits<{
  typeClick: [typeId: number, startDate: string, endDate: string]
}>()

// ==================== 状态 ====================
const loading = ref(false)
const tabIndex = ref(0) // 0收入 1支出

// 时间筛选
const fastChoose = ref(0) // 0当月 1上月 2近3月 3近6月 4近1年 5当年 6上年
const startDate = ref('')
const endDate = ref('')

// 筛选选项
const combineSubType = ref(false)
const showDisableAnalysisType = ref(true)

// 数据
const totalIn = ref('0.00')
const totalOut = ref('0.00')
const showInTypeList = ref<AnalysisTypeItem[]>([])
const showOutTypeList = ref<AnalysisTypeItem[]>([])
const allInTypeList = ref<AnalysisTypeItem[]>([])
const allOutTypeList = ref<AnalysisTypeItem[]>([])

// 禁用的分类ID（用于排除某些分类不参与百分比计算）
const disabledTypeIds = ref<Set<number>>(new Set())

// ==================== 工具函数 ====================
function formatYMD(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

/** 某年某月 1 号 */
function firstDayOf(year: number, month: number): Date {
  return new Date(year, month, 1)
}

/** 某年某月最后一天 */
function lastDayOf(year: number, month: number): Date {
  return new Date(year, month + 1, 0)
}

// 根据快捷选项计算日期范围（统一输出 yyyy-MM-dd，覆盖完整自然月起止）
function calcDateRange(value: number): { start: string; end: string } {
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth()
  const today = formatYMD(now)

  switch (value) {
    case 0: // 当月：1 号 ~ 今天
      return { start: formatYMD(firstDayOf(year, month)), end: today }
    case 1: // 上月：上月 1 号 ~ 上月最后一天
      return {
        start: formatYMD(firstDayOf(year, month - 1)),
        end: formatYMD(lastDayOf(year, month - 1)),
      }
    case 2: // 近 3 月：3 个月前的 1 号 ~ 今天
      return { start: formatYMD(firstDayOf(year, month - 2)), end: today }
    case 3: // 近 6 月
      return { start: formatYMD(firstDayOf(year, month - 5)), end: today }
    case 4: // 近 1 年
      return { start: formatYMD(firstDayOf(year - 1, month)), end: today }
    case 5: // 本年：1/1 ~ 今天
      return { start: `${year}-01-01`, end: today }
    case 6: // 上年：上年 1/1 ~ 12/31
      return { start: `${year - 1}-01-01`, end: `${year - 1}-12-31` }
    default:
      return { start: formatYMD(firstDayOf(year, month)), end: today }
  }
}

// ==================== 计算属性 ====================
// 当前显示的分类列表（用于图表）
const currentShowList = computed(() => {
  return tabIndex.value === 0 ? showInTypeList.value : showOutTypeList.value
})

// 当前全部分类列表（用于网格，带重新计算的百分比）
const currentTypeList = computed(() => {
  const list = tabIndex.value === 0 ? allInTypeList.value : allOutTypeList.value

  // 计算启用项的总金额
  const enabledTotal = list
    .filter(item => !disabledTypeIds.value.has(item.id))
    .reduce((sum, item) => sum + parseFloat(item.money || '0'), 0)

  // 重新计算百分比
  return list.map(item => {
    const isDisabled = disabledTypeIds.value.has(item.id)
    const money = parseFloat(item.money || '0')
    const newPercent = isDisabled || enabledTotal === 0
      ? 0
      : Math.round((money / enabledTotal) * 100)

    return {
      ...item,
      percent: newPercent,
      disabled: isDisabled
    }
  })
})

const currentTotal = computed(() => {
  return tabIndex.value === 0 ? totalIn.value : totalOut.value
})

// ==================== 数据加载 ====================
async function fetchData() {
  if (!startDate.value || !endDate.value) return

  loading.value = true
  try {
    const res = await analysisApi.getTypeList({
      start: startDate.value,
      end: endDate.value,
      combineSubType: combineSubType.value,
      showDisableAnalysisType: showDisableAnalysisType.value,
    })

    if (res.data.code === 0) {
      const data = res.data.data
      totalIn.value = data.totalIn
      totalOut.value = data.totalOut
      showInTypeList.value = data.showInTypeList
      showOutTypeList.value = data.showOutTypeList
      allInTypeList.value = data.allInTypeList
      allOutTypeList.value = data.allOutTypeList
      // 清空禁用状态
      disabledTypeIds.value = new Set()
    } else {
      ElMessage.error(res.data.msg || '获取统计数据失败')
    }
  } catch (err) {
    console.error('获取统计数据失败', err)
    ElMessage.error('获取统计数据失败')
  } finally {
    loading.value = false
  }
}

// ==================== 事件处理 ====================
function onTabChange(index: number) {
  tabIndex.value = index
}

function onFastChoose(value: number) {
  fastChoose.value = value
  const range = calcDateRange(value)
  startDate.value = range.start
  endDate.value = range.end
  fetchData()
}

function onDateChange(start: string, end: string) {
  startDate.value = start
  endDate.value = end
  fastChoose.value = -1 // 标记为自定义
  fetchData()
}

function onFilterChange(options: { combineSubType: boolean; showDisableAnalysisType: boolean }) {
  combineSubType.value = options.combineSubType
  showDisableAnalysisType.value = options.showDisableAnalysisType
  fetchData()
}

function onTypeClick(typeId: number) {
  emit('typeClick', typeId, startDate.value, endDate.value)
}

function toggleTypeDisabled(typeId: number) {
  const newSet = new Set(disabledTypeIds.value)
  if (newSet.has(typeId)) {
    newSet.delete(typeId)
  } else {
    newSet.add(typeId)
  }
  disabledTypeIds.value = newSet
}

// ==================== 生命周期 ====================
onMounted(() => {
  // 默认当月
  onFastChoose(0)
})
</script>

<template>
  <div class="analysis-main">
    <div class="analysis-layout">
      <!-- 左侧主区域 -->
      <div class="main-area">
        <!-- 统计卡片 -->
        <StatsCards
          :total-in="totalIn"
          :total-out="totalOut"
          :loading="loading"
        />

        <!-- 图表区域 -->
        <TypeChart
          :tab-index="tabIndex"
          :type-list="currentTypeList"
          :loading="loading"
          @tab-change="onTabChange"
          @type-toggle="toggleTypeDisabled"
        />

        <!-- 分类网格 -->
        <TypeGrid
          :tab-index="tabIndex"
          :type-list="currentTypeList"
          :loading="loading"
          @type-click="onTypeClick"
          @type-toggle="toggleTypeDisabled"
        />
      </div>

      <!-- 右侧筛选面板 -->
      <div class="side-panel">
        <FilterPanel
          :fast-choose="fastChoose"
          :start-date="startDate"
          :end-date="endDate"
          :combine-sub-type="combineSubType"
          :show-disable-analysis-type="showDisableAnalysisType"
          @fast-choose="onFastChoose"
          @date-change="onDateChange"
          @filter-change="onFilterChange"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.analysis-main {
  /* 主容器 */
}

.analysis-layout {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 24px;
  align-items: start;
}

.main-area {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.side-panel {
  position: sticky;
  top: 100px;
}
</style>
