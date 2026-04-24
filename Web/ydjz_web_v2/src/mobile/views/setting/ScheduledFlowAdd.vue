<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  showToast,
  showConfirmDialog,
  showLoadingToast,
  closeToast,
} from 'vant'
import { useSmartBack } from '@shared/composables/useSmartBack'
import {
  scheduledFlowApi,
  CycleType,
  stringifyCycleDates,
  type ScheduledFlowRuleParams,
} from '@shared/api/scheduledFlow'
import { isHandledError } from '@shared/api/request'
import { actionApi, type Action, ActionHandle, ExemptMode } from '@shared/api/action'
import { accountApi, type Account, AccountType } from '@shared/api/account'
import { typeApi, type TypeWithChildren } from '@shared/api/type'

const router = useRouter()
const { smartBack } = useSmartBack()

/* ---------------- 表单状态 ---------------- */

interface FormState {
  name: string
  money: string
  note: string
  selectedAction: Action | null
  selectedAccount: Account | null
  selectedAccountTo: Account | null
  selectedType: { id: number; tname: string } | null
  cycleType: CycleType
  cycleDatesWeekly: number[]
  cycleDatesMonthly: number[]
  cycleDatesYearly: string[]
  runTime: string // HH:mm
  startDate: string // yyyy-MM-dd
  endDate: string
  reminderEnabled: boolean
  emailEnabled: boolean
}

function makeInitialForm(): FormState {
  return {
    name: '',
    money: '',
    note: '',
    selectedAction: null,
    selectedAccount: null,
    selectedAccountTo: null,
    selectedType: null,
    cycleType: CycleType.MONTHLY,
    cycleDatesWeekly: [],
    cycleDatesMonthly: [],
    cycleDatesYearly: [],
    runTime: '09:00',
    startDate: '',
    endDate: '',
    reminderEnabled: false,
    emailEnabled: false,
  }
}

const form = ref<FormState>(makeInitialForm())
const submitting = ref(false)

/* ---------------- 基础数据 ---------------- */

const actions = ref<Action[]>([])
const accounts = ref<Account[]>([])
const types = ref<TypeWithChildren[]>([])

async function fetchActions() {
  try {
    const res = await actionApi.getAll()
    actions.value = res.data.data || []
  } catch {}
}

async function fetchAccounts() {
  try {
    const res = await accountApi.getAll()
    accounts.value = res.data.data || []
  } catch {}
}

async function fetchTypesByAction(actionId: number) {
  try {
    const res = await typeApi.getByActionId(actionId)
    types.value = res.data.data || []
  } catch {
    types.value = []
  }
}

/* ---------------- 选择器 state ---------------- */

const showActionSheet = ref(false)
const showAccountSheet = ref(false)
const accountSheetType = ref<1 | 2>(1)
const showTypeCascader = ref(false)
const cascaderValue = ref<number | string>('')
const cascaderFieldNames = { text: 'tname', value: 'id', children: 'childrenTypes' }

const showStartCalendar = ref(false)
const showEndCalendar = ref(false)
const showTimePicker = ref(false)
const timePickerValue = ref<string[]>(['09', '00'])

const showYearDateSheet = ref(false)
const yearDatePickerValue = ref<string[]>(['01', '01'])

const isTransfer = computed(
  () => form.value.selectedAction?.handle === ActionHandle.TRANSFER
)

/* ---------------- 工具 ---------------- */

const weekdayLabel = ['', '一', '二', '三', '四', '五', '六', '日']

function pad2(n: number | string): string {
  const s = String(n)
  return s.length < 2 ? `0${s}` : s
}

function daysInMonth(month: number): number {
  const maxDays = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
  return maxDays[month - 1] ?? 31
}

function getActionClass(handle: number | undefined): string {
  if (handle === ActionHandle.IN) return 'income'
  if (handle === ActionHandle.OUT) return 'expense'
  if (handle === ActionHandle.TRANSFER) return 'transfer'
  return ''
}

function getHandleText(handle: number | undefined): string {
  if (handle === ActionHandle.IN) return '流入'
  if (handle === ActionHandle.OUT) return '流出'
  if (handle === ActionHandle.TRANSFER) return '转账'
  return ''
}

