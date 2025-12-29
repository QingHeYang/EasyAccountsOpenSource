<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, onActivated, onDeactivated, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showConfirmDialog, showLoadingToast, closeToast, showDialog } from 'vant'
import { flowApi, type Flow, type FlowListResult } from '@shared/api/flow'
import FlowItem from '@mobile/components/FlowItem.vue'

const route = useRoute()
const router = useRouter()

// 数据
const loading = ref(false)
const flowData = ref<FlowListResult | null>(null)

// 当前月份
const currentDate = new Date()
const chooseMonth = ref(
  (route.query.month as string) ||
  `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}`
)

// 滚动检测 - 标题切换
const monthCardRef = ref<HTMLElement | null>(null)
const showMonthInHeader = ref(false)

function handleScroll() {
  if (!monthCardRef.value) return
  const rect = monthCardRef.value.getBoundingClientRect()
  showMonthInHeader.value = rect.bottom < 60
}

onActivated(() => {
  // 激活时重新计算滚动状态
  handleScroll()
  window.addEventListener('scroll', handleScroll, { passive: true })
})

onDeactivated(() => {
  window.removeEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})

// 月份选择器 - 双列滚轮
const showMonthPicker = ref(false)
const selectedYear = ref(parseInt(chooseMonth.value.split('-')[0]))
const selectedMonth = ref(parseInt(chooseMonth.value.split('-')[1]))
const yearColumnRef = ref<HTMLElement | null>(null)
const monthColumnRef = ref<HTMLElement | null>(null)

// 年份列（从2021年开始）
const yearColumns = computed(() => {
  const thisYear = new Date().getFullYear()
  const years = []
  for (let y = thisYear; y >= 2021; y--) {
    years.push({ text: `${y}年`, value: y })
  }
  return years
})

// 月份列
const monthColumns = computed(() => {
  const months = []
  for (let m = 1; m <= 12; m++) {
    months.push({ text: `${m}月`, value: m })
  }
  return months
})

// 打开选择器时同步当前值并滚动到选中项，锁定页面滚动
watch(showMonthPicker, (show) => {
  if (show) {
    selectedYear.value = parseInt(chooseMonth.value.split('-')[0])
    selectedMonth.value = parseInt(chooseMonth.value.split('-')[1])
    // 锁定页面滚动
    document.body.style.overflow = 'hidden'
    // 延迟滚动到选中项
    setTimeout(() => {
      scrollToSelected()
    }, 50)
  } else {
    // 解锁页面滚动
    document.body.style.overflow = ''
  }
})

function scrollToSelected() {
  const thisYear = new Date().getFullYear()
  const yearIndex = thisYear - selectedYear.value
  const monthIndex = selectedMonth.value - 1

  if (yearColumnRef.value) {
    const yearItem = yearColumnRef.value.children[yearIndex] as HTMLElement
    if (yearItem) {
      yearColumnRef.value.scrollTop = yearItem.offsetTop - yearColumnRef.value.offsetHeight / 2 + yearItem.offsetHeight / 2
    }
  }
  if (monthColumnRef.value) {
    const monthItem = monthColumnRef.value.children[monthIndex] as HTMLElement
    if (monthItem) {
      monthColumnRef.value.scrollTop = monthItem.offsetTop - monthColumnRef.value.offsetHeight / 2 + monthItem.offsetHeight / 2
    }
  }
}

function onYearClick(year: number) {
  selectedYear.value = year
}

function onMonthClick(month: number) {
  selectedMonth.value = month
}

function confirmMonthPicker() {
  const now = new Date()
  const currentYear = now.getFullYear()
  const currentMonth = now.getMonth() + 1

  // 不能选择未来月份
  if (selectedYear.value > currentYear ||
      (selectedYear.value === currentYear && selectedMonth.value > currentMonth)) {
    showToast('不能选择未来月份')
    return
  }

  chooseMonth.value = `${selectedYear.value}-${String(selectedMonth.value).padStart(2, '0')}`
  showMonthPicker.value = false
  fetchFlows()
}

