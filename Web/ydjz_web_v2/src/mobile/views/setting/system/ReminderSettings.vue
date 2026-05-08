<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { showToast, showLoadingToast, closeToast } from 'vant'
import { useSmartBack } from '@shared/composables/useSmartBack'
import {
  systemConfigApi,
  type AutoExcelConfig,
  type AutoExcelConfigUpdate,
} from '@shared/api/systemConfig'
import type { ReminderConfig } from '@shared/api/scheduledFlow'
import { isHandledError } from '@shared/api/request'
import { TriangleAlert } from 'lucide-vue-next'

import './page-styles.css'

const { smartBack } = useSmartBack()

/* ---- 后端原始值 ---- */
const originalScheduled = ref<ReminderConfig | null>(null)
const originalAutoExcel = ref<AutoExcelConfig | null>(null)

/* ---- form ---- */
const scheduledForm = reactive<ReminderConfig>({
  remindBeforeDays: 3,
  remindTime: '09:00',
})

const autoExcelForm = reactive({
  enabled: false,
  remindEnabled: false,
  remindBeforeDays: 3,
  remindEmailEnabled: false,
})

const saving = ref(false)
const showTimePicker = ref(false)
const timePickerValue = ref(['09', '00'])

function pad2(n: number | string): string {
  const s = String(n)
  return s.length < 2 ? `0${s}` : s
}

async function loadData() {
  try {
    const [s, a] = await Promise.all([
      systemConfigApi.getScheduledFlow(),
      systemConfigApi.getAutoExcel(),
    ])
    originalScheduled.value = {
      remindBeforeDays: s.data.data.remindBeforeDays || 3,
      remindTime: (s.data.data.remindTime || '09:00').substring(0, 5),
    }
    Object.assign(scheduledForm, originalScheduled.value)

    originalAutoExcel.value = {
      ...a.data.data,
      time: (a.data.data.time || '21:00').substring(0, 5),
    }
    autoExcelForm.enabled = originalAutoExcel.value.enabled
    autoExcelForm.remindEnabled = originalAutoExcel.value.remindEnabled
    autoExcelForm.remindBeforeDays = originalAutoExcel.value.remindBeforeDays || 3
    autoExcelForm.remindEmailEnabled = originalAutoExcel.value.remindEmailEnabled
  } catch (err) {
    if (!isHandledError(err)) showToast('加载失败')
  }
}

const dirty = computed(() => {
  if (!originalScheduled.value || !originalAutoExcel.value) return false
  return (
    scheduledForm.remindBeforeDays !== originalScheduled.value.remindBeforeDays ||
    scheduledForm.remindTime !== originalScheduled.value.remindTime ||
    autoExcelForm.remindEnabled !== originalAutoExcel.value.remindEnabled ||
    autoExcelForm.remindBeforeDays !== (originalAutoExcel.value.remindBeforeDays || 3) ||
    autoExcelForm.remindEmailEnabled !== originalAutoExcel.value.remindEmailEnabled
  )
})

/* 定时记账提醒 */
function onScheduledDaysChange(n: number) {
  scheduledForm.remindBeforeDays = n
}

function openScheduledTimePicker() {
  const [h, m] = scheduledForm.remindTime.split(':')
  timePickerValue.value = [pad2(h || '09'), pad2(m || '00')]
  showTimePicker.value = true
}

function onScheduledTimeConfirm() {
  scheduledForm.remindTime = `${timePickerValue.value[0]}:${timePickerValue.value[1]}`
  showTimePicker.value = false
}

/* 自动 Excel 提醒 */
function onAutoExcelRemindEnabledChange(val: boolean) {
  autoExcelForm.remindEnabled = val
}

function onAutoExcelRemindDaysChange(n: number) {
  autoExcelForm.remindBeforeDays = n
}

function onAutoExcelRemindEmailChange(val: boolean) {
  autoExcelForm.remindEmailEnabled = val
}

async function onSave() {
  if (!dirty.value || !originalScheduled.value || !originalAutoExcel.value) return
  saving.value = true
  showLoadingToast({ message: '保存中...', forbidClick: true, duration: 0 })
  try {
    // 仅当对应块有改动时才发请求（partial）
    const promises: Promise<unknown>[] = []

    const scheduledChanged =
      scheduledForm.remindBeforeDays !== originalScheduled.value.remindBeforeDays ||
      scheduledForm.remindTime !== originalScheduled.value.remindTime
    if (scheduledChanged) {
      promises.push(systemConfigApi.updateScheduledFlow({
        remindBeforeDays: scheduledForm.remindBeforeDays,
        remindTime: scheduledForm.remindTime,
      }))
    }

    const autoExcelPayload: AutoExcelConfigUpdate = {}
    if (autoExcelForm.remindEnabled !== originalAutoExcel.value.remindEnabled) {
      autoExcelPayload.remindEnabled = autoExcelForm.remindEnabled
    }
    if (autoExcelForm.remindBeforeDays !== (originalAutoExcel.value.remindBeforeDays || 3)) {
      autoExcelPayload.remindBeforeDays = autoExcelForm.remindBeforeDays
    }
    if (autoExcelForm.remindEmailEnabled !== originalAutoExcel.value.remindEmailEnabled) {
      autoExcelPayload.remindEmailEnabled = autoExcelForm.remindEmailEnabled
    }
    if (Object.keys(autoExcelPayload).length > 0) {
      promises.push(systemConfigApi.updateAutoExcel(autoExcelPayload))
    }

    await Promise.all(promises)
    closeToast()
    showToast({ message: '已保存', type: 'success' })
    smartBack('/setting/system')
  } catch (err) {
    // handled error：全局 onError 已弹 fail toast，让它自然显示，不要主动 close
    if (!isHandledError(err)) {
      closeToast()
      showToast('保存失败')
    }
  } finally {
    saving.value = false
  }
}