function getExemptText(action: Action): string {
  if (!action.exempt) return ''
  if (action.handle !== ActionHandle.TRANSFER) return '不计入'
  switch (action.exemptMode) {
    case ExemptMode.FROM_EXEMPT: return '转出不计入'
    case ExemptMode.TO_EXEMPT: return '转入不计入'
    case ExemptMode.BOTH_EXEMPT: return '两边不计入'
    default: return '不计入'
  }
}

function isAccountDisabled(account: Account, panelType: 1 | 2): boolean {
  if (account.accountType !== AccountType.LIABILITY) return false
  if (!form.value.selectedAction?.exempt) return false
  if (form.value.selectedAction.handle !== ActionHandle.TRANSFER) return true
  const mode = form.value.selectedAction.exemptMode ?? ExemptMode.NONE
  if (panelType === 1) {
    return mode === ExemptMode.FROM_EXEMPT || mode === ExemptMode.BOTH_EXEMPT
  }
  return mode === ExemptMode.TO_EXEMPT || mode === ExemptMode.BOTH_EXEMPT
}

function getAccountDisabledReason(account: Account, panelType: 1 | 2): string {
  if (!isAccountDisabled(account, panelType)) return ''
  return '负债账户不支持此收支类型'
}

/* ---------------- 日历 min/max ---------------- */

const startCalendarMinDate = computed(() => {
  // TODO(测试期放开)：产品规则要求明天起，当前放开到今天
  const d = new Date()
  d.setHours(0, 0, 0, 0)
  return d
})

const startCalendarMaxDate = computed(() => {
  const d = new Date()
  d.setFullYear(d.getFullYear() + 5)
  return d
})

const endCalendarMinDate = computed(() => {
  if (!form.value.startDate) return startCalendarMinDate.value
  const d = new Date(form.value.startDate.replace(/-/g, '/'))
  d.setDate(d.getDate() + 1) // 结束日期必须 > 开始日期
  d.setHours(0, 0, 0, 0)
  return d
})

const endCalendarMaxDate = computed(() => {
  const d = new Date()
  d.setFullYear(d.getFullYear() + 10)
  return d
})

function formatDateToYMD(date: Date): string {
  const y = date.getFullYear()
  const m = pad2(date.getMonth() + 1)
  const d = pad2(date.getDate())
  return `${y}-${m}-${d}`
}

/* ---------------- 事件 ---------------- */

function onBack() {
  smartBack('/setting/scheduled-flow')
}

// 收支
function openActionSheet() {
  showActionSheet.value = true
}

function onSelectAction(action: Action) {
  if (action.id === form.value.selectedAction?.id) {
    showActionSheet.value = false
    return
  }
  form.value.selectedAction = action
  form.value.selectedAccountTo = null
  form.value.selectedType = null
  cascaderValue.value = ''
  showActionSheet.value = false
  fetchTypesByAction(action.id)
}

// 账户
function openAccountSheet(type: 1 | 2) {
  if (!form.value.selectedAction) {
    showToast('请先选择收支类型')
    return
  }
  accountSheetType.value = type
  showAccountSheet.value = true
}

function onSelectAccount(account: Account) {
  if (isAccountDisabled(account, accountSheetType.value)) return
  if (accountSheetType.value === 1) {
    form.value.selectedAccount = account
  } else {
    form.value.selectedAccountTo = account
  }
  showAccountSheet.value = false
}

// 分类
function openTypeCascader() {
  if (!form.value.selectedAction) {
    showToast('请先选择收支类型')
    return
  }
  showTypeCascader.value = true
}

function onTypeCascaderFinish({
  selectedOptions,
}: {
  selectedOptions: Array<{ tname: string; id: number }>
}) {
  showTypeCascader.value = false
  if (selectedOptions.length > 0) {
    const lastOption = selectedOptions[selectedOptions.length - 1]
    form.value.selectedType = {
      id: lastOption.id,
      tname: selectedOptions.map((o) => o.tname).join('/'),
    }
  }
}

// 周期
function onCycleTypeChange(type: CycleType) {
  form.value.cycleType = type
  form.value.cycleDatesWeekly = []
  form.value.cycleDatesMonthly = []
  form.value.cycleDatesYearly = []
}

function toggleWeekday(day: number) {
  const arr = form.value.cycleDatesWeekly
  const idx = arr.indexOf(day)
  if (idx >= 0) arr.splice(idx, 1)
  else arr.push(day)
  arr.sort((a, b) => a - b)
}

