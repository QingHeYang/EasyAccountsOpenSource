<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Bell, AlarmClock, Document } from '@element-plus/icons-vue'
import {
  systemConfigApi,
  type AutoExcelOverview,
  type ScheduledFlowOverview,
} from '@shared/api/systemConfig'
import { isHandledError } from '@shared/api/request'

const props = defineProps<{
  scheduled: ScheduledFlowOverview
  autoExcel: AutoExcelOverview
}>()

const emit = defineEmits<{
  (e: 'updated'): void
}>()

/* ---- 本地状态 ---- */

const localScheduledDays = ref(props.scheduled.remindBeforeDays || 3)
const localScheduledTime = ref((props.scheduled.remindTime || '09:00').substring(0, 5))

const localAutoExcelEnabled = ref(props.autoExcel.enabled)
const localAutoExcelRemindEnabled = ref(props.autoExcel.remindEnabled)
const localAutoExcelRemindDays = ref(props.autoExcel.remindBeforeDays || 3)
const localAutoExcelRemindEmail = ref(props.autoExcel.remindEmailEnabled)

watch(
  () => props.scheduled,
  (v) => {
    localScheduledDays.value = v.remindBeforeDays || 3
    localScheduledTime.value = (v.remindTime || '09:00').substring(0, 5)
  },
  { deep: true },
)

watch(
  () => props.autoExcel,
  (v) => {
    localAutoExcelEnabled.value = v.enabled
    localAutoExcelRemindEnabled.value = v.remindEnabled
    localAutoExcelRemindDays.value = v.remindBeforeDays || 3
    localAutoExcelRemindEmail.value = v.remindEmailEnabled
  },
  { deep: true },
)

/* ---- 定时记账提醒（提前天数 / 提醒时间） ---- */

async function onScheduledDaysChange(val: string | number | boolean) {
  const v = val as number
  localScheduledDays.value = v
  try {
    await systemConfigApi.updateScheduledFlow({
      remindBeforeDays: v,
      remindTime: localScheduledTime.value,
    })
    emit('updated')
  } catch (err) {
    if (!isHandledError(err)) ElMessage.error('保存失败')
  }
}

async function onScheduledTimeChange(val: string | number | Date | null) {
  if (!val) return
  const v = val as string
  localScheduledTime.value = v
  try {
    await systemConfigApi.updateScheduledFlow({
      remindBeforeDays: localScheduledDays.value,
      remindTime: v,
    })
    emit('updated')
  } catch (err) {
    if (!isHandledError(err)) ElMessage.error('保存失败')
  }
}

/* ---- 自动 Excel 提醒（开关 / 天数 / 邮件开关） ---- */

async function onAutoExcelRemindEnabledChange(val: boolean) {
  try {
    await systemConfigApi.updateAutoExcel({ remindEnabled: val })
    emit('updated')
  } catch (err) {
    localAutoExcelRemindEnabled.value = !val
    if (!isHandledError(err)) ElMessage.error('保存失败')
  }
}

let autoExcelDaysDebounceTimer: ReturnType<typeof setTimeout> | null = null
function onAutoExcelRemindDaysChange(val: number | undefined) {
  if (!val || val < 1 || val > 28) return
  localAutoExcelRemindDays.value = val
  if (autoExcelDaysDebounceTimer) clearTimeout(autoExcelDaysDebounceTimer)
  autoExcelDaysDebounceTimer = setTimeout(async () => {
    try {
      await systemConfigApi.updateAutoExcel({ remindBeforeDays: val })
      emit('updated')
    } catch (err) {
      if (!isHandledError(err)) ElMessage.error('保存失败')
    }
  }, 600)
}

async function onAutoExcelRemindEmailChange(val: boolean) {
  try {
    await systemConfigApi.updateAutoExcel({ remindEmailEnabled: val })
    emit('updated')
  } catch (err) {
    localAutoExcelRemindEmail.value = !val
    if (!isHandledError(err)) ElMessage.error('保存失败')
  }
}
</script>

<template>
  <div class="sys-section">
    <div class="sys-section-header">
      <el-icon :size="18"><Bell /></el-icon>
      <span>提醒设置</span>
    </div>
    <div class="sys-section-body">
      <!-- 4a. 定时记账提醒 -->
      <div class="sys-sub-section">
        <div class="sys-sub-title">
          <el-icon :size="14"><AlarmClock /></el-icon>
          <span>定时记账提醒</span>
          <span class="sys-sub-hint">影响所有定时记账规则</span>
        </div>
        <div class="sys-info-grid">
          <div class="sys-info-item">
            <div class="sys-info-label"><span>提前 N 天</span></div>
            <div class="sys-info-value">
              <el-segmented
                v-model="localScheduledDays"
                :options="[
                  { label: '1', value: 1 },
                  { label: '2', value: 2 },
                  { label: '3', value: 3 },
                  { label: '4', value: 4 },
                  { label: '5', value: 5 },
                ]"
                size="small"
                @change="onScheduledDaysChange"
              />
            </div>
          </div>
          <div class="sys-info-item">
            <div class="sys-info-label"><span>提醒时间</span></div>
            <div class="sys-info-value">
              <el-time-picker
                v-model="localScheduledTime"
                format="HH:mm"
                value-format="HH:mm"
                size="small"
                style="width: 120px"
                :clearable="false"
                @change="onScheduledTimeChange"
              />
            </div>
          </div>
        </div>
      </div>

      <el-divider />

      <!-- 4b. 自动月度 Excel 提醒 -->
      <div
        class="sys-sub-section"
        :class="{ 'sys-sub-disabled': !localAutoExcelEnabled }"
      >
        <div class="sys-sub-title">
          <el-icon :size="14"><Document /></el-icon>
          <span>自动月度 Excel 提醒</span>
          <span v-if="!localAutoExcelEnabled" class="sys-sub-hint sys-warn">
            自动生成已关闭，提醒不会触发
          </span>
        </div>
        <div class="sys-info-grid">
          <div class="sys-info-item">
            <div class="sys-info-label"><span>提前提醒</span></div>
            <div class="sys-info-value">
              <el-switch
                v-model="localAutoExcelRemindEnabled"
                :disabled="!localAutoExcelEnabled"
                @change="onAutoExcelRemindEnabledChange"
              />
            </div>
          </div>
          <div v-if="localAutoExcelRemindEnabled" class="sys-info-item">
            <div class="sys-info-label"><span>提前天数</span></div>
            <div class="sys-info-value">
              <el-input-number
                v-model="localAutoExcelRemindDays"
                :min="1"
                :max="28"
                size="small"
                controls-position="right"
                style="width: 110px"
                :disabled="!localAutoExcelEnabled"
                @change="onAutoExcelRemindDaysChange"
              />
              <span class="sys-value-suffix">天</span>
            </div>
          </div>
          <div v-if="localAutoExcelRemindEnabled" class="sys-info-item">
            <div class="sys-info-label">
              <span>邮件提醒</span>
              <span class="sys-info-hint">站内通知必发</span>
            </div>
            <div class="sys-info-value">
              <el-switch
                v-model="localAutoExcelRemindEmail"
                :disabled="!localAutoExcelEnabled"
                @change="onAutoExcelRemindEmailChange"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
