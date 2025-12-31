<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  ArrowRight,
  Filter,
  Download,
  Plus,
} from '@element-plus/icons-vue'
import { flowApi, type Flow, type FlowListResult } from '@shared/api/flow'
import FlowItem from '@desktop/components/FlowItem.vue'
import FlowEditor from '@desktop/components/flow/FlowEditor.vue'

const route = useRoute()

// 数据
const loading = ref(false)
const flowData = ref<FlowListResult | null>(null)

// 编辑器状态
const showEditor = ref(false)
const editFlowId = ref<number | null>(null)

// 当前月份
const currentDate = new Date()
const chooseMonth = ref(
  (route.query.month as string) ||
  `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}`
)

// 月份选择器
const pickerMonth = ref<string>(chooseMonth.value)

// 筛选条件
const handleType = ref(3) // 3=全部, 0=流入, 1=流出, 2=转账
const orderType = ref(0) // 0=按时间, 1=按金额

const handleOptions = [
  { label: '全部', value: 3 },
  { label: '收入', value: 0 },
  { label: '支出', value: 1 },
  { label: '转账', value: 2 },
]

const orderOptions = [
  { label: '按时间', value: 0 },
  { label: '按金额', value: 1 },
]

// 月份显示
const monthDisplay = computed(() => {
  const [year, month] = chooseMonth.value.split('-')
  return `${year}年${parseInt(month)}月`
})

// 计算结余
const totalBalance = computed(() => {
  if (!flowData.value) return '0.00'
  const income = parseFloat(flowData.value.totalIn || '0')
  const expense = parseFloat(flowData.value.totalOut || '0')
  return (income - expense).toFixed(2)
})

// 按日期分组的流水
const groupedFlows = computed(() => {
  if (!flowData.value?.flows?.length) return []

  const groups: { date: string; dateLabel: string; flows: Flow[] }[] = []
  let currentDate = ''

  for (const flow of flowData.value.flows) {
    if (flow.fdate !== currentDate) {
      currentDate = flow.fdate
      const parts = flow.fdate.split('-')
      const dateLabel = `${parseInt(parts[1])}月${parseInt(parts[2])}日`
      groups.push({ date: flow.fdate, dateLabel, flows: [] })
    }
    groups[groups.length - 1].flows.push(flow)
  }

  return groups
})

// 日历相关
const calendarDate = computed({
  get: () => new Date(chooseMonth.value + '-01'),
  set: (val: Date) => {
    const year = val.getFullYear()
    const month = String(val.getMonth() + 1).padStart(2, '0')
    const newMonth = `${year}-${month}`
    if (newMonth !== chooseMonth.value) {
      chooseMonth.value = newMonth
      fetchFlows()
    }
  }
})

// 有记账的日期集合
const datesWithRecords = computed(() => {
  const dates = new Set<string>()
  if (flowData.value?.flows) {
    for (const flow of flowData.value.flows) {
      dates.add(flow.fdate)
    }
  }
  return dates
})

// 判断某天是否有记账
function hasRecord(date: Date): boolean {
  const dateStr = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
  return datesWithRecords.value.has(dateStr)
}

// 判断日期是否是当前月
function isCurrentMonth(date: Date): boolean {
  const [year, month] = chooseMonth.value.split('-').map(Number)
  return date.getFullYear() === year && date.getMonth() + 1 === month
}

