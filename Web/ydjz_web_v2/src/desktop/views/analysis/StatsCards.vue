<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  totalIn: string
  totalOut: string
  loading?: boolean
}>()

// 展开状态（显示完整金额）
const incomeExpanded = ref(false)
const expenseExpanded = ref(false)

// 格式化金额
function formatAmount(amount: string, expanded: boolean): string {
  const num = parseFloat(amount)
  if (isNaN(num)) return '0.00'

  if (expanded) {
    return num.toFixed(2)
  }

  if (Math.abs(num) >= 10000) {
    return (num / 10000).toFixed(2) + '万'
  }
  return num.toFixed(2)
}

function toggleIncome() {
  incomeExpanded.value = !incomeExpanded.value
}

function toggleExpense() {
  expenseExpanded.value = !expenseExpanded.value
}
</script>

<template>
  <div class="stats-cards">
    <div class="stats-card income" @click="toggleIncome" title="点击切换完整金额">
      <div class="card-label">总收入</div>
      <div class="card-value">
        <span class="currency">¥</span>
        <span class="amount">{{ formatAmount(totalIn, incomeExpanded) }}</span>
      </div>
    </div>

    <div class="stats-card expense" @click="toggleExpense" title="点击切换完整金额">
      <div class="card-label">总支出</div>
      <div class="card-value">
        <span class="currency">¥</span>
        <span class="amount">{{ formatAmount(totalOut, expenseExpanded) }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stats-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.stats-card {
  padding: 24px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.2s;
  cursor: pointer;
}

.stats-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.stats-card:active {
  transform: translateY(0);
}

.card-label {
  font-size: 14px;
  color: var(--color-text-tertiary);
  margin-bottom: 8px;
}

.card-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.currency {
  font-size: 16px;
  font-weight: 500;
}

.amount {
  font-size: 28px;
  font-weight: 600;
}

/* 收入卡片 */
.stats-card.income .card-value {
  color: var(--color-income);
}

/* 支出卡片 */
.stats-card.expense .card-value {
  color: var(--color-expense);
}

/* 暗色模式 */
html.dark .stats-card {
  background: rgba(40, 40, 40, 0.6);
  border-color: rgba(255, 255, 255, 0.1);
}
</style>