function toggleMonthDay(day: number) {
  const arr = form.value.cycleDatesMonthly
  const idx = arr.indexOf(day)
  if (idx >= 0) arr.splice(idx, 1)
  else arr.push(day)
  arr.sort((a, b) => a - b)
}

function openYearDateSheet() {
  yearDatePickerValue.value = ['01', '01']
  showYearDateSheet.value = true
}

function confirmYearDate() {
  const [m, d] = yearDatePickerValue.value
  const mmdd = `${pad2(m)}-${pad2(d)}`
  if (form.value.cycleDatesYearly.includes(mmdd)) {
    showToast('该日期已添加')
    return
  }
  form.value.cycleDatesYearly.push(mmdd)
  form.value.cycleDatesYearly.sort()
  showYearDateSheet.value = false
}

function removeYearDate(mmdd: string) {
  const arr = form.value.cycleDatesYearly
  const idx = arr.indexOf(mmdd)
  if (idx >= 0) arr.splice(idx, 1)
}

// yearDatePicker 的 day 超过月末自动修正
watch(
  () => yearDatePickerValue.value[0],
  (month) => {
    const mNum = Number(month)
    if (!Number.isFinite(mNum)) return
    const max = daysInMonth(mNum)
    const d = Number(yearDatePickerValue.value[1])
    if (d > max) {
      yearDatePickerValue.value = [yearDatePickerValue.value[0], pad2(max)]
    }
  }
)

// yearDatePicker 的 columns
const yearMonthColumn = Array.from({ length: 12 }, (_, i) => ({
  text: `${i + 1} 月`,
  value: pad2(i + 1),
}))
const yearDayColumn = computed(() => {
  const m = Number(yearDatePickerValue.value[0]) || 1
  const max = daysInMonth(m)
  return Array.from({ length: max }, (_, i) => ({
    text: `${i + 1} 日`,
    value: pad2(i + 1),
  }))
})

// 执行时间
function openTimePicker() {
  const [h, m] = (form.value.runTime || '09:00').split(':')
  timePickerValue.value = [pad2(h || '09'), pad2(m || '00')]
  showTimePicker.value = true
}

function onTimePickerConfirm() {
  form.value.runTime = `${timePickerValue.value[0]}:${timePickerValue.value[1]}`
  showTimePicker.value = false
}

// 日期
function openStartCalendar() {
  showStartCalendar.value = true
}

function openEndCalendar() {
  if (!form.value.startDate) {
    showToast('请先选择开始日期')
    return
  }
  showEndCalendar.value = true
}

function onStartCalendarConfirm(date: Date) {
  form.value.startDate = formatDateToYMD(date)
  // 若结束日期早于新开始日期，清空
  if (form.value.endDate && form.value.endDate <= form.value.startDate) {
    form.value.endDate = ''
  }
  showStartCalendar.value = false
}

function onEndCalendarConfirm(date: Date) {
  form.value.endDate = formatDateToYMD(date)
  showEndCalendar.value = false
}

function clearEndDate() {
  form.value.endDate = ''
}

// 提醒：勾选邮件提醒时弹窗确认
async function onEmailEnabledChange(val: boolean) {
  if (!val) return
  try {
    await showConfirmDialog({
      title: '开启邮件提醒',
      message:
        '邮件通知依赖 WebHook 邮件服务。请确认已在部署时启用邮件发送；未配置时即使打开也不会收到邮件。',
      confirmButtonText: '我已确认',
      cancelButtonText: '取消',
    })
  } catch {
    form.value.emailEnabled = false
  }
}

// 金额输入限制：只允许数字 + 两位小数
function onMoneyChange(raw: string) {
  let value = (raw ?? '').replace(/[^\d.]/g, '')
  const parts = value.split('.')
  if (parts.length > 2) value = parts[0] + '.' + parts.slice(1).join('')
  if (parts[1] && parts[1].length > 2) value = parts[0] + '.' + parts[1].substring(0, 2)
  form.value.money = value
}

/* ---------------- 校验 & 提交 ---------------- */

