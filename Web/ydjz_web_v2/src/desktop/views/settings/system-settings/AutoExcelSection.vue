<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  EditPen,
  Check,
  InfoFilled,
  CircleCheckFilled,
  CircleCloseFilled,
} from '@element-plus/icons-vue'
import { Calendars } from 'lucide-vue-next'
import {
  systemConfigApi,
  type AutoExcelOverview,
  type AutoExcelConfigUpdate,
  type AutoExcelTarget,
} from '@shared/api/systemConfig'
import { isHandledError } from '@shared/api/request'

const props = defineProps<{
  data: AutoExcelOverview
}>()

const emit = defineEmits<{
  (e: 'updated'): void
}>()

const targetOptions = [
  { value: 'LAST_MONTH' as AutoExcelTarget, label: '上月' },
  { value: 'CURRENT_MONTH' as AutoExcelTarget, label: '本月' },
]

/* ---- 编辑对话框 ---- */

const showDialog = ref(false)
const saving = ref(false)
const running = ref(false)

const form = reactive({
  enabled: false,
  dayOfMonth: 1,
  time: '21:00',
  target: 'LAST_MONTH' as AutoExcelTarget,
  sendEmail: false,
})

function openDialog() {
  Object.assign(form, {
    enabled: props.data.enabled,
    dayOfMonth: props.data.dayOfMonth || 1,
    time: (props.data.time || '21:00').substring(0, 5),
    target: props.data.target || 'LAST_MONTH',
    sendEmail: props.data.sendEmail,
  })
  showDialog.value = true
}

