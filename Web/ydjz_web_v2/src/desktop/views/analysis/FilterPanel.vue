<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  fastChoose: number
  startDate: string
  endDate: string
  combineSubType: boolean
  showDisableAnalysisType: boolean
}>()

const emit = defineEmits<{
  fastChoose: [value: number]
  dateChange: [start: string, end: string]
  filterChange: [options: { combineSubType: boolean; showDisableAnalysisType: boolean }]
}>()

// 快捷选项
const fastOptions = [
  { label: '当月', value: 0 },
  { label: '上月', value: 1 },
  { label: '近3月', value: 2 },
  { label: '近6月', value: 3 },
  { label: '近1年', value: 4 },
  { label: '当年', value: 5 },
  { label: '上年', value: 6 },
]

// 本地状态
const localCombineSubType = ref(props.combineSubType)
const localShowDisableAnalysisType = ref(props.showDisableAnalysisType)
const localStartDate = ref(props.startDate)
const localEndDate = ref(props.endDate)

// 同步 props
watch(() => props.combineSubType, (val) => { localCombineSubType.value = val })
watch(() => props.showDisableAnalysisType, (val) => { localShowDisableAnalysisType.value = val })
watch(() => props.startDate, (val) => { localStartDate.value = val })
watch(() => props.endDate, (val) => { localEndDate.value = val })

function onFastClick(value: number) {
  emit('fastChoose', value)
}

function onFilterToggle() {
  emit('filterChange', {
    combineSubType: localCombineSubType.value,
    showDisableAnalysisType: localShowDisableAnalysisType.value
  })
}

function onStartDateChange(val: string) {
  localStartDate.value = val
  if (localEndDate.value) {
    emit('dateChange', val, localEndDate.value)
  }
}

function onEndDateChange(val: string) {
  localEndDate.value = val
  if (localStartDate.value) {
    emit('dateChange', localStartDate.value, val)
  }
}
</script>

<template>
  <div class="filter-panel">
    <!-- 快速筛选 -->
    <div class="filter-card">
      <div class="card-title">快速筛选</div>
      <div class="quick-options">
        <button
          v-for="opt in fastOptions"
          :key="opt.value"
          class="quick-btn"
          :class="{ active: fastChoose === opt.value }"
          @click="onFastClick(opt.value)"
        >
          {{ opt.label }}
        </button>
      </div>
    </div>

    <!-- 自定义日期 -->
    <div class="filter-card">
      <div class="card-title">自定义时间</div>
      <div class="date-row">
        <div class="date-item">
          <span class="date-label">开始</span>
          <el-date-picker
            :model-value="localStartDate"
            type="date"
            placeholder="开始日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            class="date-picker"
            @update:model-value="onStartDateChange"
          />
        </div>
        <div class="date-item">
          <span class="date-label">结束</span>
          <el-date-picker
            :model-value="localEndDate"
            type="date"
            placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            class="date-picker"
            @update:model-value="onEndDateChange"
          />
        </div>
      </div>
    </div>

    <!-- 统计条件 -->
    <div class="filter-card">
      <div class="card-title">统计条件</div>
      <div class="option-list">
        <label class="option-item">
          <span>合并子分类</span>
          <el-switch
            v-model="localCombineSubType"
            size="small"
            @change="onFilterToggle"
          />
        </label>
        <label class="option-item">
          <span>显示全部分类</span>
          <el-switch
            v-model="localShowDisableAnalysisType"
            size="small"
            @change="onFilterToggle"
          />
        </label>
      </div>
    </div>

  </div>
</template>

<style scoped>
.filter-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.filter-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 12px;
}

/* 快速筛选按钮 */
.quick-options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.quick-btn {
  padding: 6px 12px;
  border: none;
  background: var(--color-bg-page);
  border-radius: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.quick-btn:hover {
  background: rgba(0, 0, 0, 0.08);
}

.quick-btn.active {
  background: var(--color-transfer);
  color: #fff;
}

/* 日期选择器 */
.date-row {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.date-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.date-label {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.date-picker {
  width: 100%;
}

.date-picker :deep(.el-input__wrapper) {
  border-radius: 8px;
}

/* 选项列表 */
.option-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.option-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: var(--color-text-primary);
  cursor: pointer;
}

/* 暗色模式 */
html.dark .filter-card {
  background: rgba(40, 40, 40, 0.6);
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .quick-btn {
  background: rgba(60, 60, 60, 0.4);
}

html.dark .quick-btn:hover {
  background: rgba(80, 80, 80, 0.6);
}

</style>