function onBack() {
  smartBack('/setting/system')
}

onMounted(() => {
  window.scrollTo(0, 0)
  loadData()
})
</script>

<template>
  <div class="sys-mob-page">
    <div class="sys-mob-header">
      <div class="sys-mob-header-left" @click="onBack">
        <van-icon name="arrow-left" size="20" />
      </div>
      <div class="sys-mob-header-title">提醒设置</div>
      <div class="sys-mob-header-right"></div>
    </div>

    <div class="sys-mob-body sys-mob-body-with-footer">
      <!-- 定时记账提醒 -->
      <van-cell-group v-if="originalScheduled" inset title="定时记账提醒">
        <!-- 提前 N 天：纵向 block 布局（5 个胶囊塞不进 cell 右侧 value 区） -->
        <van-cell>
          <template #title>
            <div class="sys-mob-block-cell">
              <span class="block-label">提前 N 天</span>
              <div class="sys-mob-segmented is-block">
                <div
                  v-for="n in 5"
                  :key="n"
                  class="seg-item"
                  :class="{ active: scheduledForm.remindBeforeDays === n }"
                  @click="onScheduledDaysChange(n)"
                >
                  {{ n }}
                </div>
              </div>
            </div>
          </template>
        </van-cell>

        <van-cell title="提醒时间" is-link @click="openScheduledTimePicker">
          <template #value>
            <span class="sys-mob-time-value">{{ scheduledForm.remindTime }}</span>
          </template>
        </van-cell>
      </van-cell-group>

      <div class="hint-line">影响所有定时记账规则的事前提醒</div>

      <!-- 自动月度 Excel 提醒 -->
      <van-cell-group v-if="originalAutoExcel" inset title="自动月度 Excel 提醒">
        <van-cell title="提前提醒" center>
          <template #value>
            <van-switch
              :model-value="autoExcelForm.remindEnabled"
              :disabled="!autoExcelForm.enabled"
              @update:model-value="onAutoExcelRemindEnabledChange"
            />
          </template>
        </van-cell>

        <van-cell
          v-if="autoExcelForm.remindEnabled"
          :class="{ 'sys-mob-cell-disabled': !autoExcelForm.enabled }"
        >
          <template #title>
            <div class="sys-mob-block-cell">
              <span class="block-label">提前 N 天</span>
              <div class="sys-mob-segmented is-block">
                <div
                  v-for="n in 5"
                  :key="n"
                  class="seg-item"
                  :class="{ active: autoExcelForm.remindBeforeDays === n }"
                  @click="autoExcelForm.enabled && onAutoExcelRemindDaysChange(n)"
                >
                  {{ n }}
                </div>
              </div>
            </div>
          </template>
        </van-cell>

        <van-cell
          v-if="autoExcelForm.remindEnabled"
          title="邮件提醒"
          label="站内通知必发"
          center
          :class="{ 'sys-mob-cell-disabled': !autoExcelForm.enabled }"
        >
          <template #value>
            <van-switch
              :model-value="autoExcelForm.remindEmailEnabled"
              :disabled="!autoExcelForm.enabled"
              @update:model-value="onAutoExcelRemindEmailChange"
            />
          </template>
        </van-cell>
      </van-cell-group>

      <div v-if="originalAutoExcel && !autoExcelForm.enabled" class="sys-mob-hint is-warn">
        <TriangleAlert :size="14" :stroke-width="1.75" class="hint-icon" />
        <div class="hint-content">
          <div class="hint-title">月度报表生成已关闭</div>
          <div class="hint-text">
            上方的提醒仅在「月度报表生成」开启后才会触发。
          </div>
        </div>
      </div>
    </div>

    <!-- 底部固定保存栏 -->
    <div class="sys-mob-footer">
      <van-button
        type="primary"
        round
        :disabled="!dirty"
        :loading="saving"
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
        @confirm="onScheduledTimeConfirm"
        @cancel="showTimePicker = false"
      />
    </van-popup>
  </div>
</template>

<style scoped>
.stepper-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
}

.suffix {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.hint-line {
  padding: 4px 22px 12px;
  font-size: 11px;
  color: var(--color-text-tertiary);
}
</style>