function validate(): string | null {
  const f = form.value
  if (!f.name.trim()) return '请输入规则名称'
  if (!f.money) return '请输入金额'
  if (!/^\d+(\.\d+)?$/.test(f.money) || Number(f.money) <= 0) return '金额必须是大于 0 的数字'
  if (!f.selectedAction) return '请选择收支类型'
  if (!f.selectedAccount) return isTransfer.value ? '请选择转出账户' : '请选择账户'
  if (isTransfer.value && !f.selectedAccountTo) return '请选择转入账户'
  if (
    isTransfer.value &&
    f.selectedAccount.id === f.selectedAccountTo?.id
  )
    return '转出与转入账户不能相同'
  if (!f.selectedType) return '请选择分类'
  if (f.cycleType === CycleType.WEEKLY && !f.cycleDatesWeekly.length)
    return '请至少选择一个周几'
  if (f.cycleType === CycleType.MONTHLY && !f.cycleDatesMonthly.length)
    return '请至少选择一个日期'
  if (f.cycleType === CycleType.YEARLY && !f.cycleDatesYearly.length)
    return '请至少添加一个日期'
  if (!f.runTime) return '请选择执行时间'
  if (!f.startDate) return '请选择开始日期'
  if (f.endDate && f.endDate <= f.startDate) return '结束日期必须晚于开始日期'
  return null
}

function buildCycleDatesString(): string {
  const f = form.value
  if (f.cycleType === CycleType.DAILY) return stringifyCycleDates([], CycleType.DAILY)
  if (f.cycleType === CycleType.WEEKLY)
    return stringifyCycleDates(f.cycleDatesWeekly, f.cycleType)
  if (f.cycleType === CycleType.MONTHLY)
    return stringifyCycleDates(f.cycleDatesMonthly, f.cycleType)
  return stringifyCycleDates(f.cycleDatesYearly, f.cycleType)
}

