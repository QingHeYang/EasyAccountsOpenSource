<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import { useSmartBack } from '@shared/composables/useSmartBack'
import {
  scheduledFlowApi,
  CycleType,
  RuleStatus,
  parseCycleDates,
  type ScheduledFlowRule,
} from '@shared/api/scheduledFlow'
import { isHandledError } from '@shared/api/request'

const router = useRouter()
const { smartBack } = useSmartBack()

const loading = ref(false)
const rules = ref<ScheduledFlowRule[]>([])

/* -------- 与桌面端一致的展示逻辑 -------- */

const cycleLabelMap: Record<CycleType, string> = {
  [CycleType.DAILY]: '每日',
  [CycleType.WEEKLY]: '每周',
  [CycleType.MONTHLY]: '每月',
  [CycleType.YEARLY]: '每年',
}

const weekdayLabel = ['', '一', '二', '三', '四', '五', '六', '日']

function formatCycle(rule: ScheduledFlowRule): string {
  const base = cycleLabelMap[rule.cycleType] ?? ''
  if (rule.cycleType === CycleType.DAILY) return base
  if (rule.cycleType === CycleType.WEEKLY) {
    const days = parseCycleDates<number>(rule.cycleDates)
    if (!days.length) return base
    return `${base} · 周${days.map((d) => weekdayLabel[d] ?? d).join('、')}`
  }
  if (rule.cycleType === CycleType.MONTHLY) {
    const days = parseCycleDates<number>(rule.cycleDates)
    if (!days.length) return base
    return `${base} · ${days.join('、')} 号`
  }
  if (rule.cycleType === CycleType.YEARLY) {
    const dates = parseCycleDates<string>(rule.cycleDates)
    if (!dates.length) return base
    return `${base} · ${dates.join('、')}`
  }
  return base
}

const statusStyleMap: Record<RuleStatus, { text: string; color: string; bg: string }> = {
  [RuleStatus.NOT_STARTED]: {
    text: '未开始',
    color: 'var(--color-text-tertiary)',
    bg: 'rgba(140, 140, 140, 0.12)',
  },
  [RuleStatus.RUNNING]: {
    text: '进行中',
    color: 'var(--color-income)',
    bg: 'var(--color-income-bg)',
  },
  [RuleStatus.PAUSED]: {
    text: '暂停',
    color: 'var(--color-note, #FAAD14)',
    bg: 'rgba(250, 173, 20, 0.12)',
  },
  [RuleStatus.FINISHED]: {
    text: '完成',
    color: 'var(--color-transfer)',
    bg: 'var(--color-transfer-bg)',
  },
  [RuleStatus.INVALID]: {
    text: '失效',
    color: 'var(--color-expense)',
    bg: 'var(--color-expense-bg)',
  },
}

/* -------- 数据 -------- */

async function loadRules() {
  loading.value = true
  try {
    const res = await scheduledFlowApi.listRules()
    rules.value = res.data.data ?? []
  } catch (err) {
    if (!isHandledError(err)) showToast('加载失败')
    rules.value = []
  } finally {
    loading.value = false
  }
}

/* -------- 事件 -------- */

function onBack() {
  smartBack('/setting')
}

function onAddRule() {
  router.push('/setting/scheduled-flow/add')
}

function onRuleClick(rule: ScheduledFlowRule) {
  router.push(`/setting/scheduled-flow/edit/${rule.id}`)
}

function onOpenReminderConfig() {
  router.push('/setting/scheduled-flow/reminder-config')
}

function onOpenLogs() {
  router.push('/setting/scheduled-flow/logs')
}

async function onToggleRuleStatus(rule: ScheduledFlowRule) {
  if (rule.status === RuleStatus.NOT_STARTED) return
  if (rule.status === RuleStatus.RUNNING) {
    try {
      await showConfirmDialog({
        title: '暂停规则',
        message: `确定暂停规则"${rule.name}"吗？暂停期间不会自动记账。`,
        confirmButtonText: '暂停',
        cancelButtonText: '取消',
      })
    } catch {
      return
    }
    try {
      await scheduledFlowApi.pauseRule(rule.id)
      showToast('已暂停')
      loadRules()
    } catch (err) {
      if (!isHandledError(err)) showToast('暂停失败')
    }
  } else {
    // 暂停 / 完成 / 失效 → 跳编辑页确认后顺势启动
    router.push(`/setting/scheduled-flow/edit/${rule.id}?start=1`)
  }
}

onMounted(loadRules)
</script>