function cancelMonthPicker() {
  showMonthPicker.value = false
}

// 筛选条件 - 折叠显示
const filterExpanded = ref(false)
const handleType = ref(3) // 3=全部, 0=流入, 1=流出, 2=转账
const orderType = ref(0) // 0=按时间, 1=按金额

const handleOptions = [
  { text: '全部', value: 3 },
  { text: '收入', value: 0 },
  { text: '支出', value: 1 },
  { text: '转账', value: 2 },
]

const orderOptions = [
  { text: '按时间', value: 0 },
  { text: '按金额', value: 1 },
]

// 当前筛选描述
const filterDesc = computed(() => {
  const handleText = handleOptions.find(o => o.value === handleType.value)?.text || '全部'
  const orderText = orderOptions.find(o => o.value === orderType.value)?.text || '按时间'
  if (handleType.value === 3 && orderType.value === 0) return ''
  return `${handleText} · ${orderText}`
})

// 月份显示
const monthDisplay = computed(() => {
  const [year, month] = chooseMonth.value.split('-')
  return `${year}年${parseInt(month)}月`
})

// 计算结余
const totalEarn = computed(() => {
  if (!flowData.value) return '0'
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
  fetchFlows()
}

function onMonthNext() {
  const [year, month] = chooseMonth.value.split('-').map(Number)
  const now = new Date()
  const currentYear = now.getFullYear()
  const currentMonth = now.getMonth() + 1

  if (year > currentYear || (year === currentYear && month >= currentMonth)) {
    showToast('已经是当月了')
    return
  }

  if (month === 12) {
    chooseMonth.value = `${year + 1}-01`
  } else {
    chooseMonth.value = `${year}-${String(month + 1).padStart(2, '0')}`
  }
  fetchFlows()
}

// 筛选变更
function onFilterChange(type: 'handle' | 'order', value: number) {
  if (type === 'handle') {
    handleType.value = value
  } else {
    orderType.value = value
  }
  fetchFlows()
}

// 跳转
function toAddFlow() {
  router.push('/flow/add')
}

function toFlowDetail(flow: Flow) {
  router.push(`/flow/edit/${flow.id}`)
}

function toScreen() {
  router.push('/screen')
}

// 收藏/取消收藏
async function onCollect(flow: Flow) {
  try {
    await flowApi.toggleCollect(flow.id, !flow.collect)
    showToast(flow.collect ? '已取消收藏' : '已收藏')
    fetchFlows()
  } catch (err) {
    showToast('操作失败')
  }
}

// 删除
function onDelete(flow: Flow) {
  showConfirmDialog({
    title: '确认删除',
    message: `确定删除 ¥${flow.money} 的「${flow.tname}」记录吗？`,
  }).then(async () => {
    try {
      await flowApi.delete(flow.id)
      showToast('已删除')
      fetchFlows()
    } catch (err) {
      showToast('删除失败')
    }
  }).catch(() => {})
}

// 生成 Excel 报表
function onExportExcel() {
  showConfirmDialog({
    title: '生成报表',
    message: `确定生成 ${monthDisplay.value} 的 Excel 报表吗？`,
  }).then(async () => {
    showLoadingToast({
      message: '生成中...',
      forbidClick: true,
    })
    try {
      const res = await flowApi.makeExcel(chooseMonth.value)
      closeToast()
      const result = res.data.data
      showDialog({
        title: result.success ? '生成成功' : '生成失败',
        message: result.log,
      })
    } catch (err) {
      closeToast()
      showToast('生成失败')
    }
  }).catch(() => {})
}

// 监听路由变化
watch(() => route.query.month, (newMonth) => {
  if (newMonth && newMonth !== chooseMonth.value) {
    chooseMonth.value = newMonth as string
    fetchFlows()
  }
})

onMounted(() => {
  fetchFlows()
})
</script>

<template>
  <div class="flow-page">
    <!-- 固定头部 -->
    <div class="page-header">
      <div class="header-title">
        {{ showMonthInHeader ? monthDisplay : '明细' }}
      </div>
      <div class="header-actions">
        <div class="header-btn" @click="filterExpanded = !filterExpanded">
          <van-icon name="filter-o" size="20" />
          <span v-if="filterDesc" class="filter-dot"></span>
        </div>
        <div class="header-btn" @click="onExportExcel">
          <van-icon name="description-o" size="20" />
        </div>
        <div class="header-btn" @click="toScreen">
          <van-icon name="search" size="20" />
        </div>
      </div>
    </div>

    <!-- 折叠筛选条件 -->
    <div class="filter-bar" :class="{ expanded: filterExpanded }">
      <div class="filter-row">
        <div class="filter-group">
          <span class="filter-group-label">类型</span>
          <div class="filter-chips">
            <div
              v-for="opt in handleOptions"
              :key="opt.value"
              class="filter-chip"
              :class="{ active: handleType === opt.value }"
              @click="onFilterChange('handle', opt.value)"
            >{{ opt.text }}</div>
          </div>
        </div>
      </div>
      <div class="filter-row">
        <div class="filter-group">
          <span class="filter-group-label">排序</span>
          <div class="filter-chips">
            <div
              v-for="opt in orderOptions"
              :key="opt.value"
              class="filter-chip"
              :class="{ active: orderType === opt.value }"
              @click="onFilterChange('order', opt.value)"
            >{{ opt.text }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 页面内容 -->
    <div class="page-body" :class="{ 'with-filter': filterExpanded }">
      <!-- 月份切换 + 统计 -->
      <div class="month-card" ref="monthCardRef">
        <div class="month-selector">
          <van-button size="small" icon="arrow-left" round plain @click="onMonthPrev" />
          <van-popover
            v-model:show="showMonthPicker"
            placement="bottom"
            :offset="[0, 8]"
          >
            <template #reference>
              <div class="month-title">
                {{ monthDisplay }}
                <van-icon :name="showMonthPicker ? 'arrow-up' : 'arrow-down'" size="12" />
              </div>
            </template>
            <div class="month-picker-popover">
              <div class="picker-columns">
                <div class="picker-column" ref="yearColumnRef">
                  <div
                    v-for="year in yearColumns"
                    :key="year.value"
                    class="picker-item"
                    :class="{ active: selectedYear === year.value }"
                    @click="onYearClick(year.value)"
                  >{{ year.text }}</div>
                </div>
                <div class="picker-column" ref="monthColumnRef">
                  <div
                    v-for="month in monthColumns"
                    :key="month.value"
                    class="picker-item"
                    :class="{ active: selectedMonth === month.value }"
                    @click="onMonthClick(month.value)"
                  >{{ month.text }}</div>
                </div>
              </div>
              <div class="picker-footer">
                <button class="picker-btn cancel" @click="cancelMonthPicker">取消</button>
                <button class="picker-btn confirm" @click="confirmMonthPicker">确定</button>
              </div>
            </div>
          </van-popover>
          <van-button size="small" icon="arrow" round plain @click="onMonthNext" />
        </div>

        <div class="month-stats" v-if="flowData">
          <div class="stat-item">
            <span class="stat-label">收入</span>
            <span class="stat-value income">+{{ flowData.totalIn || '0' }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">支出</span>
            <span class="stat-value expense">-{{ flowData.totalOut || '0' }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">结余</span>
            <span class="stat-value">{{ totalEarn }}</span>
          </div>
        </div>
      </div>

      <!-- 流水列表 -->
      <div class="flow-list" v-if="groupedFlows.length">
        <div class="flow-group" v-for="(group, index) in groupedFlows" :key="`${group.date}-${index}`">
          <div class="group-header">{{ group.dateLabel }}</div>
          <div class="group-items">
            <FlowItem
              v-for="flow in group.flows"
              :key="flow.id"
              :flow="flow"
              :show-remark="true"
              @click="toFlowDetail"
              @collect="onCollect"
              @delete="onDelete"
            />
          </div>
        </div>
      </div>

      <van-empty v-else-if="!loading" description="暂无账单" />
    </div>

    <!-- 浮动添加按钮 -->
    <div class="fab" @click="toAddFlow">
      <van-icon name="plus" size="24" />
    </div>

  </div>
</template>

<style scoped>
.flow-page {
  min-height: 100vh;
  background: transparent;
}

/* 固定头部 */
.page-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 50;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.header-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  gap: 4px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.header-btn {
  position: relative;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: var(--color-bg-card);
  color: var(--color-text-secondary);
}

.filter-dot {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-transfer);
}

/* 折叠筛选栏 */
.filter-bar {
  position: fixed;
  top: 68px;
  left: 0;
  right: 0;
  z-index: 49;
  padding: 0 16px;
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s ease, padding 0.3s ease;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.filter-bar.expanded {
  max-height: 120px;
  padding: 12px 16px;
}

.filter-row {
  margin-bottom: 8px;
}

.filter-row:last-child {
  margin-bottom: 0;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.filter-group-label {
  font-size: 13px;
  color: var(--color-text-tertiary);
  flex-shrink: 0;
  width: 32px;
}

.filter-chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-chip {
  padding: 4px 12px;
  border-radius: 14px;
  font-size: 13px;
  background: var(--color-bg-card);
  color: var(--color-text-secondary);
  transition: all 0.2s;
}

.filter-chip.active {
  background: var(--color-transfer);
  color: #fff;
}

/* 页面内容 */
.page-body {
  padding: 76px 16px 100px 16px;
  transition: padding-top 0.3s ease;
}

.page-body.with-filter {
  padding-top: 156px;
}

/* 月份卡片 */
.month-card {
  background: var(--color-bg-card);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
}

.month-selector {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.month-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}

.month-stats {
  display: flex;
  justify-content: space-around;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.stat-value {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.stat-value.income {
  color: var(--color-income);
}

.stat-value.expense {
  color: var(--color-expense);
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
  gap: 8px;
}

.group-header {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-tertiary);
  padding-left: 4px;
}

.group-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 浮动按钮 */
.fab {
  position: fixed;
  right: 20px;
  bottom: 100px;
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: var(--color-transfer);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.4);
  z-index: 50;
}

.fab:active {
  transform: scale(0.95);
}

/* 月份选择器 Popover */
.month-picker-popover {
  width: 220px;
  padding: 0;
}

.month-picker-popover .picker-columns {
  display: flex;
  height: 180px;
  overflow: hidden;
}

.month-picker-popover .picker-column {
  flex: 1;
  height: 100%;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
}

.month-picker-popover .picker-column::-webkit-scrollbar {
  display: none; /* Chrome/Safari */
}

.month-picker-popover .picker-item {
  padding: 10px 16px;
  text-align: center;
  font-size: 14px;
  color: var(--color-text-secondary);
  transition: all 0.15s;
  cursor: pointer;
}

.month-picker-popover .picker-item:active {
  background: var(--color-bg-page);
}

.month-picker-popover .picker-item.active {
  color: var(--color-transfer);
  font-weight: 600;
  background: rgba(24, 144, 255, 0.1);
}

.month-picker-popover .picker-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 8px 12px;
  border-top: 1px solid var(--color-border);
}

.month-picker-popover .picker-btn {
  padding: 6px 16px;
  font-size: 13px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
}

.month-picker-popover .picker-btn.cancel {
  background: var(--color-bg-page);
  color: var(--color-text-secondary);
}

.month-picker-popover .picker-btn.confirm {
  background: var(--color-transfer);
  color: #fff;
  font-weight: 500;
}
</style>

<!-- 页面特定样式 -->
<style>
.flow-page .page-header {
  background: rgba(245, 245, 245, 0.8);
}

.flow-page .filter-bar {
  background: rgba(245, 245, 245, 0.8);
}

html.dark .flow-page .page-header {
  background: rgba(10, 10, 10, 0.8);
}

html.dark .flow-page .filter-bar {
  background: rgba(10, 10, 10, 0.8);
}
</style>