async function onSubmit() {
  const msg = validate()
  if (msg) {
    showToast(msg)
    return
  }
  const f = form.value
  const params: ScheduledFlowRuleParams = {
    name: f.name.trim(),
    money: f.money,
    typeId: f.selectedType!.id,
    actionId: f.selectedAction!.id,
    accountId: f.selectedAccount!.id,
    accountToId: isTransfer.value ? f.selectedAccountTo?.id : undefined,
    note: f.note?.trim() || undefined,
    cycleType: f.cycleType,
    cycleDates: buildCycleDatesString(),
    runTime: f.runTime,
    startDate: f.startDate,
    endDate: f.endDate || undefined,
    reminderEnabled: f.reminderEnabled,
    emailEnabled: f.emailEnabled,
  }

  submitting.value = true
  showLoadingToast({ message: '提交中...', forbidClick: true, duration: 0 })
  try {
    await scheduledFlowApi.createRule(params)
    closeToast()
    showToast('创建成功')
    router.replace('/setting/scheduled-flow')
  } catch (err) {
    closeToast()
    if (!isHandledError(err)) showToast('创建失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  window.scrollTo(0, 0)
  fetchActions()
  fetchAccounts()
})
</script>

<template>
  <div class="scheduled-flow-add-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="header-left" @click="onBack">
        <van-icon name="arrow-left" size="20" />
      </div>
      <div class="header-title">新建规则</div>
      <div class="header-right-placeholder"></div>
    </div>

    <div class="page-body">
      <!-- 规则名称（放最顶） -->
      <van-cell-group inset class="form-group">
        <van-field
          v-model="form.name"
          label="规则名称"
          placeholder="例：房贷月供"
          required
          maxlength="20"
          input-align="right"
          clearable
        />
      </van-cell-group>

      <!-- 账单信息：金额 + 收支 + 账户 + 分类 + 备注 -->
      <van-cell-group inset title="账单信息" class="form-group">
        <van-field
          :model-value="form.money"
          @update:model-value="onMoneyChange"
          label="金额"
          placeholder="0.00"
          type="number"
          required
          input-align="right"
        >
          <template #left-icon>
            <span class="field-prefix">¥</span>
          </template>
        </van-field>
        <!-- 收支 -->
        <van-cell
          is-link
          class="picker-cell"
          @click="openActionSheet"
        >
          <template #title>
            <span class="cell-title-required">收支类型</span>
          </template>
          <template #value>
            <span v-if="form.selectedAction" class="action-display">
              <span
                class="action-tag"
                :class="getActionClass(form.selectedAction.handle)"
              >
                {{ form.selectedAction.hname }}
              </span>
              <span v-if="form.selectedAction.exempt" class="exempt-tag">
                {{ getExemptText(form.selectedAction) }}
              </span>
            </span>
            <span v-else class="placeholder">点击选择</span>
          </template>
        </van-cell>

        <!-- 账户 -->
        <van-cell is-link class="picker-cell" @click="openAccountSheet(1)">
          <template #title>
            <span class="cell-title-required">
              {{ isTransfer ? '转出账户' : '账户' }}
            </span>
          </template>
          <template #value>
            <span :class="{ placeholder: !form.selectedAccount }">
              {{ form.selectedAccount?.name || '点击选择' }}
            </span>
          </template>
        </van-cell>

        <!-- 转入账户（仅转账） -->
        <van-cell
          v-if="isTransfer"
          is-link
          class="picker-cell"
          @click="openAccountSheet(2)"
        >
          <template #title>
            <span class="cell-title-required">转入账户</span>
          </template>
          <template #value>
            <span :class="{ placeholder: !form.selectedAccountTo }">
              {{ form.selectedAccountTo?.name || '点击选择' }}
            </span>
          </template>
        </van-cell>

        <!-- 分类 -->
        <van-cell is-link class="picker-cell" @click="openTypeCascader">
          <template #title>
            <span class="cell-title-required">分类</span>
          </template>
          <template #value>
            <span :class="{ placeholder: !form.selectedType }">
              {{ form.selectedType?.tname || '点击选择' }}
            </span>
          </template>
        </van-cell>

        <!-- 备注 -->
        <van-field
          v-model="form.note"
          label="备注"
          type="textarea"
          placeholder="可留空"
          rows="1"
          autosize
          maxlength="100"
          input-align="right"
        />
      </van-cell-group>

      <!-- 周期 -->
      <van-cell-group inset title="周期" class="form-group">
        <!-- 周期类型：单行 cell + 下方 pill 组 -->
        <div class="inline-cell">
          <span class="cell-title-required">周期类型</span>
          <div class="cycle-type-group">
            <div
              class="cycle-type-item"
              :class="{ active: form.cycleType === CycleType.DAILY }"
              @click="onCycleTypeChange(CycleType.DAILY)"
            >每日</div>
            <div
              class="cycle-type-item"
              :class="{ active: form.cycleType === CycleType.WEEKLY }"
              @click="onCycleTypeChange(CycleType.WEEKLY)"
            >每周</div>
            <div
              class="cycle-type-item"
              :class="{ active: form.cycleType === CycleType.MONTHLY }"
              @click="onCycleTypeChange(CycleType.MONTHLY)"
            >每月</div>
            <div
              class="cycle-type-item"
              :class="{ active: form.cycleType === CycleType.YEARLY }"
              @click="onCycleTypeChange(CycleType.YEARLY)"
            >每年</div>
          </div>
        </div>

        <!-- 每周 -->
        <div v-if="form.cycleType === CycleType.WEEKLY" class="inline-cell">
          <span class="cell-title-required">选择周几</span>
          <div class="weekday-group">
            <div
              v-for="d in 7"
              :key="d"
              class="weekday-item"
              :class="{ active: form.cycleDatesWeekly.includes(d) }"
              @click="toggleWeekday(d)"
            >周{{ weekdayLabel[d] }}</div>
          </div>
        </div>

        <!-- 每月 -->
        <div v-if="form.cycleType === CycleType.MONTHLY" class="inline-cell">
          <span class="cell-title-required">选择日期</span>
          <div class="month-grid">
            <div
              v-for="d in 31"
              :key="d"
              class="month-day"
              :class="{ active: form.cycleDatesMonthly.includes(d) }"
              @click="toggleMonthDay(d)"
            >{{ d }}</div>
          </div>
          <div class="field-hint">选 29 / 30 / 31 号遇短月自动回退到月末</div>
        </div>

        <!-- 每年 -->
        <div v-if="form.cycleType === CycleType.YEARLY" class="inline-cell">
          <span class="cell-title-required">指定日期</span>
          <div class="year-dates">
            <div
              v-for="mmdd in form.cycleDatesYearly"
              :key="mmdd"
              class="year-date-pill"
            >
              {{ mmdd }}
              <van-icon
                name="cross"
                size="12"
                class="remove-icon"
                @click.stop="removeYearDate(mmdd)"
              />
            </div>
            <div class="year-date-add" @click="openYearDateSheet">
              <van-icon name="plus" size="14" />添加
            </div>
          </div>
        </div>
      </van-cell-group>

      <!-- 执行时间 -->
      <van-cell-group inset title="执行时间" class="form-group">
        <van-cell is-link class="picker-cell" @click="openTimePicker">
          <template #title>
            <span class="cell-title-required">执行时间</span>
          </template>
          <template #value>
            <span class="mono-text">{{ form.runTime }}</span>
          </template>
        </van-cell>

        <van-cell is-link class="picker-cell" @click="openStartCalendar">
          <template #title>
            <span class="cell-title-required">开始日期</span>
          </template>
          <template #value>
            <span :class="{ placeholder: !form.startDate }">
              {{ form.startDate || '点击选择' }}
            </span>
          </template>
        </van-cell>

        <van-cell class="picker-cell">
          <template #title>结束日期</template>
          <template #value>
            <span
              v-if="form.endDate"
              class="end-date-display"
            >
              <span class="mono-text" @click="openEndCalendar">{{ form.endDate }}</span>
              <van-icon
                name="cross"
                size="14"
                class="clear-icon"
                @click.stop="clearEndDate"
              />
            </span>
            <span v-else class="placeholder" @click="openEndCalendar">
              留空 = 永久
            </span>
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 通知设置 -->
      <van-cell-group inset title="通知设置" class="form-group">
        <van-cell>
          <template #title>
            <div class="switch-info">
              <div class="switch-title">开启事前提醒</div>
              <div class="switch-desc">按全局配置提前 N 天发站内通知</div>
            </div>
          </template>
          <template #value>
            <van-switch v-model="form.reminderEnabled" size="22" />
          </template>
        </van-cell>

        <van-cell>
          <template #title>
            <div class="switch-info">
              <div class="switch-title">同时发送邮件</div>
              <div class="switch-desc">需要 WebHook 已配置邮件服务</div>
            </div>
          </template>
          <template #value>
            <van-switch
              v-model="form.emailEnabled"
              :disabled="!form.reminderEnabled"
              size="22"
              @change="onEmailEnabledChange"
            />
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 提交按钮 -->
      <van-button
        type="primary"
        block
        round
        :loading="submitting"
        class="submit-btn"
        @click="onSubmit"
      >
        创建规则
      </van-button>
    </div>

    <!-- ========= 选择器弹层 ========= -->

    <!-- 收支 -->
    <van-action-sheet
      v-model:show="showActionSheet"
      title="选择收支"
      teleport="body"
    >
      <div class="sheet-list">
        <div
          v-for="action in actions"
          :key="action.id"
          class="sheet-item"
          @click="onSelectAction(action)"
        >
          <div class="sheet-item-info">
            <span class="sheet-item-name">{{ action.hname }}</span>
            <div class="sheet-item-tags">
              <span class="action-tag" :class="getActionClass(action.handle)">
                {{ getHandleText(action.handle) }}
              </span>
              <span v-if="action.exempt" class="exempt-tag">
                {{ getExemptText(action) }}
              </span>
            </div>
          </div>
          <van-icon
            v-if="form.selectedAction?.id === action.id"
            name="success"
            class="check-icon"
          />
        </div>
      </div>
    </van-action-sheet>

    <!-- 账户 -->
    <van-action-sheet
      v-model:show="showAccountSheet"
      :title="accountSheetType === 1 ? (isTransfer ? '选择转出账户' : '选择账户') : '选择转入账户'"
      teleport="body"
    >
      <div class="sheet-list">
        <div
          v-for="account in accounts"
          :key="account.id"
          class="sheet-item account-item"
          :class="{
            active:
              accountSheetType === 1
                ? form.selectedAccount?.id === account.id
                : form.selectedAccountTo?.id === account.id,
            disabled: isAccountDisabled(account, accountSheetType),
          }"
          @click="onSelectAccount(account)"
        >
          <div class="account-left">
            <span
              class="account-type-tag"
              :class="
                account.accountType === AccountType.LIABILITY ? 'liability' : 'asset'
              "
            >
              {{ account.accountType === AccountType.LIABILITY ? '负债' : '资产' }}
            </span>
            <div class="account-info">
              <span class="account-name">{{ account.name }}</span>
              <span
                v-if="isAccountDisabled(account, accountSheetType)"
                class="disabled-reason"
              >
                {{ getAccountDisabledReason(account, accountSheetType) }}
              </span>
            </div>
          </div>
          <div class="account-right">
            <span class="account-balance">¥{{ account.money }}</span>
            <span
              v-if="account.exemptMoney && parseFloat(account.exemptMoney) !== 0"
              class="account-exempt"
            >
              不计入 ¥{{ account.exemptMoney }}
            </span>
          </div>
        </div>
      </div>
    </van-action-sheet>

    <!-- 分类级联 -->
    <van-popup v-model:show="showTypeCascader" round position="bottom" teleport="body">
      <van-cascader
        v-model="cascaderValue"
        title="选择分类"
        :options="types"
        :field-names="cascaderFieldNames"
        @close="showTypeCascader = false"
        @finish="onTypeCascaderFinish"
      />
    </van-popup>

    <!-- 开始日期（用自定义 popup 限高，避免 van-calendar 默认铺满屏幕） -->
    <van-popup
      v-model:show="showStartCalendar"
      position="bottom"
      round
      teleport="body"
      :style="{ height: '60%' }"
      class="calendar-popup"
    >
      <van-calendar
        :poppable="false"
        :show="true"
        :show-confirm="false"
        :min-date="startCalendarMinDate"
        :max-date="startCalendarMaxDate"
        title="选择开始日期"
        :style="{ height: '100%' }"
        @confirm="onStartCalendarConfirm"
      />
    </van-popup>

    <!-- 结束日期 -->
    <van-popup
      v-model:show="showEndCalendar"
      position="bottom"
      round
      teleport="body"
      :style="{ height: '60%' }"
      class="calendar-popup"
    >
      <van-calendar
        :poppable="false"
        :show="true"
        :show-confirm="false"
        :min-date="endCalendarMinDate"
        :max-date="endCalendarMaxDate"
        title="选择结束日期"
        :style="{ height: '100%' }"
        @confirm="onEndCalendarConfirm"
      />
    </van-popup>

    <!-- 执行时间（HH:mm） -->
    <van-popup v-model:show="showTimePicker" round position="bottom" teleport="body">
      <van-time-picker
        v-model="timePickerValue"
        :columns-type="['hour', 'minute']"
        title="选择执行时间"
        @confirm="onTimePickerConfirm"
        @cancel="showTimePicker = false"
      />
    </van-popup>

    <!-- 每年日期（月 + 日） -->
    <van-popup v-model:show="showYearDateSheet" round position="bottom" teleport="body">
      <van-picker
        v-model="yearDatePickerValue"
        :columns="[yearMonthColumn, yearDayColumn]"
        title="添加日期"
        @confirm="confirmYearDate"
        @cancel="showYearDateSheet = false"
      />
    </van-popup>
  </div>
