<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { showToast, showLoadingToast, closeToast } from 'vant'
import { useSmartBack } from '@shared/composables/useSmartBack'
import {
  systemConfigApi,
  type BackupConfig,
  type BackupConfigUpdate,
  type BackupFrequency,
} from '@shared/api/systemConfig'
import { isHandledError } from '@shared/api/request'

import './page-styles.css'

const { smartBack } = useSmartBack()

const original = ref<BackupConfig | null>(null)
const form = reactive<BackupConfig>({
  enabled: false,
  frequency: 'daily',
  time: '22:00',
  dayOfWeek: 1,
  dayOfMonth: 1,
  cron: '',
})
const saving = ref(false)

const showTimePicker = ref(false)
const timePickerValue = ref(['22', '00'])

const freqOptions: { value: BackupFrequency; label: string }[] = [
  { value: 'daily', label: '每日' },
  { value: 'weekly', label: '每周' },
  { value: 'monthly', label: '每月' },
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

const monthDays = Array.from({ length: 28 }, (_, i) => i + 1)

function pad2(n: number | string): string {
  const s = String(n)
  return s.length < 2 ? `0${s}` : s
}

async function loadData() {
  try {
    const res = await systemConfigApi.getBackup()
    original.value = {
      ...res.data.data,
      time: (res.data.data.time || '22:00').substring(0, 5),
      frequency: res.data.data.frequency || 'daily',
      dayOfWeek: res.data.data.dayOfWeek || 1,
      dayOfMonth: res.data.data.dayOfMonth || 1,
    }
    Object.assign(form, original.value)
  } catch (err) {
    if (!isHandledError(err)) showToast('加载失败')
  }
}

const dirty = computed(() => {
  if (!original.value) return false
  return (
    form.enabled !== original.value.enabled ||
    form.frequency !== original.value.frequency ||
    form.time !== original.value.time ||
    form.dayOfWeek !== original.value.dayOfWeek ||
    form.dayOfMonth !== original.value.dayOfMonth
  )
})

function onEnabledChange(val: boolean) {
  form.enabled = val
}

function onFrequencyChange(val: BackupFrequency) {
  form.frequency = val
  if (val === 'weekly' && (!form.dayOfWeek || form.dayOfWeek < 1)) form.dayOfWeek = 1
  if (val === 'monthly' && (!form.dayOfMonth || form.dayOfMonth < 1)) form.dayOfMonth = 1
}

function openTimePicker() {
  const [h, m] = form.time.split(':')
  timePickerValue.value = [pad2(h || '22'), pad2(m || '00')]
  showTimePicker.value = true
}

function onTimeConfirm() {
  form.time = `${timePickerValue.value[0]}:${timePickerValue.value[1]}`
  showTimePicker.value = false
}

function onDayOfWeekChange(n: number) {
  form.dayOfWeek = n
}

function onDayOfMonthChange(n: number) {
  form.dayOfMonth = n
}

async function onSave() {
  if (!dirty.value) return
  const payload: BackupConfigUpdate = { enabled: form.enabled }
  if (form.enabled) {
    payload.frequency = form.frequency
    payload.time = form.time
    if (form.frequency === 'weekly') payload.dayOfWeek = form.dayOfWeek
    if (form.frequency === 'monthly') payload.dayOfMonth = form.dayOfMonth
  }
  saving.value = true
  showLoadingToast({ message: '保存中...', forbidClick: true, duration: 0 })
  try {
    await systemConfigApi.updateBackup(payload)
    closeToast()
    showToast({ message: '已保存', type: 'success' })
    smartBack('/setting/system')
  } catch (err) {
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
      <div class="sys-mob-header-title">备份设置</div>
      <div class="sys-mob-header-right"></div>
    </div>

    <div class="sys-mob-body sys-mob-body-with-footer">
      <van-cell-group v-if="original" inset>
        <van-cell title="启用自动备份" center>
          <template #value>
            <van-switch
              :model-value="form.enabled"
              @update:model-value="onEnabledChange"
            />
          </template>
        </van-cell>

        <van-cell v-if="form.enabled" title="频率" center>
          <template #value>
            <div class="sys-mob-segmented">
              <div
                v-for="opt in freqOptions"
                :key="opt.value"
                class="seg-item"
                :class="{ active: form.frequency === opt.value }"
                @click="onFrequencyChange(opt.value)"
              >
                {{ opt.label }}
              </div>
            </div>
          </template>
        </van-cell>

        <van-cell
          v-if="form.enabled"
          title="时间"
          is-link
          @click="openTimePicker"
        >
          <template #value>
            <span class="sys-mob-time-value">{{ form.time }}</span>
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 星期几（仅 weekly） -->
      <van-cell-group
        v-if="original && form.enabled && form.frequency === 'weekly'"
        inset
        title="星期"
      >
        <div class="week-grid">
          <div
            v-for="d in weekDays"
            :key="d.value"
            class="week-cell"
            :class="{ active: form.dayOfWeek === d.value }"
            @click="onDayOfWeekChange(d.value)"
          >
            周{{ d.label }}
          </div>
        </div>
      </van-cell-group>

      <!-- 日号（仅 monthly） -->
      <van-cell-group
        v-if="original && form.enabled && form.frequency === 'monthly'"
        inset
        title="日号"
      >
        <div class="sys-mob-day-grid">
          <div
            v-for="d in monthDays"
            :key="d"
            class="sys-mob-day-cell"
            :class="{ active: form.dayOfMonth === d }"
            @click="onDayOfMonthChange(d)"
          >
            {{ d }}
          </div>
        </div>
        <div class="hint-line">为防 2 月跳月，最大 28 号</div>
      </van-cell-group>
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
        title="选择备份时间"
        @confirm="onTimeConfirm"
        @cancel="showTimePicker = false"
      />
    </van-popup>
  </div>
</template>

<style scoped>
.week-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
  padding: 12px 14px;
}

.week-cell {
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-page);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.week-cell:active {
  opacity: 0.75;
}

.week-cell.active {
  background: var(--color-transfer);
  border-color: var(--color-transfer);
  color: #fff;
  font-weight: 600;
}

.hint-line {
  padding: 4px 16px 12px;
  font-size: 11px;
  color: var(--color-text-tertiary);
  text-align: center;
}
</style>
