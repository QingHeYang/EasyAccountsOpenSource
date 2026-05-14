<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { FolderOpen } from 'lucide-vue-next'
import {
  systemConfigApi,
  type BackupOverview,
  type BackupFrequency,
} from '@shared/api/systemConfig'
import { isHandledError } from '@shared/api/request'

const props = defineProps<{
  data: BackupOverview
}>()

const emit = defineEmits<{
  (e: 'updated'): void
}>()

const freqOptions = [
  { value: 'daily' as BackupFrequency, label: '每日' },
  { value: 'weekly' as BackupFrequency, label: '每周' },
  { value: 'monthly' as BackupFrequency, label: '每月' },
]

const weekDays = [
  { value: 1, label: '一' },
  { value: 2, label: '二' },
  { value: 3, label: '三' },
  { value: 4, label: '四' },
  { value: 5, label: '五' },
  { value: 6, label: '六' },
  { value: 7, label: '日' },
]

/* ---- 本地状态：从 props 同步 ---- */

const localEnabled = ref(props.data.enabled)
const localFrequency = ref<BackupFrequency>(props.data.frequency || 'daily')
const localTime = ref((props.data.time || '22:00').substring(0, 5))
const localDayOfWeek = ref(props.data.dayOfWeek || 1)
const localDayOfMonth = ref(props.data.dayOfMonth || 1)

watch(
  () => props.data,
  (v) => {
    localEnabled.value = v.enabled
    localFrequency.value = v.frequency || 'daily'
    localTime.value = (v.time || '22:00').substring(0, 5)
    localDayOfWeek.value = v.dayOfWeek || 1
    localDayOfMonth.value = v.dayOfMonth || 1
  },
  { deep: true },
)

/* ---- 即时保存 handlers ---- */

async function onEnabledChange(val: boolean) {
  try {
    await systemConfigApi.updateBackup({ enabled: val })
    emit('updated')
  } catch (err) {
    localEnabled.value = !val
    if (!isHandledError(err)) ElMessage.error('保存失败')
  }
}

async function onFrequencyChange(val: string | number | boolean) {
  const v = val as BackupFrequency
  // 切换频率时给默认日号/星期，避免后端拿到 0
  const extra: { dayOfWeek?: number; dayOfMonth?: number } = {}
  if (v === 'weekly' && (!localDayOfWeek.value || localDayOfWeek.value < 1 || localDayOfWeek.value > 7)) {
    localDayOfWeek.value = 1
    extra.dayOfWeek = 1
  }
  if (v === 'monthly' && (!localDayOfMonth.value || localDayOfMonth.value < 1 || localDayOfMonth.value > 28)) {
    localDayOfMonth.value = 1
    extra.dayOfMonth = 1
  }
  try {
    await systemConfigApi.updateBackup({ frequency: v, ...extra })
    emit('updated')
  } catch (err) {
    if (!isHandledError(err)) ElMessage.error('保存失败')
  }
}

async function onTimeChange(val: string | number | Date | null) {
  if (!val) return
  const v = val as string
  localTime.value = v
  try {
    await systemConfigApi.updateBackup({ time: v })
    emit('updated')
  } catch (err) {
    if (!isHandledError(err)) ElMessage.error('保存失败')
  }
}

async function onDayOfWeekChange(val: string | number | boolean) {
  const v = val as number
  try {
    await systemConfigApi.updateBackup({ dayOfWeek: v })
    emit('updated')
  } catch (err) {
    if (!isHandledError(err)) ElMessage.error('保存失败')
  }
}

let monthDayDebounceTimer: ReturnType<typeof setTimeout> | null = null
function onDayOfMonthChange(val: number | undefined) {
  if (!val || val < 1 || val > 28) return
  localDayOfMonth.value = val
  if (monthDayDebounceTimer) clearTimeout(monthDayDebounceTimer)
  monthDayDebounceTimer = setTimeout(async () => {
    try {
      await systemConfigApi.updateBackup({ dayOfMonth: val })
      emit('updated')
    } catch (err) {
      if (!isHandledError(err)) ElMessage.error('保存失败')
    }
  }, 600)
}
</script>

<template>
  <div class="sys-section">
    <div class="sys-section-header">
      <FolderOpen :size="18" :stroke-width="1.75" />
      <span>备份设置</span>
    </div>
    <div class="sys-section-body">
      <div class="sys-info-grid">
        <!-- 启用开关 -->
        <div class="sys-info-item">
          <div class="sys-info-label">
            <span>启用自动备份</span>
          </div>
          <div class="sys-info-value">
            <el-switch v-model="localEnabled" @change="onEnabledChange" />
          </div>
        </div>

        <!-- 频率 -->
        <div v-if="localEnabled" class="sys-info-item">
          <div class="sys-info-label">
            <span>频率</span>
          </div>
          <div class="sys-info-value">
            <el-segmented
              v-model="localFrequency"
              :options="freqOptions"
              @change="onFrequencyChange"
            />
          </div>
        </div>

        <!-- 星期几（仅 weekly） -->
        <div v-if="localEnabled && localFrequency === 'weekly'" class="sys-info-item">
          <div class="sys-info-label">
            <span>星期</span>
          </div>
          <div class="sys-info-value">
            <el-segmented
              v-model="localDayOfWeek"
              :options="weekDays"
              size="small"
              @change="onDayOfWeekChange"
            />
          </div>
        </div>

        <!-- 日号（仅 monthly） -->
        <div v-if="localEnabled && localFrequency === 'monthly'" class="sys-info-item">
          <div class="sys-info-label">
            <span>日号</span>
            <span class="sys-info-hint">为防 2 月跳月，最大 28</span>
          </div>
          <div class="sys-info-value">
            <el-input-number
              v-model="localDayOfMonth"
              :min="1"
              :max="28"
              size="small"
              controls-position="right"
              style="width: 110px"
              @change="onDayOfMonthChange"
            />
            <span class="sys-value-suffix">号</span>
          </div>
        </div>

        <!-- 时间 -->
        <div v-if="localEnabled" class="sys-info-item">
          <div class="sys-info-label">
            <span>时间</span>
          </div>
          <div class="sys-info-value">
            <el-time-picker
              v-model="localTime"
              format="HH:mm"
              value-format="HH:mm"
              size="small"
              :clearable="false"
              style="width: 120px"
              @change="onTimeChange"
            />
          </div>
        </div>
      </div>

    </div>
  </div>
</template>