</template>

<style scoped>
.scheduled-flow-add-page {
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

/* 表单分组（紧凑版 Vant cell 风） */
.form-group {
  margin-bottom: 12px;
}

/* van-cell 必填星号 */
.cell-title-required {
  color: var(--color-text-primary);
}

.cell-title-required::after {
  content: ' *';
  color: var(--color-expense);
}

/* picker cell 的 value 右对齐默认就有，这里只调样式 */
.picker-cell :deep(.van-cell__value) {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  color: var(--color-text-primary);
}

.picker-cell .placeholder {
  color: var(--color-text-tertiary);
}

.action-display {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.action-tag {
  display: inline-block;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.action-tag.income {
  color: var(--color-income);
  background: var(--color-income-bg);
}

.action-tag.expense {
  color: var(--color-expense);
  background: var(--color-expense-bg);
}

.action-tag.transfer {
  color: var(--color-transfer);
  background: var(--color-transfer-bg);
}

.exempt-tag {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--color-bg-page);
  color: var(--color-text-tertiary);
}

.mono-text {
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.2px;
}

.end-date-display {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.clear-icon {
  color: var(--color-text-tertiary);
  padding: 2px;
}

/* 金额前缀 */
.field-prefix {
  color: var(--color-text-secondary);
  font-size: 14px;
  margin-right: 4px;
}

/* 内联 cell（cycle 类型 / 周几 / 日期网格）—— 自定义 cell 风 */
.inline-cell {
  padding: 12px 16px;
}

.inline-cell + .inline-cell {
  border-top: 1px solid var(--color-border);
}

.inline-cell .cell-title-required {
  display: block;
  font-size: 14px;
  color: var(--color-text-primary);
  margin-bottom: 10px;
}

.field-hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--color-text-tertiary);
  line-height: 1.5;
}

/* 周期类型 */
.cycle-type-group {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.cycle-type-item {
  padding: 8px 0;
  text-align: center;
  font-size: 13px;
  color: var(--color-text-secondary);
  background: var(--color-bg-page);
  border: 1px solid var(--color-border);
  border-radius: 8px;
}

.cycle-type-item:active {
  opacity: 0.75;
}

.cycle-type-item.active {
  color: #fff;
  background: var(--color-transfer);
  border-color: var(--color-transfer);
  font-weight: 600;
}

/* 周几 */
.weekday-group {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 5px;
}

.weekday-item {
  padding: 7px 0;
  text-align: center;
  font-size: 12px;
  color: var(--color-text-secondary);
  background: var(--color-bg-page);
  border: 1px solid var(--color-border);
  border-radius: 6px;
}

.weekday-item.active {
  color: #fff;
  background: var(--color-transfer);
  border-color: var(--color-transfer);
  font-weight: 600;
}

/* 月日期网格 */
.month-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 5px;
}

.month-day {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: var(--color-text-secondary);
  background: var(--color-bg-page);
  border: 1px solid var(--color-border);
  border-radius: 6px;
}

.month-day.active {
  color: #fff;
  background: var(--color-transfer);
  border-color: var(--color-transfer);
  font-weight: 600;
}

/* 每年日期 */
.year-dates {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.year-date-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  background: var(--color-transfer-bg);
  color: var(--color-transfer);
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
}

.year-date-pill .remove-icon {
  cursor: pointer;
  opacity: 0.7;
}

.year-date-add {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  background: var(--color-bg-page);
  border: 1px dashed var(--color-border);
  border-radius: 6px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* 通知开关行：van-cell 里放 title + desc */
.switch-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.switch-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.switch-desc {
  font-size: 12px;
  color: var(--color-text-tertiary);
  line-height: 1.4;
}

/* 提交按钮 */
.submit-btn {
  margin-top: 8px;
  height: 44px;
  font-size: 15px;
  font-weight: 600;
}

/* ========= 选择器弹层样式 ========= */
/* 注意：不要在 .sheet-list 上加 max-height / overflow，
   van-action-sheet 自己默认 max-height: 80%，双层限制会造成嵌套滚动 */
.sheet-list {
  padding: 12px 16px 16px;
}

.sheet-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  margin-bottom: 8px;
  background: var(--color-bg-page);
  border-radius: 12px;
}

.sheet-item:last-child {
  margin-bottom: 0;
}

.sheet-item:active {
  opacity: 0.8;
}

.sheet-item-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sheet-item-name {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.sheet-item-tags {
  display: flex;
  gap: 6px;
}

.check-icon {
  color: var(--color-transfer);
  font-size: 18px;
}

/* 账户 sheet-item 布局 */
.account-item {
  align-items: center;
}

.account-item.disabled {
  opacity: 0.45;
}

.account-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.account-type-tag {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 500;
  flex-shrink: 0;
}

.account-type-tag.asset {
  color: var(--color-income);
  background: var(--color-income-bg);
}

.account-type-tag.liability {
  color: var(--color-expense);
  background: var(--color-expense-bg);
}

.account-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.account-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.disabled-reason {
  font-size: 11px;
  color: var(--color-text-tertiary);
}

.account-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  flex-shrink: 0;
}

.account-balance {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.account-exempt {
  font-size: 11px;
  color: var(--color-text-tertiary);
}
</style>

<style>
.scheduled-flow-add-page .page-header {
  background: rgba(245, 245, 245, 0.8);
}

html.dark .scheduled-flow-add-page .page-header {
  background: rgba(10, 10, 10, 0.8);
}
</style>
