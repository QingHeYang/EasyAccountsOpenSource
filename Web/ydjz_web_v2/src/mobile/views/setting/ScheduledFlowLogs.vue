<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import { useSmartBack } from '@shared/composables/useSmartBack'
import {
  scheduledFlowApi,
  FailCategory,
  type ScheduledFlowLog,
  type ScheduledFlowRule,
} from '@shared/api/scheduledFlow'
import { isHandledError } from '@shared/api/request'

const router = useRouter()
const { smartBack } = useSmartBack()

const PAGE_SIZE = 20

const logs = ref<ScheduledFlowLog[]>([])
const rules = ref<ScheduledFlowRule[]>([])
/** 当前筛选的规则 ID；null 表示全部 */
const filterRuleId = ref<number | null>(null)
const page = ref(0)
const loading = ref(false)
const finished = ref(false)
const showFilterSheet = ref(false)

const filterRuleName = computed(() => {
  if (filterRuleId.value === null) return '全部规则'
  return rules.value.find((r) => r.id === filterRuleId.value)?.name ?? `规则 #${filterRuleId.value}`
})

const failCategoryLabel: Record<FailCategory, string> = {
  [FailCategory.MASTER_DATA]: '主数据类',
  [FailCategory.OTHER]: '其他类',
}

/* -------- 数据 -------- */

async function loadRules() {
  try {
    const res = await scheduledFlowApi.listRules()
    rules.value = res.data.data ?? []
  } catch {
    /* 拦截器已处理 */
  }
}

/** van-list 触发：加载下一页 */
async function fetchPage() {
  loading.value = true
  try {
    const res = await scheduledFlowApi.listLogs({
      ruleId: filterRuleId.value ?? undefined,
      page: page.value,
      size: PAGE_SIZE,
    })
    const batch = res.data.data ?? []
    logs.value.push(...batch)
    if (batch.length < PAGE_SIZE) {
      finished.value = true
    } else {
      page.value += 1
    }
  } catch (err) {
    if (!isHandledError(err)) showToast('加载失败')
    finished.value = true
  } finally {
    loading.value = false
  }
}

function onLoad() {
  fetchPage()
}

/* -------- 事件 -------- */

function onBack() {
  smartBack('/setting/scheduled-flow')
}

function onFilterChange(id: number | null) {
  if (id === filterRuleId.value) {
    showFilterSheet.value = false
    return
  }
  filterRuleId.value = id
  showFilterSheet.value = false
  // 重置后立刻加载第 0 页
  logs.value = []
  page.value = 0
  finished.value = false
  fetchPage()
}

