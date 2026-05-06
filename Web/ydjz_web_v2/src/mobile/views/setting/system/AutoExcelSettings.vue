<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { showToast, showConfirmDialog, showDialog, showLoadingToast, closeToast } from 'vant'
import { useSmartBack } from '@shared/composables/useSmartBack'
import {
  systemConfigApi,
  type AutoExcelConfig,
  type AutoExcelConfigUpdate,
  type AutoExcelTarget,
} from '@shared/api/systemConfig'
import { isHandledError } from '@shared/api/request'

import './page-styles.css'

const { smartBack } = useSmartBack()

const original = ref<AutoExcelConfig | null>(null)
const form = reactive({
  enabled: false,
  dayOfMonth: 1,
  time: '21:00',
  target: 'LAST_MONTH' as AutoExcelTarget,
  sendEmail: false,
})

const saving = ref(false)
const running = ref(false)
const showTimePicker = ref(false)
const timePickerValue = ref(['21', '00'])

const targetOptions: { value: AutoExcelTarget; label: string }[] = [
  { value: 'LAST_MONTH', label: '上月' },
  { value: 'CURRENT_MONTH', label: '本月' },
]

const monthDays = Array.from({ length: 28 }, (_, i) => i + 1)

function pad2(n: number | string): string {
  const s = String(n)
  return s.length < 2 ? `0${s}` : s
}

async function loadData() {
  try {
    const res = await systemConfigApi.getAutoExcel()
    original.value = {
      ...res.data.data,
      time: (res.data.data.time || '21:00').substring(0, 5),
      dayOfMonth: res.data.data.dayOfMonth || 1,
      target: res.data.data.target || 'LAST_MONTH',
    }
    form.enabled = original.value.enabled
    form.dayOfMonth = original.value.dayOfMonth
    form.time = original.value.time
    form.target = original.value.target
    form.sendEmail = original.value.sendEmail
  } catch (err) {
    if (!isHandledError(err)) showToast('加载失败')
  }
}

const dirty = computed(() => {
  if (!original.value) return false
  return (
    form.enabled !== original.value.enabled ||
    form.dayOfMonth !== original.value.dayOfMonth ||
    form.time !== original.value.time ||
    form.target !== original.value.target ||
    form.sendEmail !== original.value.sendEmail
  )
})

function onEnabledChange(val: boolean) {
  form.enabled = val
}

function onDayOfMonthChange(n: number) {
  form.dayOfMonth = n
}

function openTimePicker() {
  const [h, m] = form.time.split(':')
  timePickerValue.value = [pad2(h || '21'), pad2(m || '00')]
  showTimePicker.value = true
}

function onTimeConfirm() {
  form.time = `${timePickerValue.value[0]}:${timePickerValue.value[1]}`
  showTimePicker.value = false
}

function onTargetChange(val: AutoExcelTarget) {
  form.target = val
}

function onSendEmailChange(val: boolean) {
  form.sendEmail = val
}

async function onSave() {
  if (!dirty.value) return
  const payload: AutoExcelConfigUpdate = { enabled: form.enabled }
  if (form.enabled) {
    payload.dayOfMonth = form.dayOfMonth
    payload.time = form.time
    payload.target = form.target
    payload.sendEmail = form.sendEmail
  }
  saving.value = true
  showLoadingToast({ message: '保存中...', forbidClick: true, duration: 0 })
  try {
    await systemConfigApi.updateAutoExcel(payload)
    closeToast()
    showToast({ message: '已保存', type: 'success' })
    smartBack('/setting/system')
  } catch (err) {
    closeToast()
    if (!isHandledError(err)) showToast('保存失败')
  } finally {
    saving.value = false
  }
}

