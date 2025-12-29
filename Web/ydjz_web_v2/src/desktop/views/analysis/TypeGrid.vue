<script setup lang="ts">
import type { AnalysisTypeItem } from '@shared/api/analysis'

const props = defineProps<{
  tabIndex: number
  typeList: (AnalysisTypeItem & { disabled?: boolean; percent?: number })[]
  loading?: boolean
}>()

const emit = defineEmits<{
  typeClick: [typeId: number]
  typeToggle: [typeId: number]
}>()

function onCardClick(typeId: number) {
  emit('typeClick', typeId)
}

function onCardRightClick(e: MouseEvent, typeId: number) {
  e.preventDefault()
  emit('typeToggle', typeId)
}

// 格式化金额
function formatMoney(amount: string): string {
  const num = parseFloat(amount)
  if (isNaN(num)) return '0.00'
  if (Math.abs(num) >= 10000) {
    return (num / 10000).toFixed(2) + '万'
  }
  return num.toFixed(2)
}
</script>

<template>
  <div class="type-grid-section">
    <div class="section-header">
      <h3 class="section-title">分类明细</h3>
      <span class="section-tip">右键点击可排除分类</span>
    </div>

    <div v-if="loading" class="grid-loading">
      <el-icon class="is-loading" :size="24">
        <Loading />
      </el-icon>
      <span>加载中...</span>
    </div>

    <div v-else-if="typeList.length === 0" class="grid-empty">
      <el-empty description="暂无分类数据" :image-size="80" />
    </div>

    <div v-else class="type-grid">
      <div
        v-for="item in typeList"
        :key="item.id"
        class="type-card"
        :class="{ disabled: item.disabled }"
        @click="onCardClick(item.id)"
        @contextmenu="onCardRightClick($event, item.id)"
      >
        <div class="card-header">
          <span class="type-name">{{ item.name }}</span>
        </div>

        <div class="card-body">
          <div class="card-money">¥{{ formatMoney(item.money) }}</div>
          <div
            v-if="!item.disabled"
            class="card-percent"
            :class="tabIndex === 0 ? 'income' : 'expense'"
          >
            {{ item.percent }}%
          </div>
          <div v-else class="card-percent disabled-text">已排除</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { Loading } from '@element-plus/icons-vue'
export default {
  components: { Loading }
}
</script>

<style scoped>
.type-grid-section {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  padding: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}

.section-tip {
  font-size: 12px;
  color: var(--color-text-quaternary);
}

.grid-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px;
  color: var(--color-text-tertiary);
}

.grid-empty {
  padding: 20px;
}

.type-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.type-card {
  padding: 16px;
  background: var(--color-bg-page);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.type-card:hover {
  background: #fff;
  border-color: var(--color-transfer);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.type-card.disabled {
  opacity: 0.5;
}

.type-card.disabled:hover {
  border-color: var(--color-text-quaternary);
}

.card-header {
  margin-bottom: 12px;
}

.type-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-body {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.card-money {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.card-percent {
  font-size: 24px;
  font-weight: 700;
}

.card-percent.income {
  color: var(--color-income);
}

.card-percent.expense {
  color: var(--color-expense);
}

.card-percent.disabled-text {
  font-size: 13px;
  font-weight: 400;
  color: var(--color-text-quaternary);
}

/* 暗色模式 */
html.dark .type-grid-section {
  background: rgba(40, 40, 40, 0.6);
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .type-card {
  background: rgba(60, 60, 60, 0.4);
}

html.dark .type-card:hover {
  background: rgba(70, 70, 70, 0.6);
}

html.dark .progress-bar {
  background: rgba(255, 255, 255, 0.1);
}
</style>