async function save() {
  const payload: AutoExcelConfigUpdate = { enabled: form.enabled }
  if (form.enabled) {
    payload.dayOfMonth = form.dayOfMonth
    payload.time = form.time
    payload.target = form.target
    payload.sendEmail = form.sendEmail
  }
  saving.value = true
  try {
    await systemConfigApi.updateAutoExcel(payload)
    ElMessage.success('已保存')
    showDialog.value = false
    emit('updated')
  } catch (err) {
    if (!isHandledError(err)) ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function runNow() {
  if (running.value) return
  const targetText = props.data.target === 'CURRENT_MONTH' ? '本月' : '上月'
  try {
    await ElMessageBox.confirm(
      `将立即生成${targetText}的 Excel 报表，是否继续？`,
      '立即生成',
      { type: 'info' },
    )
  } catch {
    return
  }
  running.value = true
  try {
    await systemConfigApi.runAutoExcelNow()
    ElMessage.success('已生成')
    emit('updated')
  } catch (err) {
    if (!isHandledError(err)) ElMessage.error('生成失败')
  } finally {
    running.value = false
  }
}

function targetLabel(t: AutoExcelTarget | undefined): string {
  return t === 'CURRENT_MONTH' ? '本月' : '上月'
}
</script>

<template>
  <div class="sys-section">
    <div class="sys-section-header">
      <Calendars :size="18" :stroke-width="1.75" />
      <span>月度报表生成设置</span>

      <!-- 功能解释 popover -->
      <el-popover
        trigger="hover"
        placement="top-start"
        :width="320"
        popper-class="sf-info-popover"
      >
        <template #reference>
          <el-icon class="sys-header-info"><InfoFilled /></el-icon>
        </template>
        <div class="ip-content">
          <div class="ip-title">什么是月度报表？</div>
          <div class="ip-desc">
            系统按你设定的日期 / 时间，自动生成一份 Excel 报表，包含所选月份的全部流水、分类汇总等数据。
          </div>
          <ul class="ip-list">
            <li>
              <strong>报表对象</strong>：可选「上月」（典型场景：月初统计上月）或「本月」
            </li>
            <li>
              <strong>邮件发送</strong>：开启后生成完成立即发送给收件人邮箱
            </li>
            <li>
              <strong>事前提醒</strong>：在「提醒设置」中开启，提前 N 天站内 / 邮件提醒
            </li>
          </ul>
          <div class="ip-tip">
            💡 也可以在这里点击「立即生成」立刻产出本期报表，不必等下次自动执行
          </div>
        </div>
      </el-popover>

      <!-- 立即生成（仅启用时显示） -->
      <el-button
        v-if="data.enabled"
        size="small"
        text
        type="primary"
        class="sys-section-action"
        :loading="running"
        @click="runNow"
      >
        <el-icon v-if="!running"><Check /></el-icon>
        <span>{{ running ? '生成中...' : '立即生成' }}</span>
      </el-button>

      <el-button
        type="primary"
        size="small"
        text
        class="sys-section-edit"
        @click="openDialog"
      >
        <el-icon><EditPen /></el-icon>
        <span>编辑</span>
      </el-button>
    </div>

    <div class="sys-section-body">
      <!-- 状态横幅 -->
      <div class="ae-status" :class="{ 'ae-status--ok': data.enabled }">
        <el-icon :size="16">
          <CircleCheckFilled v-if="data.enabled" />
          <CircleCloseFilled v-else />
        </el-icon>
        <span>{{ data.enabled ? '自动生成已启用' : '自动生成未启用' }}</span>
      </div>

      <!-- 已启用：展示具体字段 -->
      <div v-if="data.enabled" class="ae-info-list">
        <div class="ae-info-item">
          <span class="ae-info-label">执行时间</span>
          <span class="ae-info-value">
            每月 {{ data.dayOfMonth }} 号
            {{ (data.time || '').substring(0, 5) }}
          </span>
        </div>
        <div class="ae-info-item">
          <span class="ae-info-label">报表对象</span>
          <span class="ae-info-value">{{ targetLabel(data.target) }}</span>
        </div>
        <div class="ae-info-item">
          <span class="ae-info-label">邮件发送</span>
          <el-tag
            :type="data.sendEmail ? 'success' : 'info'"
            size="small"
            effect="plain"
            round
          >
            {{ data.sendEmail ? '开启' : '关闭' }}
          </el-tag>
        </div>
        <div v-if="data.nextRunDate" class="ae-info-item">
          <span class="ae-info-label">下次执行</span>
          <span class="ae-info-value">{{ data.nextRunDate }}</span>
        </div>
        <div v-if="data.targetYearMonth" class="ae-info-item">
          <span class="ae-info-label">目标月份</span>
          <span class="ae-info-value">{{ data.targetYearMonth }}</span>
        </div>
      </div>
    </div>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="showDialog"
      title="月度报表生成设置"
      width="520px"
      class="sys-dialog auto-excel-dialog"
      append-to-body
    >
      <div class="sf-form">
        <!-- 组 1：调度 -->
        <div class="sf-card">
          <div class="sf-card-title">调度</div>
          <div class="sf-card-body">
            <div class="sf-row">
              <span class="sf-label">启用</span>
              <div class="ae-switch-wrap">
                <el-switch v-model="form.enabled" />
              </div>
            </div>
            <template v-if="form.enabled">
              <!-- 执行日号：1-28 grid 选择 -->
              <div class="sf-row sf-row--block">
                <span class="sf-label">
                  执行日号
                  <el-tooltip
                    content="为防 2 月跳月，最大 28 号"
                    placement="top"
                  >
                    <el-icon class="sf-info"><InfoFilled /></el-icon>
                  </el-tooltip>
                </span>
                <div class="sf-day-grid">
                  <div
                    v-for="d in 28"
                    :key="d"
                    class="sf-day-cell"
                    :class="{ 'is-active': form.dayOfMonth === d }"
                    @click="form.dayOfMonth = d"
                  >
                    {{ d }}
                  </div>
                </div>
              </div>

              <div class="sf-row">
                <span class="sf-label">执行时间</span>
                <el-time-picker
                  v-model="form.time"
                  format="HH:mm"
                  value-format="HH:mm"
                  :clearable="false"
                  class="sf-input--narrow"
                />
              </div>

              <!-- 报表对象：附建议提示 -->
              <div class="sf-row">
                <span class="sf-label">
                  报表对象
                  <el-popover
                    trigger="hover"
                    placement="top-start"
                    :width="340"
                    popper-class="sf-info-popover"
                  >
                    <template #reference>
                      <el-icon class="sf-info"><InfoFilled /></el-icon>
                    </template>
                    <div class="ip-content">
                      <div class="ip-title">建议生成「上月」报表</div>
                      <div class="ip-desc">
                        记账普遍存在滞后性 —— 很多账单会在事后几天才补录。
                        本月报表如果在月内生成，可能会漏掉之后才补的流水。
                      </div>
                      <ul class="ip-list">
                        <li>
                          <strong>推荐</strong>：执行日号选 <strong>1 ~ 10 号</strong>，
                          对象选 <strong>上月</strong> —— 月初统计上月，数据最完整
                        </li>
                        <li>
                          <strong>不推荐</strong>：本月（除非你确认本月不会再补录账单）
                        </li>
                      </ul>
                    </div>
                  </el-popover>
                </span>
                <el-segmented
                  v-model="form.target"
                  :options="targetOptions"
                />
              </div>
            </template>
          </div>
        </div>

        <!-- 组 2：邮件发送 -->
        <div v-if="form.enabled" class="sf-card">
          <div class="sf-card-title">邮件发送</div>
          <div class="sf-card-body sf-card-body--list">
            <div class="sf-toggle-row">
              <div class="sf-toggle-label">
                <span>生成后直接发送邮件</span>
                <span class="sf-toggle-hint">报表生成完成后立即发送给「邮件设置」中的收件人</span>
              </div>
              <el-switch v-model="form.sendEmail" />
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
/* === section header 上的 info icon 和 立即生成按钮 === */
.sys-header-info {
  font-size: 14px;
  color: var(--color-text-tertiary);
  cursor: help;
  margin-left: 4px;
  transition: color 0.2s;
}

.sys-header-info:hover {
  color: var(--color-transfer);
}

.sys-section-action {
  margin-left: auto !important;
  padding: 4px 10px !important;
  height: 28px !important;
}

/* 让 edit 紧贴 action 右边（覆盖 styles.css 里 .sys-section-edit 的 auto） */
.sys-section-action ~ .sys-section-edit {
  margin-left: 4px !important;
}

/* 自动 Excel 状态横幅 */
.ae-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 8px;
  font-size: 13px;
  color: var(--color-text-tertiary);
  margin-bottom: 10px;
}

.ae-status .el-icon {
  color: var(--color-text-tertiary);
}

.ae-status--ok {
  background: rgba(82, 196, 26, 0.08);
  color: var(--color-income);
}

.ae-status--ok .el-icon {
  color: var(--color-income);
}

/* 信息项列表 */
.ae-info-list {
  display: flex;
  flex-direction: column;
  gap: 1px;
  background: var(--color-border-light);
  border-radius: 8px;
  overflow: hidden;
}

.ae-info-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: var(--color-bg-card);
  font-size: 13px;
}

.ae-info-label {
  color: var(--color-text-secondary);
}

.ae-info-value {
  color: var(--color-text-primary);
  font-weight: 500;
}

/* 对话框内：开关 wrapper（让开关右对齐显示） */
.ae-switch-wrap {
  flex: 1;
  display: flex;
}

.ae-suffix {
  font-size: 13px;
  color: var(--color-text-tertiary);
}

html.dark .ae-status {
  background: rgba(255, 255, 255, 0.04);
}

html.dark .ae-status--ok {
  background: rgba(105, 219, 124, 0.12);
  color: #69db7c;
}

html.dark .ae-status--ok .el-icon {
  color: #69db7c;
}

html.dark .ae-info-list {
  background: rgba(255, 255, 255, 0.06);
}

html.dark .ae-info-item {
  background: rgba(255, 255, 255, 0.04);
}
</style>
