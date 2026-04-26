<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { showToast, showLoadingToast, closeToast } from 'vant'
import { useSmartBack } from '@shared/composables/useSmartBack'
import {
  scheduledFlowApi,
  type ReminderConfig,
} from '@shared/api/scheduledFlow'
import { isHandledError } from '@shared/api/request'

const { smartBack } = useSmartBack()

const loading = ref(false)
const saving = ref(false)
const form = ref<ReminderConfig>({
  remindBeforeDays: 3,
  remindTime: '09:00',
})

const showTimePicker = ref(false)
const timePickerValue = ref<string[]>(['09', '00'])

function pad2(n: number | string): string {
  const s = String(n)
  return s.length < 2 ? `0${s}` : s
}

/* -------- 数据 -------- */

async function loadConfig() {
  loading.value = true
  try {
    const res = await scheduledFlowApi.getReminderConfig()
    const cfg = res.data.data
    if (cfg) {
      form.value = {
        remindBeforeDays: cfg.remindBeforeDays || 3,
        remindTime: (cfg.remindTime || '09:00').substring(0, 5),
      }
    }
  } catch (err) {
    if (!isHandledError(err)) showToast('加载配置失败')
  } finally {
    loading.value = false
  }
}

/* -------- 事件 -------- */

function onBack() {
  smartBack('/setting/scheduled-flow')
}

function onPickDays(n: number) {
  form.value.remindBeforeDays = n
}

function openTimePicker() {
  const [h, m] = (form.value.remindTime || '09:00').split(':')
  timePickerValue.value = [pad2(h || '09'), pad2(m || '00')]
  showTimePicker.value = true
}

function onTimeConfirm() {
  form.value.remindTime = `${timePickerValue.value[0]}:${timePickerValue.value[1]}`
  showTimePicker.value = false
}

async function onSave() {
  const f = form.value
  if (!f.remindBeforeDays || f.remindBeforeDays < 1 || f.remindBeforeDays > 5) {
    showToast('请选择 1~5 天')
    return
  }
  if (!f.remindTime) {
    showToast('请选择提醒时间')
    return
  }

  saving.value = true
  showLoadingToast({ message: '保存中...', forbidClick: true, duration: 0 })
  try {
    await scheduledFlowApi.updateReminderConfig(f)
    closeToast()
    showToast('保存成功')
    smartBack('/setting/scheduled-flow')
  } catch (err) {
    closeToast()
    if (!isHandledError(err)) showToast('保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  window.scrollTo(0, 0)
  loadConfig()
})
</script>

<template>
  <div class="reminder-config-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="header-left" @click="onBack">
        <van-icon name="arrow-left" size="20" />
      </div>
      <div class="header-title">提醒设置</div>
      <div class="header-right-placeholder"></div>
    </div>

    <div class="page-body">
      <!-- 全局生效提示 -->
      <div class="hint-card">
        <van-icon name="info-o" size="14" class="hint-icon" />
        <div class="hint-content">
          <div class="hint-rule">全局生效</div>
          <div class="hint-example">
            此配置对所有开启提醒的定时规则生效，单条规则无法单独覆盖
          </div>
        </div>
      </div>

      <!-- 提前 N 天 -->
      <van-cell-group inset title="提前几天提醒" class="form-group">
        <div class="days-cell">
          <div
            v-for="n in 5"
            :key="n"
            class="days-item"
            :class="{ active: form.remindBeforeDays === n }"
            @click="onPickDays(n)"
          >
            {{ n }} 天
          </div>
        </div>
      </van-cell-group>

      <!-- 提醒时间 -->
      <van-cell-group inset title="提醒时间" class="form-group">
        <van-cell is-link class="picker-cell" @click="openTimePicker">
          <template #title>
            <span class="cell-title">每天此时触发</span>
          </template>
          <template #value>
            <span class="time-value">{{ form.remindTime }}</span>
          </template>
        </van-cell>
        <div class="cell-hint">
          每天的这个时分检查并发送当日所需的提醒
        </div>
      </van-cell-group>

      <!-- 保存按钮 -->
      <van-button
        type="primary"
        block
        round
        :loading="saving"
        :disabled="loading"
        class="save-btn"
        @click="onSave"
      >
        保存
      </van-button>
    </div>

    <!-- 时间 picker -->
    <van-popup
      v-model:show="showTimePicker"
      round
      position="bottom"
      teleport="body"
    >
      <van-time-picker
        v-model="timePickerValue"
        :columns-type="['hour', 'minute']"
        title="选择提醒时间"
        @confirm="onTimeConfirm"
        @cancel="showTimePicker = false"
      />
    </van-popup>
  </div>
</template>

<style scoped>
.reminder-config-page {
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

.header-left {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: var(--color-bg-card);
  color: var(--color-text-primary);
}

.header-left:active {
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

/* hint */
.hint-card {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
  padding: 12px 14px;
  background: var(--color-transfer-bg);
  border: 1px solid rgba(24, 144, 255, 0.18);
  border-radius: 12px;
}

.hint-icon {
  flex-shrink: 0;
  margin-top: 2px;
  color: var(--color-transfer);
}

.hint-content {
  flex: 1;
  min-width: 0;
}

.hint-rule {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 2px;
}

.hint-example {
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

/* form-group */
.form-group {
  margin-bottom: 12px;
}

/* 提前 N 天 */
.days-cell {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
  padding: 12px 14px;
}

.days-item {
  padding: 10px 0;
  text-align: center;
  font-size: 13px;
  color: var(--color-text-secondary);
  background: var(--color-bg-page);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  font-variant-numeric: tabular-nums;
}

.days-item:active {
  opacity: 0.75;
}

.days-item.active {
  color: #fff;
  background: var(--color-transfer);
  border-color: var(--color-transfer);
  font-weight: 600;
}

/* picker cell */
.picker-cell :deep(.van-cell__value) {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.cell-title {
  color: var(--color-text-primary);
}

.time-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-transfer);
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.5px;
}

.cell-hint {
  padding: 8px 16px 14px;
  font-size: 12px;
  color: var(--color-text-tertiary);
  line-height: 1.5;
}

/* 保存按钮 */
.save-btn {
  margin-top: 12px;
  height: 44px;
  font-size: 15px;
  font-weight: 600;
}
</style>

<style>
.reminder-config-page .page-header {
  background: rgba(245, 245, 245, 0.8);
}

html.dark .reminder-config-page .page-header {
  background: rgba(10, 10, 10, 0.8);
}
</style>