// 点击日历日期
function onCalendarDateClick(date: Date) {
  if (!isCurrentMonth(date)) return
  // 滚动到该日期的流水
  const dateStr = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
  const groupEl = document.querySelector(`[data-date="${dateStr}"]`)
  if (groupEl) {
    groupEl.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

// 获取流水列表
async function fetchFlows() {
  loading.value = true
  try {
    const res = await flowApi.getMonthList(handleType.value, orderType.value, chooseMonth.value)
    if (res.data.code === 0) {
      flowData.value = res.data.data
    }
  } catch (err) {
    console.error('获取流水失败:', err)
  } finally {
    loading.value = false
  }
}

// 月份切换
function onMonthPrev() {
  const [year, month] = chooseMonth.value.split('-').map(Number)
  if (month === 1) {
    chooseMonth.value = `${year - 1}-12`
  } else {
    chooseMonth.value = `${year}-${String(month - 1).padStart(2, '0')}`
  }
  pickerMonth.value = chooseMonth.value
  fetchFlows()
}

function onMonthNext() {
  const [year, month] = chooseMonth.value.split('-').map(Number)
  const now = new Date()
  const currentYear = now.getFullYear()
  const currentMonth = now.getMonth() + 1

  if (year > currentYear || (year === currentYear && month >= currentMonth)) {
    ElMessage.warning('已经是当月了')
    return
  }

  if (month === 12) {
    chooseMonth.value = `${year + 1}-01`
  } else {
    chooseMonth.value = `${year}-${String(month + 1).padStart(2, '0')}`
  }
  pickerMonth.value = chooseMonth.value
  fetchFlows()
}

// 选择月份
function onPickMonth(val: string | null) {
  if (!val) return
  chooseMonth.value = val
  pickerMonth.value = val
  fetchFlows()
}

// 筛选变更
function onFilterChange() {
  fetchFlows()
}

// 打开编辑器
function toAddFlow() {
  editFlowId.value = null
  showEditor.value = true
}

function toFlowDetail(flow: Flow) {
  editFlowId.value = flow.id
  showEditor.value = true
}

function onEditorSuccess() {
  fetchFlows()
}

// 收藏/取消收藏
async function onCollect(flow: Flow) {
  try {
    await flowApi.toggleCollect(flow.id, !flow.collect)
    ElMessage.success(flow.collect ? '已取消收藏' : '已收藏')
    fetchFlows()
  } catch (err) {
    ElMessage.error('操作失败')
  }
}

// 删除
function onDelete(flow: Flow) {
  ElMessageBox.confirm(
    `确定删除 ¥${flow.money} 的「${flow.tname}」记录吗？`,
    '确认删除',
    {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await flowApi.delete(flow.id)
      ElMessage.success('已删除')
      fetchFlows()
    } catch (err) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

// 导出 Excel
function onExportExcel() {
  ElMessageBox.confirm(
    `确定生成 ${monthDisplay.value} 的 Excel 报表吗？`,
    '生成报表',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info',
    }
  ).then(async () => {
    const loadingMsg = ElMessage({
      message: '生成中...',
      type: 'info',
      duration: 0,
    })
    try {
      const res = await flowApi.makeExcel(chooseMonth.value)
      loadingMsg.close()
      const result = res.data.data
      if (result.success) {
        ElMessage.success(result.log)
      } else {
        ElMessage.error(result.log)
      }
    } catch (err) {
      loadingMsg.close()
      ElMessage.error('生成失败')
    }
  }).catch(() => {})
}

// 监听路由变化
watch(() => route.query.month, (newMonth) => {
  if (newMonth && newMonth !== chooseMonth.value) {
    chooseMonth.value = newMonth as string
    pickerMonth.value = newMonth as string
    fetchFlows()
  }
})

onMounted(() => {
  fetchFlows()
})
</script>

<template>
  <div class="flow-list-page" v-loading="loading">
    <div class="flow-layout">
      <!-- 左侧：流水列表 -->
      <div class="left-panel">
        <!-- 列表头 -->
        <div class="list-header">
          <span class="col-date">日期</span>
          <span class="col-type">分类</span>
          <span class="col-account">账户</span>
          <span class="col-remark">备注</span>
          <span class="col-money">金额</span>
          <span class="col-actions">操作</span>
        </div>

        <!-- 流水列表（可滚动区域） -->
        <div class="flow-list-wrapper">
          <div class="flow-list" v-if="groupedFlows.length">
            <div class="flow-group" v-for="group in groupedFlows" :key="group.date" :data-date="group.date">
              <div class="group-header">{{ group.dateLabel }}</div>
              <div class="group-items">
                <FlowItem
                  v-for="flow in group.flows"
                  :key="flow.id"
                  :flow="flow"
                  @click="toFlowDetail"
                  @collect="onCollect"
                  @delete="onDelete"
                />
              </div>
            </div>
          </div>

          <el-empty v-else-if="!loading" description="暂无账单" />
        </div>
      </div>

      <!-- 右侧：统计 + 筛选 -->
      <div class="right-panel">
        <!-- 新增按钮 -->
        <button class="add-btn-m" @click="toAddFlow">
          <div class="m-stripes"></div>
          <div class="btn-content">
            <el-icon><Plus /></el-icon>
            <span>新增账单</span>
          </div>
        </button>

        <!-- 月份选择 -->
        <div class="month-card">
          <div class="month-selector">
            <el-button :icon="ArrowLeft" circle size="small" @click="onMonthPrev" />
            <el-date-picker
              v-model="pickerMonth"
              type="month"
              format="YYYY年M月"
              value-format="YYYY-MM"
              :disabled-date="(date: Date) => date > new Date()"
              :clearable="false"
              class="month-picker"
              @change="onPickMonth"
            />
            <el-button :icon="ArrowRight" circle size="small" @click="onMonthNext" />
          </div>
        </div>

        <!-- 月度统计 -->
        <div class="stats-card">
          <div class="stat-row">
            <span class="stat-label">收入</span>
            <span class="stat-value income">+{{ flowData?.totalIn || '0.00' }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">支出</span>
            <span class="stat-value expense">-{{ flowData?.totalOut || '0.00' }}</span>
          </div>
          <el-divider />
          <div class="stat-row">
            <span class="stat-label">结余</span>
            <span class="stat-value balance">{{ totalBalance }}</span>
          </div>
        </div>

        <!-- 日历卡片 -->
        <div class="calendar-card">
          <el-calendar v-model="calendarDate">
            <template #date-cell="{ data }">
              <div
                class="calendar-cell"
                :class="{
                  'has-record': hasRecord(data.date),
                  'other-month': !isCurrentMonth(data.date)
                }"
                @click="onCalendarDateClick(data.date)"
              >
                <span class="day-num">{{ data.date.getDate() }}</span>
                <span v-if="hasRecord(data.date)" class="record-dot"></span>
              </div>
            </template>
          </el-calendar>
        </div>

        <!-- 筛选条件 -->
        <div class="filter-card">
          <h3 class="filter-title">
            <el-icon><Filter /></el-icon>
            <span>筛选</span>
          </h3>
          <div class="filter-group">
            <label class="filter-label">类型</label>
            <el-radio-group v-model="handleType" size="small" @change="onFilterChange">
              <el-radio-button
                v-for="opt in handleOptions"
                :key="opt.value"
                :value="opt.value"
              >{{ opt.label }}</el-radio-button>
            </el-radio-group>
          </div>
          <div class="filter-group">
            <label class="filter-label">排序</label>
            <el-radio-group v-model="orderType" size="small" @change="onFilterChange">
              <el-radio-button
                v-for="opt in orderOptions"
                :key="opt.value"
                :value="opt.value"
              >{{ opt.label }}</el-radio-button>
            </el-radio-group>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <el-button :icon="Download" @click="onExportExcel">导出报表</el-button>
        </div>
      </div>
    </div>

    <!-- 账单编辑器 -->
    <FlowEditor
      v-model:visible="showEditor"
      :flow-id="editFlowId"
      @success="onEditorSuccess"
    />
  </div>
</template>

<style scoped>
.flow-list-page {
  position: relative;
}

/* 主布局 */
.flow-layout {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 20px;
}

/* 左侧：流水列表 */
.left-panel {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

/* 右侧：操作面板 */
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 月份卡片 */
.month-card {
  background: linear-gradient(135deg, var(--color-transfer) 0%, #5b9cf8 100%);
  border-radius: 16px;
  padding: 20px;
  color: #fff;
}

.month-selector {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  position: relative;
}

.month-selector .el-button {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: #fff;
}

.month-selector .el-button:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* 月份选择器 */
.month-selector :deep(.month-picker) {
  --el-date-editor-width: auto;
  --el-fill-color-blank: transparent;
}

.month-selector :deep(.month-picker .el-input__wrapper) {
  background: transparent !important;
  box-shadow: none !important;
  border: none !important;
  padding: 6px 16px;
  border-radius: 8px;
  transition: background 0.2s;
  cursor: pointer;
}

.month-selector :deep(.month-picker .el-input__wrapper:hover) {
  background: rgba(255, 255, 255, 0.25) !important;
}

.month-selector :deep(.month-picker .el-input__inner) {
  color: #fff !important;
  font-size: 18px;
  font-weight: 600;
  text-align: center;
  cursor: pointer;
  caret-color: transparent;
}

.month-selector :deep(.month-picker .el-input__prefix),
.month-selector :deep(.month-picker .el-input__suffix) {
  display: none !important;
}

/* 日历卡片 */
.calendar-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  padding: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.calendar-card :deep(.el-calendar) {
  --el-calendar-border: none;
  --el-calendar-header-border-bottom: none;
  background: transparent;
}

.calendar-card :deep(.el-calendar__header) {
  padding: 8px 12px;
  border-bottom: none;
}

.calendar-card :deep(.el-calendar__title) {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.calendar-card :deep(.el-calendar__button-group) {
  display: none;
}

.calendar-card :deep(.el-calendar__body) {
  padding: 0;
}

.calendar-card :deep(.el-calendar-table) {
  font-size: 12px;
}

.calendar-card :deep(.el-calendar-table thead th) {
  padding: 6px 0;
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-tertiary);
}

.calendar-card :deep(.el-calendar-table td) {
  border: none !important;
}

.calendar-card :deep(.el-calendar-table .el-calendar-day) {
  height: auto;
  padding: 0;
}

.calendar-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 32px;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  transition: background 0.2s;
}

.calendar-cell:hover {
  background: var(--color-bg-page);
}

.calendar-cell.other-month {
  opacity: 0.3;
}

.calendar-cell .day-num {
  font-size: 12px;
  color: var(--color-text-primary);
}

.calendar-cell.has-record .day-num {
  font-weight: 600;
  color: var(--color-transfer);
}

.record-dot {
  position: absolute;
  bottom: 2px;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--color-transfer);
}

.calendar-card :deep(.el-calendar-table td.is-today .calendar-cell) {
  background: var(--color-transfer);
}

.calendar-card :deep(.el-calendar-table td.is-today .calendar-cell .day-num) {
  color: #fff;
  font-weight: 600;
}

.calendar-card :deep(.el-calendar-table td.is-today .calendar-cell .record-dot) {
  background: #fff;
}

/* 统计卡片 */
.stats-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.stat-label {
  font-size: 14px;
  color: var(--color-text-tertiary);
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
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

.stats-card .el-divider {
  margin: 8px 0;
}

/* 筛选卡片 */
.filter-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 16px 0;
}

.filter-group {
  margin-bottom: 12px;
}

.filter-group:last-child {
  margin-bottom: 0;
}

.filter-label {
  display: block;
  font-size: 13px;
  color: var(--color-text-tertiary);
  margin-bottom: 8px;
}

/* 操作按钮 */
.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-buttons .el-button {
  width: 100%;
}

/* 列表头 */
.list-header {
  display: grid;
  grid-template-columns: 60px 220px 200px 1fr 120px 80px;
  gap: 16px;
  padding: 12px 16px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-tertiary);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.col-money,
.col-actions {
  text-align: right;
}

/* 流水列表容器 */
.flow-list-wrapper {
  margin-top: 8px;
}

/* 流水列表 */
.flow-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.flow-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.group-header {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-tertiary);
  padding: 12px 16px 8px;
  background: var(--color-bg-page);
  border-radius: 8px 8px 0 0;
  margin-top: 8px;
}

.flow-group:first-child .group-header {
  margin-top: 0;
}

.group-items {
  display: flex;
  flex-direction: column;
  background: var(--color-bg-card);
  border-radius: 0 0 8px 8px;
}

/* 新增按钮 - 三色斜分 */
.add-btn-m {
  position: relative;
  width: 100%;
  height: 48px;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  overflow: hidden;
  background: linear-gradient(
    135deg,
    var(--color-income) 0%,
    var(--color-income) 25%,
    var(--color-transfer) 25%,
    var(--color-transfer) 75%,
    var(--color-expense) 75%,
    var(--color-expense) 100%
  );
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transition: transform 0.2s, box-shadow 0.2s;
}

.add-btn-m::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 12px;
  opacity: 0;
  transition: opacity 0.3s;
  box-shadow:
    0 0 20px 4px rgba(16, 185, 129, 0.5),
    0 0 30px 8px rgba(239, 68, 68, 0.4),
    0 0 40px 12px rgba(59, 130, 246, 0.3);
}

.add-btn-m:hover::before {
  opacity: 1;
}

.add-btn-m:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.add-btn-m:active {
  transform: translateY(0);
}

.m-stripes {
  display: none;
}

.btn-content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 100%;
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}
</style>

<!-- 暗色模式 -->
<style>
html.dark .flow-list-page .left-panel,
html.dark .flow-list-page .stats-card,
html.dark .flow-list-page .filter-card,
html.dark .flow-list-page .calendar-card {
  background: rgba(40, 40, 40, 0.6);
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .flow-list-page .group-header {
  background: rgba(30, 30, 30, 0.6);
}

html.dark .flow-list-page .group-items {
  background: rgba(40, 40, 40, 0.4);
}

html.dark .flow-list-page .calendar-cell:hover {
  background: rgba(50, 50, 50, 0.6);
}

/* 月份选择器暗色模式 */
html.dark .flow-list-page .month-picker {
  --el-fill-color-blank: transparent;
}

html.dark .flow-list-page .month-picker .el-input__wrapper {
  background: transparent !important;
  background-color: transparent !important;
  box-shadow: none !important;
}
</style>