<template>
  <div class="scheduled-flow-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="header-left" @click="onBack">
        <van-icon name="arrow-left" size="20" />
      </div>
      <div class="header-title">定时记账</div>
      <div class="header-right" @click="onAddRule">
        <van-icon name="plus" size="20" />
      </div>
    </div>

    <div class="page-body">
      <!-- 快捷入口：提醒设置 + 执行记录 -->
      <div class="quick-actions">
        <div class="quick-action" @click="onOpenReminderConfig">
          <van-icon name="setting-o" size="18" class="quick-action-icon" />
          <span>提醒设置</span>
          <van-icon name="arrow" size="14" class="quick-action-arrow" />
        </div>
        <div class="quick-action" @click="onOpenLogs">
          <van-icon name="notes-o" size="18" class="quick-action-icon" />
          <span>执行记录</span>
          <van-icon name="arrow" size="14" class="quick-action-arrow" />
        </div>
      </div>

      <!-- 规则列表 -->
      <div v-if="rules.length" class="rule-list">
        <div
          v-for="rule in rules"
          :key="rule.id"
          class="rule-card"
          @click="onRuleClick(rule)"
        >
          <div class="rule-head">
            <span class="rule-name">{{ rule.name }}</span>
            <span
              class="status-tag"
              :style="{
                color: statusStyleMap[rule.status]?.color,
                background: statusStyleMap[rule.status]?.bg,
              }"
            >
              {{ statusStyleMap[rule.status]?.text ?? '未知' }}
            </span>
          </div>
          <div class="rule-cycle">
            {{ formatCycle(rule) }} · {{ rule.runTime?.substring(0, 5) }}
          </div>
          <div class="rule-meta">
            <span class="rule-money">¥{{ rule.money }}</span>
            <span v-if="rule.typeName" class="rule-pill">{{ rule.typeName }}</span>
            <!-- 转账：两个账户合并为一个 pill -->
            <span v-if="rule.accountToName" class="rule-pill rule-pill-transfer">
              {{ rule.accountName || '—' }}
              <van-icon name="arrow" size="10" class="transfer-arrow" />
              {{ rule.accountToName }}
            </span>
            <span v-else-if="rule.accountName" class="rule-pill">{{ rule.accountName }}</span>
          </div>

          <div v-if="rule.status === RuleStatus.INVALID" class="rule-invalid-hint">
            <van-icon name="warning-o" size="12" />
            主数据失效，请编辑后重新启动
          </div>

          <div class="rule-actions" @click.stop>
            <!-- 未开始：静态提示 -->
            <span
              v-if="rule.status === RuleStatus.NOT_STARTED"
              class="rule-auto-start-hint"
            >
              <van-icon name="clock-o" size="12" />
              {{ rule.startDate || '--' }} 自动启动
            </span>
            <!-- 运行中：暂停 -->
            <van-button
              v-else-if="rule.status === RuleStatus.RUNNING"
              size="small"
              type="warning"
              plain
              icon="pause-circle-o"
              class="rule-toggle-btn"
              @click="onToggleRuleStatus(rule)"
            >
              暂停
            </van-button>
            <!-- 暂停 / 完成 / 失效：开始 -->
            <van-button
              v-else
              size="small"
              type="primary"
              plain
              icon="play-circle-o"
              class="rule-toggle-btn"
              @click="onToggleRuleStatus(rule)"
            >
              开始
            </van-button>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <van-empty
        v-else-if="!loading"
        image="search"
        description="还没有定时规则"
      >
        <template #description>
          <div class="empty-desc">
            <div class="empty-title">还没有定时规则</div>
            <div class="empty-sub">点击右上角 + 新建一条，让系统自动替你记账</div>
          </div>
        </template>
      </van-empty>

      <!-- 加载占位 -->
      <van-skeleton v-if="loading && !rules.length" title :row="3" class="loading-skeleton" />
    </div>
  </div>
</template>

<style scoped>
.scheduled-flow-page {
  min-height: 100vh;
  background: var(--color-bg-page);
}

/* 顶部导航 */
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

.header-left,
.header-right {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: var(--color-bg-card);
  color: var(--color-text-primary);
}

.header-left:active,
.header-right:active {
  opacity: 0.7;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.page-body {
  padding: 76px 16px 100px;
}

/* 快捷入口条 */
.quick-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 14px;
}

.quick-action {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 14px;
  background: var(--color-bg-card);
  border-radius: 12px;
  font-size: 14px;
  color: var(--color-text-primary);
  transition: opacity 0.15s;
}

.quick-action:active {
  opacity: 0.7;
}

.quick-action-icon {
  color: var(--color-transfer);
}

.quick-action-arrow {
  margin-left: auto;
  color: var(--color-text-tertiary);
}

/* 规则列表 */
.rule-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.rule-card {
  padding: 14px;
  background: var(--color-bg-card);
  border-radius: 14px;
  transition: opacity 0.15s;
}

.rule-card:active {
  opacity: 0.85;
}

.rule-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
  gap: 10px;
}

.rule-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}

.status-tag {
  flex-shrink: 0;
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 500;
}

.rule-cycle {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}

.rule-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.rule-money {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-right: 4px;
}

.rule-pill {
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 12px;
  color: var(--color-text-secondary);
  background: var(--color-bg-page);
}

.rule-pill-transfer {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  color: var(--color-transfer);
  background: var(--color-transfer-bg);
}

.transfer-arrow {
  opacity: 0.7;
}

.rule-invalid-hint {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 10px;
  padding: 6px 10px;
  font-size: 12px;
  color: var(--color-expense);
  background: var(--color-expense-bg);
  border-radius: 6px;
}

.rule-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px dashed var(--color-border);
}

.rule-toggle-btn {
  min-width: 82px;
}

.rule-auto-start-hint {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  font-size: 12px;
  color: var(--color-text-tertiary);
  background: var(--color-bg-page);
  border-radius: 6px;
  font-variant-numeric: tabular-nums;
}

/* 空状态 */
.empty-desc {
  text-align: center;
}

.empty-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}

.empty-sub {
  font-size: 13px;
  color: var(--color-text-tertiary);
}

.loading-skeleton {
  padding: 14px;
  background: var(--color-bg-card);
  border-radius: 14px;
}
</style>

<style>
.scheduled-flow-page .page-header {
  background: rgba(245, 245, 245, 0.8);
}

html.dark .scheduled-flow-page .page-header {
  background: rgba(10, 10, 10, 0.8);
}
</style>