async function runNow() {
  if (running.value) return
  if (dirty.value) {
    showToast('请先保存修改后再生成')
    return
  }
  const targetText = form.target === 'CURRENT_MONTH' ? '本月' : '上月'
  try {
    await showConfirmDialog({
      title: '立即生成',
      message: `将立即生成${targetText}的 Excel 报表，是否继续？`,
    })
  } catch {
    return
  }
  running.value = true
  showLoadingToast({ message: '生成中...', forbidClick: true, duration: 0 })
  try {
    await systemConfigApi.runAutoExcelNow()
    closeToast()
    showToast({ message: '已生成', type: 'success' })
    loadData()
  } catch (err) {
    closeToast()
    if (!isHandledError(err)) showToast('生成失败')
  } finally {
    running.value = false
  }
}

function showInfoDialog() {
  showDialog({
    title: '什么是月度报表？',
    message:
      '系统按你设定的日期 / 时间，自动生成一份 Excel 报表，包含所选月份的全部流水、分类汇总等数据。\n\n' +
      '建议：执行日号选 1-10 号 + 报表对象选「上月」，月初统计上月数据最完整。\n\n' +
      '原因：记账普遍存在滞后性 —— 很多账单会在事后几天才补录。本月报表如果在月内生成，可能会漏掉之后才补的流水。',
    confirmButtonText: '我知道了',
    messageAlign: 'left',
  })
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
      <div class="sys-mob-header-title">月度报表生成</div>
      <div class="sys-mob-header-right is-info" @click="showInfoDialog">
        <van-icon name="question-o" size="20" />
      </div>
    </div>

    <div class="sys-mob-body sys-mob-body-with-footer">
      <van-cell-group v-if="original" inset>
        <van-cell title="启用自动生成" center>
          <template #value>
            <van-switch
              :model-value="form.enabled"
              @update:model-value="onEnabledChange"
            />
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 启用后的配置 -->
      <template v-if="form.enabled">
        <van-cell-group inset title="执行日号">
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

        <van-cell-group inset>
          <van-cell title="执行时间" is-link @click="openTimePicker">
            <template #value>
              <span class="sys-mob-time-value">{{ form.time }}</span>
            </template>
          </van-cell>

          <van-cell title="报表对象" center>
            <template #value>
              <div class="sys-mob-segmented">
                <div
                  v-for="opt in targetOptions"
                  :key="opt.value"
                  class="seg-item"
                  :class="{ active: form.target === opt.value }"
                  @click="onTargetChange(opt.value)"
                >
                  {{ opt.label }}
                </div>
              </div>
            </template>
          </van-cell>

          <van-cell
            title="生成后直接发送邮件"
            label="完成后立即发送给收件人"
            center
          >
            <template #value>
              <van-switch
                :model-value="form.sendEmail"
                @update:model-value="onSendEmailChange"
              />
            </template>
          </van-cell>
        </van-cell-group>

        <!-- 状态信息（来自 original，不参与 dirty） -->
        <van-cell-group v-if="original" inset title="状态">
          <van-cell title="上次执行" :value="original.lastRunDate || '-'" />
          <van-cell title="下次执行" :value="original.nextRunDate || '-'" />
          <van-cell title="目标月份" :value="original.targetYearMonth || '-'" />
        </van-cell-group>

        <div v-if="dirty" class="hint-line">有未保存的修改，请先保存才能立即生成</div>
      </template>
    </div>

    <!-- 底部固定栏：立即生成 + 保存 -->
    <div class="sys-mob-footer">
      <van-button
        v-if="form.enabled"
        plain
        round
        :loading="running"
        :disabled="dirty"
        @click="runNow"
      >
        {{ running ? '生成中...' : '立即生成' }}
      </van-button>
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
        title="选择执行时间"
        @confirm="onTimeConfirm"
        @cancel="showTimePicker = false"
      />
    </van-popup>
  </div>
</template>

<style scoped>
.hint-line {
  padding: 4px 16px 12px;
  font-size: 11px;
  color: var(--color-text-tertiary);
  text-align: center;
}
</style>