async function onDeleteLog(log: ScheduledFlowLog) {
  const fullTime = log.executeTime ? log.executeTime.substring(0, 16) : ''
  try {
    await showConfirmDialog({
      title: '删除记录',
      message: `确定删除"${log.ruleName}"在 ${fullTime} 的执行记录吗？`,
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  try {
    await scheduledFlowApi.deleteLog(log.id)
    showToast('已删除')
    const idx = logs.value.findIndex((l) => l.id === log.id)
    if (idx >= 0) logs.value.splice(idx, 1)
  } catch (err) {
    if (!isHandledError(err)) showToast('删除失败')
  }
}

async function onClearByRule() {
  if (filterRuleId.value === null) return
  const rule = rules.value.find((r) => r.id === filterRuleId.value)
  try {
    await showConfirmDialog({
      title: '清空记录',
      message: `确定清空规则"${rule?.name ?? `#${filterRuleId.value}`}"的全部执行记录吗？此操作不可恢复。`,
      confirmButtonText: '清空',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  try {
    await scheduledFlowApi.clearLogsByRule(filterRuleId.value)
    showToast('已清空')
    logs.value = []
    page.value = 0
    finished.value = true
  } catch (err) {
    if (!isHandledError(err)) showToast('清空失败')
  }
}

function onViewFlow(log: ScheduledFlowLog) {
  if (!log.success || !log.flowId) return
  router.push(`/flow/edit/${log.flowId}`)
}

function formatLogTime(s: string): string {
  // MM-DD HH:mm 显示，完整时间放 title 给桌面浏览器 hover
  if (!s) return ''
  if (s.length >= 16) return s.substring(5, 16)
  return s
}

onMounted(() => {
  window.scrollTo(0, 0)
  loadRules()
  // 不主动调 fetchPage —— van-list 挂载后会自动触发首次 onLoad
})
</script>

<template>
  <div class="scheduled-logs-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="header-left" @click="onBack">
        <van-icon name="arrow-left" size="20" />
      </div>
      <div class="header-title">执行记录</div>
      <!-- 仅过滤了某规则时才展示"清空"按钮 -->
      <div
        v-if="filterRuleId !== null && (logs.length || finished)"
        class="header-right header-right-action"
        @click="onClearByRule"
      >
        <van-icon name="delete-o" size="20" />
      </div>
      <div v-else class="header-right-placeholder"></div>
    </div>

    <div class="page-body">
      <!-- 筛选条 -->
      <div class="filter-bar" @click="showFilterSheet = true">
        <span class="filter-label">按规则筛选</span>
        <span class="filter-value" :class="{ active: filterRuleId !== null }">
          {{ filterRuleName }}
        </span>
        <van-icon name="arrow" size="14" class="filter-arrow" />
      </div>

      <!-- 列表 / 空状态 -->
      <template v-if="logs.length || !finished">
        <van-list
          v-model:loading="loading"
          :finished="finished"
          finished-text="— 已到底 —"
          @load="onLoad"
        >
          <div
            v-for="log in logs"
            :key="log.id"
            class="log-card"
            :class="{ success: log.success, fail: !log.success }"
          >
            <!-- 顶行：状态图标 · 时间 · 规则名 · 删除 -->
            <div class="log-head">
              <van-icon
                :name="log.success ? 'checked' : 'clear'"
                :class="['log-status-icon', log.success ? 'icon-success' : 'icon-fail']"
                size="16"
              />
              <span class="log-time" :title="log.executeTime">
                {{ formatLogTime(log.executeTime) }}
              </span>
              <span
                class="log-rule"
                :class="{ deleted: log.ruleName === '[已删除]' }"
                :title="log.ruleName"
              >
                {{ log.ruleName }}
              </span>
              <van-icon
                name="cross"
                size="16"
                class="log-delete"
                @click.stop="onDeleteLog(log)"
              />
            </div>

            <!-- 详情行 -->
            <div class="log-detail">
              <!-- 成功：可点击的流水链接 -->
              <span
                v-if="log.success"
                class="log-flow-link"
                :class="{ disabled: !log.flowId }"
                @click.stop="onViewFlow(log)"
              >
                <van-icon name="eye-o" size="11" />
                查看流水
                <span v-if="log.flowId" class="log-flow-id">#{{ log.flowId }}</span>
              </span>
              <!-- 失败：分类徽章 + 原因 -->
              <template v-else>
                <span
                  v-if="log.failCategory"
                  class="fail-badge"
                  :class="`fail-badge-${log.failCategory}`"
                >
                  {{ failCategoryLabel[log.failCategory] }}
                </span>
                <span class="fail-reason">{{ log.failReason || '（无详细原因）' }}</span>
              </template>
            </div>
          </div>
        </van-list>
      </template>

      <!-- 空状态：加载完且无数据 -->
      <van-empty
        v-else
        image="search"
        description=""
        class="logs-empty"
      >
        <template #description>
          <div class="empty-title">
            {{ filterRuleId !== null ? '该规则暂无执行记录' : '暂无执行记录' }}
          </div>
          <div class="empty-sub">
            <template v-if="filterRuleId !== null">
              换一个规则看看，或回去等下一次自动执行
            </template>
            <template v-else>
              规则执行后会在这里留下记录
            </template>
          </div>
        </template>
      </van-empty>
    </div>

    <!-- 筛选弹层 -->
    <van-action-sheet
      v-model:show="showFilterSheet"
      title="按规则筛选"
      teleport="body"
    >
      <div class="filter-sheet-list">
        <div
          class="filter-sheet-item"
          :class="{ active: filterRuleId === null }"
          @click="onFilterChange(null)"
        >
          <span>全部规则</span>
          <van-icon
            v-if="filterRuleId === null"
            name="success"
            class="check-icon"
          />
        </div>
        <div
          v-for="rule in rules"
          :key="rule.id"
          class="filter-sheet-item"
          :class="{ active: filterRuleId === rule.id }"
          @click="onFilterChange(rule.id)"
        >
          <span class="sheet-rule-name">{{ rule.name }}</span>
          <van-icon
            v-if="filterRuleId === rule.id"
            name="success"
            class="check-icon"
          />
        </div>
        <div v-if="!rules.length" class="filter-sheet-empty">
          暂无规则
        </div>
      </div>
    </van-action-sheet>
  </div>
</template>

<style scoped>
.scheduled-logs-page {
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

.header-right-action {
  color: var(--color-expense);
}

.header-left:active,
.header-right:active {
  opacity: 0.7;
}

.header-right-placeholder {
  width: 40px;
  height: 40px;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.page-body {
  padding: 76px 16px 32px;
}

/* 筛选条 */
.filter-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  margin-bottom: 12px;
  background: var(--color-bg-card);
  border-radius: 12px;
  font-size: 14px;
  transition: opacity 0.15s;
}

.filter-bar:active {
  opacity: 0.75;
}

.filter-label {
  color: var(--color-text-secondary);
}

.filter-value {
  flex: 1;
  text-align: right;
  color: var(--color-text-primary);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.filter-value.active {
  color: var(--color-transfer);
}

.filter-arrow {
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

/* 日志卡 */
.log-card {
  padding: 12px 14px;
  margin-bottom: 8px;
  background: var(--color-bg-card);
  border-radius: 12px;
}

.log-card:last-child {
  margin-bottom: 0;
}

.log-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.log-status-icon {
  flex-shrink: 0;
}

.log-status-icon.icon-success {
  color: var(--color-income);
}

.log-status-icon.icon-fail {
  color: var(--color-expense);
}

.log-time {
  flex-shrink: 0;
  font-size: 12px;
  color: var(--color-text-tertiary);
  font-variant-numeric: tabular-nums;
}

.log-rule {
  flex: 1;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.log-rule.deleted {
  color: var(--color-text-tertiary);
  font-weight: 500;
  font-style: italic;
}

.log-delete {
  flex-shrink: 0;
  color: var(--color-text-tertiary);
  padding: 4px;
  transition: color 0.15s;
}

.log-delete:active {
  color: var(--color-expense);
}

.log-detail {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  padding-left: 24px;
}

/* 流水链接 */
.log-flow-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  background: var(--color-transfer-bg);
  color: var(--color-transfer);
  border-radius: 6px;
  font-weight: 500;
  font-size: 12px;
}

.log-flow-link:active {
  opacity: 0.75;
}

.log-flow-link.disabled {
  opacity: 0.5;
  pointer-events: none;
}

.log-flow-id {
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 11px;
  opacity: 0.9;
}

/* 失败 */
.fail-badge {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 5px;
  font-size: 11px;
  font-weight: 500;
}

.fail-badge.fail-badge-1 {
  color: var(--color-expense);
  background: var(--color-expense-bg);
}

.fail-badge.fail-badge-2 {
  color: #faad14;
  background: rgba(250, 173, 20, 0.12);
}

.fail-reason {
  flex: 1;
  min-width: 0;
  color: var(--color-text-secondary);
  font-size: 12px;
  word-break: break-all;
}

/* van-list 末尾文案 */
:deep(.van-list__finished-text),
:deep(.van-list__loading) {
  font-size: 12px;
  color: var(--color-text-tertiary);
  padding: 14px 0;
}

/* 空状态 */
.logs-empty {
  padding-top: 40px;
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
  line-height: 1.5;
  text-align: center;
}

/* 筛选弹层 */
.filter-sheet-list {
  padding: 8px 16px 24px;
  max-height: 60vh;
  overflow-y: auto;
}

.filter-sheet-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 14px;
  margin-bottom: 8px;
  background: var(--color-bg-page);
  border-radius: 10px;
  font-size: 15px;
  color: var(--color-text-primary);
}

.filter-sheet-item:last-child {
  margin-bottom: 0;
}

.filter-sheet-item:active {
  opacity: 0.75;
}

.filter-sheet-item.active {
  color: var(--color-transfer);
  background: var(--color-transfer-bg);
  font-weight: 600;
}

.sheet-rule-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.check-icon {
  color: var(--color-transfer);
  font-size: 18px;
  flex-shrink: 0;
}

.filter-sheet-empty {
  padding: 24px 0;
  text-align: center;
  color: var(--color-text-tertiary);
  font-size: 14px;
}
</style>

<style>
.scheduled-logs-page .page-header {
  background: rgba(245, 245, 245, 0.8);
}

html.dark .scheduled-logs-page .page-header {
  background: rgba(10, 10, 10, 0.8);
}
</style>
