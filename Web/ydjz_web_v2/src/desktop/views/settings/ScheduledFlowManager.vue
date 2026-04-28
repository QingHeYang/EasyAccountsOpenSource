<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  AlarmClock,
  ArrowRight,
  Close,
  Document,
  Refresh,
  Clock,
  Bell,
  InfoFilled,
  Tickets,
  CircleCheckFilled,
  CircleCloseFilled,
  Delete,
  VideoPlay,
  VideoPause,
  View,
} from '@element-plus/icons-vue'
import FlowEditor from '@desktop/components/flow/FlowEditor.vue'
import {
  scheduledFlowApi,
  CycleType,
  RuleStatus,
  FailCategory,
  parseCycleDates,
  stringifyCycleDates,
  type ScheduledFlowRule,
  type ScheduledFlowRuleParams,
  type ScheduledFlowLog,
} from '@shared/api/scheduledFlow'
import { isHandledError } from '@shared/api/request'
import { actionApi, type Action, ActionHandle, ExemptMode } from '@shared/api/action'
import { accountApi, type Account, AccountType } from '@shared/api/account'
import { typeApi, type TypeWithChildren } from '@shared/api/type'

defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
}>()

/* ---------------- 规则列表 ---------------- */

const loading = ref(false)
const rules = ref<ScheduledFlowRule[]>([])

async function loadRules() {
  loading.value = true
  try {
    const res = await scheduledFlowApi.listRules()
    rules.value = res.data.data ?? []
  } catch (err) {
    if (!isHandledError(err)) ElMessage.error('加载规则列表失败')
    rules.value = []
  } finally {
    loading.value = false
  }
}

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

const statusStyleMap: Record<
  RuleStatus,
  { text: string; color: string; bg: string }
> = {
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

/* ---------------- 表单状态 ---------------- */

const actions = ref<Action[]>([])
const accounts = ref<Account[]>([])
const ruleTypes = ref<TypeWithChildren[]>([])

interface FormState {
  name: string
  money: string
  note: string
  actionId: number | undefined
  selectedAction: Action | null
  accountId: number | undefined
  selectedAccount: Account | null
  accountToId: number | undefined
  selectedAccountTo: Account | null
  typeId: number | undefined
  selectedType: { id: number; tname: string } | null
  cycleType: CycleType
  cycleDatesWeekly: number[]
  cycleDatesMonthly: number[]
  cycleDatesYearly: string[]
  runTime: string
  startDate: string
  endDate: string
  reminderEnabled: boolean
  emailEnabled: boolean
}

function makeInitialForm(): FormState {
  return {
    name: '',
    money: '',
    note: '',
    actionId: undefined,
    selectedAction: null,
    accountId: undefined,
    selectedAccount: null,
    accountToId: undefined,
    selectedAccountTo: null,
    typeId: undefined,
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

const formDialogVisible = ref(false)
const form = ref<FormState>(makeInitialForm())
const submitting = ref(false)
const editingRuleId = ref<number | null>(null)
/** "启动前的编辑" —— 用户对一条非运行态规则点"开始"后进入编辑，保存后应顺势启动 */
const pendingStartAfterSave = ref(false)

const isEditing = computed(() => editingRuleId.value !== null)
const formTitle = computed(() => {
  if (pendingStartAfterSave.value) return '确认并启动规则'
  return isEditing.value ? '编辑规则' : '新建规则'
})
const submitLabel = computed(() => {
  if (pendingStartAfterSave.value) return '保存并启动'
  return isEditing.value ? '保存' : '创建'
})

const isTransfer = computed(
  () => form.value.selectedAction?.handle === ActionHandle.TRANSFER
)

interface PreviewRow {
  label: string
  value: string
  missing?: boolean
  /** 值以彩色 pill 形式显示（记账类型专用） */
  pillStyle?: { color: string; background: string }
}

const rulePreview = computed<PreviewRow[]>(() => {
  const f = form.value
  const rows: PreviewRow[] = []

  // 周期
  let cycleText = cycleLabelMap[f.cycleType] ?? ''
  if (f.cycleType === CycleType.WEEKLY) {
    cycleText = f.cycleDatesWeekly.length
      ? `每周 · 周${f.cycleDatesWeekly.map((d) => weekdayLabel[d]).join('、')}`
      : '每周 · 未选周几'
  } else if (f.cycleType === CycleType.MONTHLY) {
    cycleText = f.cycleDatesMonthly.length
      ? `每月 · ${f.cycleDatesMonthly.join('、')} 号`
      : '每月 · 未选日期'
  } else if (f.cycleType === CycleType.YEARLY) {
    cycleText = f.cycleDatesYearly.length
      ? `每年 · ${f.cycleDatesYearly.join('、')}`
      : '每年 · 未选日期'
  }
  rows.push({ label: '周期', value: cycleText })

  // 执行时间
  rows.push({
    label: '执行时间',
    value: f.runTime ? `${f.runTime.substring(0, 5)}` : '未选',
    missing: !f.runTime,
  })

  // 有效期
  let validText: string
  if (!f.startDate) {
    validText = '未选开始日期'
  } else if (f.endDate) {
    validText = `${f.startDate} ~ ${f.endDate}`
  } else {
    validText = `${f.startDate} 起永久`
  }
  rows.push({ label: '有效期', value: validText, missing: !f.startDate })

  // 类型：流入 / 流出 / 转账（彩色 pill）
  if (f.selectedAction) {
    const info = getHandleInfo(f.selectedAction.handle)
    rows.push({
      label: '类型',
      value: `${info.text} · ${f.selectedAction.hname}`,
      pillStyle: { color: info.color, background: info.bg },
    })
  } else {
    rows.push({ label: '类型', value: '未选收支', missing: true })
  }

  // 记账内容
  const parts: string[] = []
  // 根据动作给金额带上正负号
  const handle = f.selectedAction?.handle
  const sign = handle === ActionHandle.IN ? '+' : handle === ActionHandle.OUT ? '-' : ''
  parts.push(f.money ? `${sign}¥${f.money}` : '¥?')
  if (f.selectedType?.tname) parts.push(f.selectedType.tname)
  if (f.selectedAccount?.name) parts.push(f.selectedAccount.name)
  if (isTransfer.value && f.selectedAccountTo?.name) {
    parts.push(`→ ${f.selectedAccountTo.name}`)
  }
  rows.push({ label: '记账', value: parts.join(' · ') })

  // 提醒
  if (f.reminderEnabled) {
    rows.push({
      label: '提醒',
      value: f.emailEnabled ? '站内通知 + 邮件' : '站内通知',
    })
  }

  return rows
})

// TODO(测试期放开)：按产品规则 startDate 应 >= 今天+1，为便于测试暂时放开到"今天也能选"
function isBeforeToday(date: Date) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return date.getTime() < today.getTime()
}

function isBeforeStart(date: Date) {
  if (!form.value.startDate) return isBeforeToday(date)
  const start = new Date(form.value.startDate)
  start.setHours(0, 0, 0, 0)
  return date.getTime() <= start.getTime()
}

// 选择器可见性
const showActionPicker = ref(false)
const showAccountPicker = ref(false)
const accountPickerType = ref<1 | 2>(1)
const showTypePicker = ref(false)
const showYearDatePicker = ref(false)
const yearPickerMonth = ref(1)
const yearPickerDay = ref(1)

/* ---------------- 辅助 ---------------- */

function getHandleInfo(handle: ActionHandle) {
  switch (handle) {
    case ActionHandle.IN:
      return { text: '流入', color: 'var(--color-income)', bg: 'var(--color-income-bg)' }
    case ActionHandle.OUT:
      return { text: '流出', color: 'var(--color-expense)', bg: 'var(--color-expense-bg)' }
    case ActionHandle.TRANSFER:
      return { text: '转账', color: 'var(--color-transfer)', bg: 'var(--color-transfer-bg)' }
    default:
      return { text: '未知', color: 'var(--color-text-secondary)', bg: 'var(--color-bg-page)' }
  }
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

function pad2(n: number): string {
  return n < 10 ? `0${n}` : String(n)
}

function daysInMonth(month: number): number {
  const maxDays = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
  return maxDays[month - 1] ?? 31
}

/** 某年某月（month0: 0-11）实际有多少天，精确处理闰年 */
function actualDaysInYearMonth(year: number, month0: number): number {
  return new Date(year, month0 + 1, 0).getDate()
}

function formatYMD(year: number, month0: number, day: number): string {
  return `${year}-${pad2(month0 + 1)}-${pad2(day)}`
}

/** W3 预览：每月 → 下月执行日；每年 → 下一年执行日；其它 → 空 */
const futureRunDates = computed<string[]>(() => {
  const f = form.value
  const now = new Date()
  if (f.cycleType === CycleType.MONTHLY && f.cycleDatesMonthly.length) {
    const nextMonthDate = new Date(now.getFullYear(), now.getMonth() + 1, 1)
    const y = nextMonthDate.getFullYear()
    const m0 = nextMonthDate.getMonth()
    const maxDay = actualDaysInYearMonth(y, m0)
    const uniq = new Set<string>()
    for (const d of f.cycleDatesMonthly) {
      const actual = Math.min(d, maxDay)
      uniq.add(formatYMD(y, m0, actual))
    }
    return Array.from(uniq).sort()
  }
  if (f.cycleType === CycleType.YEARLY && f.cycleDatesYearly.length) {
    const nextYear = now.getFullYear() + 1
    const uniq = new Set<string>()
    for (const mmdd of f.cycleDatesYearly) {
      const match = /^(\d{1,2})-(\d{1,2})$/.exec(mmdd)
      if (!match) continue
      const m = Number(match[1])
      const d = Number(match[2])
      if (m < 1 || m > 12) continue
      const maxDay = actualDaysInYearMonth(nextYear, m - 1)
      const actual = Math.min(d, maxDay)
      uniq.add(formatYMD(nextYear, m - 1, actual))
    }
    return Array.from(uniq).sort()
  }
  return []
})

const futureRunDatesLabel = computed(() => {
  if (form.value.cycleType === CycleType.MONTHLY) return '下个月执行日'
  if (form.value.cycleType === CycleType.YEARLY) return '下一年执行日'
  return ''
})

/* ---------------- 数据加载 ---------------- */

async function loadActions() {
  try {
    const res = await actionApi.getAll()
    actions.value = res.data.data ?? []
  } catch {
    /* 拦截器已处理 */
  }
}

async function loadAccounts() {
  try {
    const res = await accountApi.getAll()
    accounts.value = res.data.data ?? []
  } catch {
    /* 拦截器已处理 */
  }
}

async function loadRuleTypes(actionId: number) {
  try {
    const res = await typeApi.getByActionId(actionId)
    ruleTypes.value = res.data.data ?? []
  } catch {
    ruleTypes.value = []
  }
}

/* ---------------- 事件 ---------------- */

function onAddRule() {
  editingRuleId.value = null
  pendingStartAfterSave.value = false
  form.value = makeInitialForm()
  formDialogVisible.value = true
  loadActions()
  loadAccounts()
}

/** 卡片右下角切换按钮：运行中→暂停直改；其他态→进入编辑流程，保存时顺势启动
 * 注意：未开始（NOT_STARTED）走系统自动，不应进入此函数 */
async function onToggleRuleStatus(rule: ScheduledFlowRule) {
  if (rule.status === RuleStatus.NOT_STARTED) return
  if (rule.status === RuleStatus.RUNNING) {
    try {
      await ElMessageBox.confirm(
        `确定暂停规则"${rule.name}"吗？暂停期间不会自动记账。`,
        '暂停规则',
        {
          confirmButtonText: '暂停',
          cancelButtonText: '取消',
          type: 'warning',
        }
      )
    } catch {
      return
    }
    try {
      await scheduledFlowApi.pauseRule(rule.id)
      ElMessage.success('已暂停')
      loadRules()
    } catch (err) {
      if (!isHandledError(err)) ElMessage.error('暂停失败')
    }
  } else {
    // 未开始 / 暂停 / 完成 / 失效 → 先让用户编辑确认，保存时顺带启动
    pendingStartAfterSave.value = true
    await onRuleClick(rule)
  }
}

async function onRuleClick(rule: ScheduledFlowRule) {
  editingRuleId.value = rule.id
  // 先重置，再并行拉依赖数据，避免对话框打开时看到旧表单
  form.value = makeInitialForm()
  formDialogVisible.value = true

  await Promise.all([
    loadActions(),
    loadAccounts(),
    rule.actionId ? loadRuleTypes(rule.actionId) : Promise.resolve(),
  ])

  // 若对话框在加载期间被关掉，放弃回填
  if (!formDialogVisible.value || editingRuleId.value !== rule.id) return

  const action = actions.value.find((a) => a.id === rule.actionId) ?? null
  const account = accounts.value.find((a) => a.id === rule.accountId) ?? null
  const accountTo = rule.accountToId
    ? accounts.value.find((a) => a.id === rule.accountToId) ?? null
    : null

  form.value = {
    name: rule.name,
    money: rule.money,
    note: rule.note || '',
    actionId: rule.actionId,
    selectedAction: action,
    accountId: rule.accountId,
    selectedAccount: account,
    accountToId: rule.accountToId,
    selectedAccountTo: accountTo,
    typeId: rule.typeId,
    selectedType: rule.typeName ? { id: rule.typeId, tname: rule.typeName } : null,
    cycleType: rule.cycleType,
    cycleDatesWeekly:
      rule.cycleType === CycleType.WEEKLY ? parseCycleDates<number>(rule.cycleDates) : [],
    cycleDatesMonthly:
      rule.cycleType === CycleType.MONTHLY ? parseCycleDates<number>(rule.cycleDates) : [],
    cycleDatesYearly:
      rule.cycleType === CycleType.YEARLY ? parseCycleDates<string>(rule.cycleDates) : [],
    runTime: (rule.runTime || '09:00').substring(0, 5),
    startDate: (rule.startDate || '').substring(0, 10),
    endDate: (rule.endDate || '').substring(0, 10),
    reminderEnabled: rule.reminderEnabled,
    emailEnabled: rule.emailEnabled,
  }
}

function closeFormDialog() {
  formDialogVisible.value = false
}

function onFormDialogClosed() {
  // 完全关闭后再清空表单与编辑态，避免动画期间看到字段变化
  form.value = makeInitialForm()
  ruleTypes.value = []
  editingRuleId.value = null
  pendingStartAfterSave.value = false
}

async function onDeleteRule() {
  if (!editingRuleId.value) return
  const id = editingRuleId.value
  const name = form.value.name || `规则 #${id}`
  try {
    await ElMessageBox.confirm(
      `确定删除"${name}"吗？相关的执行日志和未读通知会一并清除，此操作不可恢复。`,
      '删除规则',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
  } catch {
    return
  }
  submitting.value = true
  try {
    await scheduledFlowApi.deleteRule(id)
    ElMessage.success('已删除')
    closeFormDialog()
    loadRules()
  } catch (err) {
    if (!isHandledError(err)) ElMessage.error('删除失败')
  } finally {
    submitting.value = false
  }
}

function onSelectAction(action: Action) {
  if (action.id === form.value.actionId) {
    showActionPicker.value = false
    return
  }
  form.value.actionId = action.id
  form.value.selectedAction = action
  form.value.accountToId = undefined
  form.value.selectedAccountTo = null
  form.value.typeId = undefined
  form.value.selectedType = null
  showActionPicker.value = false
  loadRuleTypes(action.id)
}

function openAccountPicker(type: 1 | 2) {
  if (!form.value.selectedAction) {
    ElMessage.warning('请先选择收支类型')
    return
  }
  accountPickerType.value = type
  showAccountPicker.value = true
}

function onSelectAccount(account: Account) {
  if (isAccountDisabled(account, accountPickerType.value)) return
  if (accountPickerType.value === 1) {
    form.value.accountId = account.id
    form.value.selectedAccount = account
  } else {
    form.value.accountToId = account.id
    form.value.selectedAccountTo = account
  }
  showAccountPicker.value = false
}

function openTypePicker() {
  if (!form.value.actionId) {
    ElMessage.warning('请先选择收支类型')
    return
  }
  showTypePicker.value = true
}

function onSelectType(type: TypeWithChildren, parent?: TypeWithChildren) {
  if (!parent && type.childrenTypes?.length) return
  const tname = parent ? `${parent.tname}/${type.tname}` : type.tname
  form.value.typeId = type.id
  form.value.selectedType = { id: type.id, tname }
  showTypePicker.value = false
}

/** 勾选"发送邮件"时弹确认：邮件通知依赖系统邮件配置
 *  TODO(后端接口): 等后端提供 mail 配置已就绪检测接口后，改为仅在"未配置"时弹出 */
async function onEmailEnabledChange(val: boolean) {
  if (!val) return // 取消勾选无需提示
  try {
    await ElMessageBox.confirm(
      '邮件通知需要在「系统设置 → 邮件」中配置邮箱才能收到。未配置时即使打开此开关也不会收到邮件。',
      '开启邮件提醒',
      {
        confirmButtonText: '我已确认',
        cancelButtonText: '取消',
        type: 'info',
      }
    )
    // 用户确认：保持 true
  } catch {
    // 用户取消或关闭弹窗：还原为 false
    form.value.emailEnabled = false
  }
}

function onCycleTypeChange(value: CycleType) {
  form.value.cycleType = value
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

function openYearDatePicker() {
  yearPickerMonth.value = 1
  yearPickerDay.value = 1
  showYearDatePicker.value = true
}

function confirmYearDate() {
  const mmdd = `${pad2(yearPickerMonth.value)}-${pad2(yearPickerDay.value)}`
  if (form.value.cycleDatesYearly.includes(mmdd)) {
    ElMessage.warning('该日期已添加')
    return
  }
  form.value.cycleDatesYearly.push(mmdd)
  form.value.cycleDatesYearly.sort()
  showYearDatePicker.value = false
}

function removeYearDate(mmdd: string) {
  const arr = form.value.cycleDatesYearly
  const idx = arr.indexOf(mmdd)
  if (idx >= 0) arr.splice(idx, 1)
}

watch(
  () => yearPickerMonth.value,
  (m) => {
    const max = daysInMonth(m)
    if (yearPickerDay.value > max) yearPickerDay.value = max
  }
)

/* ---------------- 提交 ---------------- */

function validate(): string | null {
  const f = form.value
  if (!f.name.trim()) return '请输入规则名称'
  if (!f.money) return '请输入金额'
  if (!/^\d+(\.\d+)?$/.test(f.money) || Number(f.money) <= 0) return '金额必须是大于 0 的数字'
  if (!f.actionId || !f.selectedAction) return '请选择收支类型'
  if (!f.accountId) return isTransfer.value ? '请选择转出账户' : '请选择账户'
  if (isTransfer.value && !f.accountToId) return '请选择转入账户'
  if (isTransfer.value && f.accountId === f.accountToId) return '转出与转入账户不能相同'
  if (!f.typeId) return '请选择分类'
  if (f.cycleType === CycleType.WEEKLY && !f.cycleDatesWeekly.length) return '请至少选择一个周几'
  if (f.cycleType === CycleType.MONTHLY && !f.cycleDatesMonthly.length) return '请至少选择一个日期'
  if (f.cycleType === CycleType.YEARLY && !f.cycleDatesYearly.length) return '请至少添加一个日期'
  if (!f.runTime) return '请选择执行时间'
  if (!f.startDate) return '请选择开始日期'
  const startTs = new Date(f.startDate).getTime()
  // TODO(测试期放开)：原规则要求 >= 今天+1，暂时放开到今天
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  if (startTs < today.getTime()) return '开始日期不能早于今天'
  if (f.endDate && new Date(f.endDate).getTime() <= startTs) return '结束日期必须晚于开始日期'
  return null
}

function buildCycleDatesString(): string {
  const f = form.value
  if (f.cycleType === CycleType.DAILY) return stringifyCycleDates([], CycleType.DAILY)
  if (f.cycleType === CycleType.WEEKLY) return stringifyCycleDates(f.cycleDatesWeekly, f.cycleType)
  if (f.cycleType === CycleType.MONTHLY) return stringifyCycleDates(f.cycleDatesMonthly, f.cycleType)
  return stringifyCycleDates(f.cycleDatesYearly, f.cycleType)
}

async function onSubmit() {
  const msg = validate()
  if (msg) {
    ElMessage.warning(msg)
    return
  }

  const f = form.value
  const params: ScheduledFlowRuleParams = {
    name: f.name.trim(),
    money: f.money,
    typeId: f.typeId!,
    actionId: f.actionId!,
    accountId: f.accountId!,
    accountToId: isTransfer.value ? f.accountToId : undefined,
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
  try {
    if (isEditing.value && editingRuleId.value) {
      await scheduledFlowApi.updateRule(editingRuleId.value, params)
      if (pendingStartAfterSave.value) {
        try {
          await scheduledFlowApi.startRule(editingRuleId.value)
          ElMessage.success('已保存并启动')
        } catch (err) {
          if (!isHandledError(err)) ElMessage.warning('已保存，但启动失败，请稍后在列表手动启动')
        }
      } else {
        ElMessage.success('保存成功')
      }
    } else {
      await scheduledFlowApi.createRule(params)
      ElMessage.success('创建成功')
    }
    closeFormDialog()
    loadRules()
  } catch (err) {
    if (!isHandledError(err)) ElMessage.error(isEditing.value ? '保存失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

/* ---------------- 执行记录 ---------------- */

const showLogDialog = ref(false)
const logLoading = ref(false)
const logs = ref<ScheduledFlowLog[]>([])
const logFilterRuleId = ref<number | null>(null)
const logPage = ref(0)
const logPageSize = 20
const logHasMore = ref(false)

async function loadLogs(reset = false) {
  if (reset) {
    logPage.value = 0
    logs.value = []
  }
  logLoading.value = true
  try {
    const res = await scheduledFlowApi.listLogs({
      ruleId: logFilterRuleId.value ?? undefined,
      page: logPage.value,
      size: logPageSize,
    })
    const batch = res.data.data ?? []
    if (reset) logs.value = batch
    else logs.value.push(...batch)
    logHasMore.value = batch.length === logPageSize
  } catch (err) {
    if (!isHandledError(err)) ElMessage.error('加载执行记录失败')
    logHasMore.value = false
  } finally {
    logLoading.value = false
  }
}

function openLogDialog() {
  showLogDialog.value = true
  logFilterRuleId.value = null
  loadLogs(true)
}

function onLogFilterChange() {
  loadLogs(true)
}

function onLogLoadMore() {
  logPage.value += 1
  loadLogs(false)
}

const failCategoryLabel: Record<FailCategory, string> = {
  [FailCategory.MASTER_DATA]: '主数据类',
  [FailCategory.OTHER]: '其他类',
}

function formatLogTime(s: string): string {
  // 显示 MM-DD HH:mm（扁平单行列表空间有限，完整时间放到 title 里 hover 可见）
  if (!s) return ''
  if (s.length >= 16) return s.substring(5, 16)
  return s
}

async function onDeleteLog(log: ScheduledFlowLog) {
  const fullTime = log.executeTime ? log.executeTime.substring(0, 16) : ''
  try {
    await ElMessageBox.confirm(
      `确定删除规则"${log.ruleName}"在 ${fullTime} 的执行记录吗？`,
      '删除记录',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
  } catch {
    return // 取消
  }
  try {
    await scheduledFlowApi.deleteLog(log.id)
    ElMessage.success('已删除')
    // 本地移除即可，不用重拉
    const idx = logs.value.findIndex((l) => l.id === log.id)
    if (idx >= 0) logs.value.splice(idx, 1)
  } catch (err) {
    if (!isHandledError(err)) ElMessage.error('删除失败')
  }
}

/* 点击日志里的"查看流水"→ 直接打开 FlowEditor 抽屉；日志对话框保持打开 */
const showFlowEditor = ref(false)
const viewingFlowId = ref<number | null>(null)

function onViewFlow(log: ScheduledFlowLog) {
  if (!log.success || !log.flowId) return
  viewingFlowId.value = log.flowId
  showFlowEditor.value = true
}

function onFlowEditorClose(v: boolean) {
  showFlowEditor.value = v
  if (!v) viewingFlowId.value = null
}

async function onClearLogsByRule() {
  const ruleId = logFilterRuleId.value
  if (!ruleId) return
  const rule = rules.value.find((r) => r.id === ruleId)
  try {
    await ElMessageBox.confirm(
      `确定清空规则"${rule?.name ?? ruleId}"的全部执行记录吗？此操作不可恢复。`,
      '清空记录',
      {
        confirmButtonText: '清空',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
  } catch {
    return
  }
  try {
    await scheduledFlowApi.clearLogsByRule(ruleId)
    ElMessage.success('已清空')
    loadLogs(true)
  } catch (err) {
    if (!isHandledError(err)) ElMessage.error('清空失败')
  }
}

/** 暴露给父级：按 ID 打开规则的编辑对话框
 *  通知中心点击跳转时会从 settings/index.vue 调用这个方法 */
async function openRuleById(id: number) {
  // 若规则列表还没载入，先加载
  if (!rules.value.length) {
    await loadRules()
  }
  const rule = rules.value.find((r) => r.id === id)
  if (!rule) {
    ElMessage.warning('规则已被删除')
    return
  }
  await onRuleClick(rule)
}

defineExpose({ openRuleById })

/* 抽屉关闭时也把表单对话框关了，避免脱离上下文悬浮 */
function onDrawerVisibleChange(v: boolean) {
  emit('update:visible', v)
  if (!v) {
    formDialogVisible.value = false
    showActionPicker.value = false
    showAccountPicker.value = false
    showTypePicker.value = false
    showYearDatePicker.value = false
    showLogDialog.value = false
    showFlowEditor.value = false
  }
}
</script>

<template>
  <!-- 一级：规则列表抽屉 -->
  <el-drawer
    :model-value="visible"
    title="定时记账"
    direction="rtl"
    size="520px"
    class="setting-drawer scheduled-flow-drawer"
    @update:model-value="onDrawerVisibleChange"
    @open="loadRules"
  >
    <template #header>
      <div class="drawer-header">
        <div class="drawer-header-left">
          <span class="drawer-title">定时记账</span>
        </div>
        <div class="drawer-header-right">
          <el-button
            :icon="Tickets"
            circle
            class="header-icon-btn"
            title="执行记录"
            @click="openLogDialog"
          />
        </div>
      </div>
    </template>

    <div class="list-body" v-loading="loading">
      <!-- 顶部：新建规则 -->
      <div class="top-actions">
        <el-button type="primary" size="large" :icon="Plus" class="action-create" @click="onAddRule">
          新建规则
        </el-button>
      </div>

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
            <!-- 转账：两个账户合并为一个 block，中间带箭头 -->
            <span v-if="rule.accountToName" class="rule-pill rule-pill-transfer">
              {{ rule.accountName || '—' }}
              <el-icon :size="11" class="transfer-arrow"><ArrowRight /></el-icon>
              {{ rule.accountToName }}
            </span>
            <!-- 非转账：单独一个账户 pill -->
            <span v-else-if="rule.accountName" class="rule-pill">{{ rule.accountName }}</span>
          </div>

          <div v-if="rule.status === RuleStatus.INVALID" class="rule-invalid-hint">
            <el-icon :size="12"><InfoFilled /></el-icon>
            主数据失效，请编辑后重新启动
          </div>

          <div class="rule-actions" @click.stop>
            <!-- 未开始：等待 startDate 系统自动启动，用户无法手动点 -->
            <span
              v-if="rule.status === RuleStatus.NOT_STARTED"
              class="rule-auto-start-hint"
            >
              <el-icon :size="12"><Clock /></el-icon>
              {{ rule.startDate || '--' }} 自动启动
            </span>
            <!-- 运行中：暂停 -->
            <el-button
              v-else-if="rule.status === RuleStatus.RUNNING"
              type="warning"
              plain
              size="small"
              :icon="VideoPause"
              class="rule-toggle-btn"
              @click="onToggleRuleStatus(rule)"
            >
              暂停
            </el-button>
            <!-- 暂停 / 完成 / 失效：用户编辑后重新启动 -->
            <el-button
              v-else
              type="primary"
              plain
              size="small"
              :icon="VideoPlay"
              class="rule-toggle-btn"
              @click="onToggleRuleStatus(rule)"
            >
              开始
            </el-button>
          </div>
        </div>
      </div>

      <div v-else-if="!loading" class="empty-state">
        <div class="empty-icon">
          <el-icon :size="40"><AlarmClock /></el-icon>
        </div>
        <div class="empty-title">还没有定时规则</div>
        <div class="empty-desc">点击上方「新建规则」让系统在指定时间自动为你记一笔流水</div>
      </div>
    </div>
  </el-drawer>

  <!-- 二级：新建/编辑表单对话框 -->
  <el-dialog
    v-model="formDialogVisible"
    :title="formTitle"
    width="600"
    class="rule-form-dialog"
    :close-on-click-modal="false"
    :close-on-press-escape="!submitting"
    append-to-body
    @closed="onFormDialogClosed"
  >
    <div class="form-body">
      <!-- 启动前编辑提示 -->
      <div v-if="pendingStartAfterSave" class="start-banner">
        <el-icon :size="16" class="start-banner-icon"><InfoFilled /></el-icon>
        <div class="start-banner-text">
          <div class="start-banner-title">请确认规则配置</div>
          <div class="start-banner-desc">保存后系统将自动启动此规则</div>
        </div>
      </div>

      <!-- Section 1: 记账信息 -->
      <div class="form-section">
        <div class="section-header">
          <div class="section-icon-wrap section-icon-primary">
            <el-icon :size="16"><Document /></el-icon>
          </div>
          <div class="section-text">
            <div class="section-title">记账信息</div>
            <div class="section-subtitle">规则触发时生成的流水字段</div>
          </div>
        </div>

        <div class="form-item">
          <label class="form-label">规则名称 <span class="required">*</span></label>
          <el-input v-model="form.name" placeholder="例：房贷月供" size="large" maxlength="20" show-word-limit />
        </div>

        <div class="form-item">
          <label class="form-label">金额 <span class="required">*</span></label>
          <el-input v-model="form.money" placeholder="0.00" size="large" type="number">
            <template #prefix>¥</template>
          </el-input>
        </div>

        <div class="form-item">
          <label class="form-label">收支类型 <span class="required">*</span></label>
          <div class="form-select" @click="showActionPicker = true">
            <span v-if="form.selectedAction" class="action-display">
              <span
                class="action-tag"
                :style="{
                  color: getHandleInfo(form.selectedAction.handle).color,
                  background: getHandleInfo(form.selectedAction.handle).bg,
                }"
              >
                {{ form.selectedAction.hname }}
              </span>
              <span v-if="form.selectedAction.exempt" class="exempt-tag">
                {{ getExemptText(form.selectedAction) }}
              </span>
            </span>
            <span v-else class="placeholder">点击选择收支</span>
            <el-icon><ArrowRight /></el-icon>
          </div>
        </div>

        <div class="form-grid">
          <div class="form-item">
            <label class="form-label">
              {{ isTransfer ? '转出账户' : '账户' }} <span class="required">*</span>
            </label>
            <div class="form-select" @click="openAccountPicker(1)">
              <span :class="{ placeholder: !form.selectedAccount }">
                {{ form.selectedAccount?.name || '点击选择' }}
              </span>
              <el-icon><ArrowRight /></el-icon>
            </div>
          </div>

          <div v-if="isTransfer" class="form-item">
            <label class="form-label">转入账户 <span class="required">*</span></label>
            <div class="form-select" @click="openAccountPicker(2)">
              <span :class="{ placeholder: !form.selectedAccountTo }">
                {{ form.selectedAccountTo?.name || '点击选择' }}
              </span>
              <el-icon><ArrowRight /></el-icon>
            </div>
          </div>

          <div class="form-item">
            <label class="form-label">分类 <span class="required">*</span></label>
            <div class="form-select" @click="openTypePicker">
              <span :class="{ placeholder: !form.selectedType }">
                {{ form.selectedType?.tname || '点击选择' }}
              </span>
              <el-icon><ArrowRight /></el-icon>
            </div>
          </div>
        </div>

        <div class="form-item">
          <label class="form-label">备注</label>
          <el-input
            v-model="form.note"
            placeholder="可留空"
            size="large"
            type="textarea"
            :rows="2"
            maxlength="100"
            show-word-limit
          />
        </div>
      </div>

      <!-- Section 2: 周期配置 -->
      <div class="form-section">
        <div class="section-header">
          <div class="section-icon-wrap section-icon-success">
            <el-icon :size="16"><Refresh /></el-icon>
          </div>
          <div class="section-text">
            <div class="section-title">周期配置</div>
            <div class="section-subtitle">按什么频率触发</div>
          </div>
        </div>

        <div class="form-item">
          <label class="form-label">周期类型 <span class="required">*</span></label>
          <div class="cycle-type-group">
            <div
              v-for="(lbl, key) in cycleLabelMap"
              :key="key"
              class="cycle-type-item"
              :class="{ active: form.cycleType === Number(key) }"
              @click="onCycleTypeChange(Number(key) as CycleType)"
            >
              {{ lbl }}
            </div>
          </div>
        </div>

        <div v-if="form.cycleType === CycleType.WEEKLY" class="form-item">
          <label class="form-label">选择周几 <span class="required">*</span></label>
          <div class="weekday-group">
            <div
              v-for="d in 7"
              :key="d"
              class="weekday-item"
              :class="{ active: form.cycleDatesWeekly.includes(d) }"
              @click="toggleWeekday(d)"
            >
              周{{ weekdayLabel[d] }}
            </div>
          </div>
        </div>

        <div v-if="form.cycleType === CycleType.MONTHLY" class="form-item">
          <label class="form-label">选择日期 <span class="required">*</span></label>
          <div class="month-grid">
            <div
              v-for="d in 31"
              :key="d"
              class="month-day"
              :class="{ active: form.cycleDatesMonthly.includes(d) }"
              @click="toggleMonthDay(d)"
            >
              {{ d }}
            </div>
          </div>
          <div class="hint-card">
            <el-icon :size="14" class="hint-icon"><InfoFilled /></el-icon>
            <div class="hint-content">
              <div class="hint-rule">月末回退规则</div>
              <div class="hint-example">
                选 31 号时：2 月记 28 / 29 日、4 / 6 / 9 / 11 月记 30 日；选 30 号时：2 月记 28 / 29 日
              </div>
            </div>
          </div>
        </div>

        <div v-if="form.cycleType === CycleType.YEARLY" class="form-item">
          <label class="form-label">指定日期 <span class="required">*</span></label>
          <div class="year-dates">
            <div
              v-for="mmdd in form.cycleDatesYearly"
              :key="mmdd"
              class="year-date-pill"
            >
              {{ mmdd }}
              <el-icon :size="12" class="remove-icon" @click.stop="removeYearDate(mmdd)">
                <Close />
              </el-icon>
            </div>
            <div class="year-date-add" @click="openYearDatePicker">
              <el-icon><Plus /></el-icon>
              添加日期
            </div>
          </div>
        </div>

        <!-- W3: 未来执行日预览（月/年） -->
        <div v-if="futureRunDates.length" class="future-preview">
          <div class="future-preview-header">
            <el-icon :size="13" class="future-preview-icon"><Clock /></el-icon>
            <span>{{ futureRunDatesLabel }}（按当前配置推算，共 {{ futureRunDates.length }} 天）</span>
          </div>
          <div class="future-preview-pills">
            <span
              v-for="d in futureRunDates"
              :key="d"
              class="future-preview-pill"
            >
              {{ d }}
            </span>
          </div>
        </div>
      </div>

      <!-- Section 3: 执行安排 -->
      <div class="form-section">
        <div class="section-header">
          <div class="section-icon-wrap section-icon-warning">
            <el-icon :size="16"><Clock /></el-icon>
          </div>
          <div class="section-text">
            <div class="section-title">执行安排</div>
            <div class="section-subtitle">具体触发的时分与有效期</div>
          </div>
        </div>

        <div class="form-grid-three">
          <div class="form-item">
            <label class="form-label">执行时间 <span class="required">*</span></label>
            <el-time-picker
              v-model="form.runTime"
              format="HH:mm"
              value-format="HH:mm"
              placeholder="选择时间"
              size="large"
              style="width: 100%"
            />
          </div>

          <div class="form-item">
            <label class="form-label">开始日期 <span class="required">*</span></label>
            <el-date-picker
              v-model="form.startDate"
              type="date"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              placeholder="最早今天（测试期临时放开）"
              size="large"
              :disabled-date="isBeforeToday"
              style="width: 100%"
            />
          </div>

          <div class="form-item">
            <label class="form-label">结束日期</label>
            <el-date-picker
              v-model="form.endDate"
              type="date"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              placeholder="留空 = 永久"
              size="large"
              :disabled-date="isBeforeStart"
              style="width: 100%"
            />
          </div>
        </div>
      </div>

      <!-- Section 4: 通知设置 -->
      <div class="form-section">
        <div class="section-header">
          <div class="section-icon-wrap section-icon-danger">
            <el-icon :size="16"><Bell /></el-icon>
          </div>
          <div class="section-text">
            <div class="section-title">通知设置</div>
            <div class="section-subtitle">执行前是否提醒你</div>
          </div>
        </div>

        <div class="form-item-inline">
          <div class="inline-info">
            <div class="inline-title">开启事前提醒</div>
            <div class="inline-desc">执行前按全局配置提前 N 天发站内通知</div>
          </div>
          <el-switch v-model="form.reminderEnabled" />
        </div>

        <div class="form-item-inline">
          <div class="inline-info">
            <div class="inline-title">同时发送邮件</div>
            <div class="inline-desc">需要在「系统设置 → 邮件」中配置邮箱</div>
          </div>
          <el-switch
            v-model="form.emailEnabled"
            :disabled="!form.reminderEnabled"
            @change="onEmailEnabledChange"
          />
        </div>
      </div>

      <!-- 规则预览 -->
      <div class="rule-preview">
        <div class="preview-header">
          <el-icon :size="14" class="preview-icon"><InfoFilled /></el-icon>
          <span>规则预览</span>
        </div>
        <div class="preview-body">
          <div
            v-for="row in rulePreview"
            :key="row.label"
            class="preview-row"
            :class="{ missing: row.missing }"
          >
            <span class="preview-row-label">{{ row.label }}</span>
            <span
              v-if="row.pillStyle"
              class="preview-row-pill"
              :style="{ color: row.pillStyle.color, background: row.pillStyle.background }"
            >
              {{ row.value }}
            </span>
            <span v-else class="preview-row-value">{{ row.value }}</span>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="form-footer">
        <el-button
          v-if="isEditing"
          type="danger"
          plain
          :icon="Delete"
          :disabled="submitting"
          class="form-footer-delete"
          @click="onDeleteRule"
        >
          删除
        </el-button>
        <div class="form-footer-right">
          <el-button @click="closeFormDialog">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="onSubmit">
            {{ submitLabel }}
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>

  <!-- 三级：收支选择器 -->
  <el-dialog
    v-model="showActionPicker"
    title="选择收支"
    width="480"
    class="picker-dialog"
    append-to-body
  >
    <div class="picker-list">
      <div
        v-for="action in actions"
        :key="action.id"
        class="picker-item"
        :class="{ active: form.actionId === action.id }"
        @click="onSelectAction(action)"
      >
        <div class="picker-info">
          <span class="picker-name">{{ action.hname }}</span>
          <div class="picker-tags">
            <span
              class="action-tag"
              :style="{
                color: getHandleInfo(action.handle).color,
                background: getHandleInfo(action.handle).bg,
              }"
            >
              {{ getHandleInfo(action.handle).text }}
            </span>
            <span v-if="action.exempt" class="exempt-tag">
              {{ getExemptText(action) }}
            </span>
          </div>
        </div>
      </div>
      <el-empty v-if="!actions.length" description="暂无收支" :image-size="60" />
    </div>
  </el-dialog>

  <!-- 三级：账户选择器 -->
  <el-dialog
    v-model="showAccountPicker"
    :title="accountPickerType === 1 ? (isTransfer ? '选择转出账户' : '选择账户') : '选择转入账户'"
    width="520"
    class="picker-dialog"
    append-to-body
  >
    <div class="picker-list">
      <el-tooltip
        v-for="account in accounts"
        :key="account.id"
        :content="getAccountDisabledReason(account, accountPickerType)"
        :disabled="!isAccountDisabled(account, accountPickerType)"
        placement="right"
      >
        <div
          class="picker-item account-picker-item"
          :class="{
            active:
              accountPickerType === 1
                ? form.accountId === account.id
                : form.accountToId === account.id,
            disabled: isAccountDisabled(account, accountPickerType),
          }"
          @click="!isAccountDisabled(account, accountPickerType) && onSelectAccount(account)"
        >
          <div class="picker-left">
            <span
              class="account-type-tag"
              :class="account.accountType === AccountType.LIABILITY ? 'liability' : 'asset'"
            >
              {{ account.accountType === AccountType.LIABILITY ? '负债' : '资产' }}
            </span>
            <div class="picker-info">
              <span class="picker-name">{{ account.name }}</span>
              <span v-if="account.note" class="picker-hint">{{ account.note }}</span>
            </div>
          </div>
          <div class="picker-right">
            <span class="picker-money">¥{{ account.money }}</span>
            <span
              v-if="account.exemptMoney && parseFloat(account.exemptMoney) !== 0"
              class="picker-exempt"
            >
              不计入 ¥{{ account.exemptMoney }}
            </span>
          </div>
        </div>
      </el-tooltip>
      <el-empty v-if="!accounts.length" description="暂无账户" :image-size="60" />
    </div>
  </el-dialog>

  <!-- 三级：分类选择器 -->
  <el-dialog
    v-model="showTypePicker"
    title="选择分类"
    width="520"
    class="picker-dialog"
    append-to-body
  >
    <div class="type-picker-list">
      <div v-for="parent in ruleTypes" :key="parent.id" class="type-picker-group">
        <div
          class="type-picker-parent"
          :class="{
            active: form.typeId === parent.id,
            'has-children': parent.childrenTypes?.length,
          }"
          @click="onSelectType(parent)"
        >
          {{ parent.tname }}
          <span v-if="!parent.childrenTypes?.length" class="selectable-hint">可选</span>
        </div>
        <div v-if="parent.childrenTypes?.length" class="type-picker-children">
          <div
            v-for="child in parent.childrenTypes"
            :key="child.id"
            class="type-picker-child"
            :class="{ active: form.typeId === child.id }"
            @click="onSelectType(child, parent)"
          >
            {{ child.tname }}
          </div>
        </div>
      </div>
      <el-empty v-if="!ruleTypes.length" description="暂无分类" :image-size="60" />
    </div>
  </el-dialog>

  <!-- 执行记录对话框（固定高度 + 扁平单行列表） -->
  <el-dialog
    v-model="showLogDialog"
    title="执行记录"
    width="640"
    class="log-dialog"
    append-to-body
  >
    <div class="log-content">
      <!-- 顶部筛选条 -->
      <div class="log-filter">
        <span class="log-filter-label">按规则筛选</span>
        <el-select
          v-model="logFilterRuleId"
          placeholder="全部规则"
          clearable
          style="flex: 1"
          @change="onLogFilterChange"
        >
          <el-option
            v-for="r in rules"
            :key="r.id"
            :value="r.id"
            :label="r.name"
          />
        </el-select>
        <el-button
          v-if="logFilterRuleId && logs.length"
          :icon="Delete"
          size="default"
          type="danger"
          plain
          @click="onClearLogsByRule"
        >
          清空
        </el-button>
      </div>

      <!-- 列表区：固定占满剩余高度，内部滚动 -->
      <div class="log-list-wrap" v-loading="logLoading && !logs.length">
        <!-- 有数据：扁平单行列表 -->
        <template v-if="logs.length">
          <div class="log-list">
            <div
              v-for="log in logs"
              :key="log.id"
              class="log-row"
              :class="{ success: log.success, fail: !log.success }"
            >
              <el-icon
                class="log-row-icon"
                :class="log.success ? 'success' : 'fail'"
                :size="16"
              >
                <CircleCheckFilled v-if="log.success" />
                <CircleCloseFilled v-else />
              </el-icon>

              <span class="log-row-time" :title="log.executeTime">
                {{ formatLogTime(log.executeTime) }}
              </span>

              <span
                class="log-row-rule"
                :class="{ deleted: log.ruleName === '[已删除]' }"
                :title="log.ruleName"
              >
                {{ log.ruleName }}
              </span>

              <div class="log-row-detail">
                <!-- 成功：可点击的流水链接 -->
                <span
                  v-if="log.success"
                  class="log-flow-link"
                  :class="{ disabled: !log.flowId }"
                  @click.stop="onViewFlow(log)"
                >
                  <el-icon :size="11"><View /></el-icon>
                  查看流水
                  <span v-if="log.flowId" class="log-flow-id">#{{ log.flowId }}</span>
                </span>
                <!-- 失败：分类徽章 + 原因（省略号） -->
                <template v-else>
                  <span
                    v-if="log.failCategory"
                    class="fail-badge"
                    :class="`fail-badge-${log.failCategory}`"
                  >
                    {{ failCategoryLabel[log.failCategory] }}
                  </span>
                  <span class="fail-reason" :title="log.failReason || ''">
                    {{ log.failReason || '（无详细原因）' }}
                  </span>
                </template>
              </div>

              <el-button
                :icon="Delete"
                text
                circle
                size="small"
                class="log-row-delete"
                title="删除这条记录"
                @click.stop="onDeleteLog(log)"
              />
            </div>
          </div>

          <!-- 分页 -->
          <div v-if="logHasMore" class="log-load-more">
            <el-button :loading="logLoading" text @click="onLogLoadMore">
              加载更多
            </el-button>
          </div>
          <div v-else class="log-end-hint">— 已到底 —</div>
        </template>

        <!-- 空状态：占满容器居中 -->
        <div v-else-if="!logLoading" class="log-empty">
          <div class="log-empty-icon">
            <el-icon :size="28"><Tickets /></el-icon>
          </div>
          <div class="log-empty-title">暂无执行记录</div>
          <div class="log-empty-desc">规则执行后会在这里留下记录</div>
        </div>
      </div>
    </div>
  </el-dialog>

  <!-- 三级：每年日期选择器 -->
  <el-dialog
    v-model="showYearDatePicker"
    title="添加日期"
    width="460"
    class="picker-dialog"
    append-to-body
  >
    <div class="year-picker">
      <!-- 预览条 -->
      <div class="year-preview">
        <div class="year-preview-label">已选</div>
        <div class="year-preview-value">
          {{ pad2(yearPickerMonth) }}-{{ pad2(yearPickerDay) }}
        </div>
      </div>

      <!-- 月份 -->
      <div class="year-picker-block">
        <div class="year-picker-label">月份</div>
        <div class="year-picker-months">
          <div
            v-for="m in 12"
            :key="m"
            class="year-picker-month"
            :class="{ active: yearPickerMonth === m }"
            @click="yearPickerMonth = m"
          >
            {{ m }} 月
          </div>
        </div>
      </div>

      <!-- 日期 -->
      <div class="year-picker-block">
        <div class="year-picker-label">日期</div>
        <div class="year-picker-days">
          <div
            v-for="d in daysInMonth(yearPickerMonth)"
            :key="d"
            class="year-picker-day"
            :class="{ active: yearPickerDay === d }"
            @click="yearPickerDay = d"
          >
            {{ d }}
          </div>
        </div>
      </div>

      <div class="hint-card">
        <el-icon :size="14" class="hint-icon"><InfoFilled /></el-icon>
        <div class="hint-content">
          <div class="hint-rule">月末回退规则</div>
          <div class="hint-example">选 2-29 → 平年记 2-28；选 2-30 / 2-31 → 统一记 2 月最后一天</div>
        </div>
      </div>
    </div>
    <template #footer>
      <el-button @click="showYearDatePicker = false">取消</el-button>
      <el-button type="primary" @click="confirmYearDate">
        添加 {{ pad2(yearPickerMonth) }}-{{ pad2(yearPickerDay) }}
      </el-button>
    </template>
  </el-dialog>

  <!-- 流水详情抽屉（点击执行记录里的"查看流水"触发） -->
  <FlowEditor
    :visible="showFlowEditor"
    :flow-id="viewingFlowId"
    @update:visible="onFlowEditorClose"
  />
</template>

<style scoped>
.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.drawer-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.drawer-header-right {
  display: flex;
  gap: 8px;
}

.drawer-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

/* 抽屉头右侧图标按钮（记录 / 设置） */
.drawer-header-right {
  display: flex;
  gap: 8px;
}

.header-icon-btn {
  color: var(--color-text-secondary);
}

.header-icon-btn:hover {
  color: var(--color-transfer);
  border-color: var(--color-transfer);
}

/* 执行记录对话框：固定高度 + 扁平单行列表 */
.log-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.log-content {
  display: flex;
  flex-direction: column;
  height: 60vh;
  min-height: 380px;
}

/* 顶部筛选条 */
.log-filter {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px;
  border-bottom: 1px solid var(--color-border-light);
  flex-shrink: 0;
}

.log-filter-label {
  font-size: 13px;
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

/* 列表容器：占满剩余高度，内部滚动 */
.log-list-wrap {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  position: relative;
}

.log-list {
  display: flex;
  flex-direction: column;
}

/* 单行扁平 row */
.log-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 20px;
  border-bottom: 1px solid var(--color-border-light);
  transition: background 0.15s;
  min-height: 44px;
}

.log-row:hover {
  background: var(--color-bg-page);
}

.log-row-icon {
  flex-shrink: 0;
}

.log-row-icon.success {
  color: var(--color-income);
}

.log-row-icon.fail {
  color: var(--color-expense);
}

.log-row-time {
  flex-shrink: 0;
  width: 90px;
  font-size: 12px;
  color: var(--color-text-tertiary);
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.2px;
}

.log-row-rule {
  flex-shrink: 0;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.log-row-rule.deleted {
  color: var(--color-text-tertiary);
  font-weight: 500;
  font-style: italic;
}

.log-row-detail {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  overflow: hidden;
  font-size: 12.5px;
}

/* 流水链接 chip */
.log-flow-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: var(--color-transfer-bg);
  color: var(--color-transfer);
  border-radius: 5px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  flex-shrink: 0;
}

.log-flow-link:hover {
  background: var(--color-transfer);
  color: #fff;
}

.log-flow-link.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.log-flow-link.disabled:hover {
  background: var(--color-transfer-bg);
  color: var(--color-transfer);
}

.log-flow-id {
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 11px;
  opacity: 0.9;
}

/* 失败徽章 */
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
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
  flex: 1;
}

/* 删除按钮 */
.log-row-delete {
  flex-shrink: 0;
  color: var(--color-text-tertiary);
  opacity: 0;
  transition: opacity 0.15s;
  width: 24px;
  height: 24px;
  min-height: 24px;
}

.log-row:hover .log-row-delete {
  opacity: 1;
}

.log-row-delete:hover {
  color: var(--color-expense);
  background: var(--color-expense-bg);
}

/* 分页 & 末尾 */
.log-load-more {
  display: flex;
  justify-content: center;
  padding: 12px;
}

.log-end-hint {
  text-align: center;
  font-size: 12px;
  color: var(--color-text-tertiary);
  padding: 14px;
}

/* 空状态：铺满整个 log-list-wrap，居中 */
.log-empty {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  text-align: center;
}

.log-empty-icon {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-page);
  border-radius: 50%;
  color: var(--color-text-tertiary);
  margin-bottom: 14px;
}

.log-empty-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}

.log-empty-desc {
  font-size: 13px;
  color: var(--color-text-tertiary);
}

/* 收紧抽屉头到内容的间距（默认 32px 太松） */
:deep(.el-drawer__header) {
  margin-bottom: 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--color-border-light);
}

/* 列表 */
.list-body {
  padding: 4px 20px 20px;
}

/* 顶部操作条：新建规则 */
.top-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}

.top-actions .action-create {
  flex: 1;
  height: 46px;
  border-radius: 12px;
  font-weight: 600;
}

/* 提醒配置对话框 */
.reminder-config {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.reminder-hint {
  margin-top: 0 !important;
}

.days-group {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
}

.days-item {
  padding: 10px;
  text-align: center;
  font-size: 14px;
  color: var(--color-text-secondary);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-light);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s;
}

.days-item:hover {
  border-color: var(--color-border);
}

.days-item.active {
  color: var(--color-transfer);
  background: var(--color-transfer-bg);
  border-color: var(--color-transfer);
  font-weight: 600;
}

.rule-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rule-card {
  padding: 16px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(8px);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.rule-card:hover {
  border-color: var(--color-transfer);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.rule-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.rule-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.status-tag {
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
  gap: 8px;
}

.rule-money {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.rule-pill {
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 12px;
  color: var(--color-text-secondary);
  background: var(--color-bg-page);
}

/* 转账账户合并 pill：账户 → 账户 */
.rule-pill-transfer {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--color-transfer);
  background: var(--color-transfer-bg);
}

.rule-pill-transfer .transfer-arrow {
  opacity: 0.7;
}

/* 规则卡片底部操作区 */
.rule-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed var(--color-border-light);
}

.rule-toggle-btn {
  min-width: 80px;
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

/* 失效态提示 */
.rule-invalid-hint {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  padding: 6px 10px;
  font-size: 12px;
  color: var(--color-expense);
  background: var(--color-expense-bg);
  border-radius: 6px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px 20px;
  text-align: center;
}

.empty-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-transfer-bg);
  border-radius: 50%;
  color: var(--color-transfer);
  margin-bottom: 16px;
}

.empty-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 6px;
}

.empty-desc {
  font-size: 13px;
  color: var(--color-text-tertiary);
  line-height: 1.6;
  margin-bottom: 20px;
  max-width: 280px;
}

/* 表单对话框 */
.form-body {
  max-height: 60vh;
  overflow-y: auto;
  padding-right: 4px;
}

/* 启动前编辑 banner */
.start-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  margin-bottom: 14px;
  background: linear-gradient(
    135deg,
    rgba(250, 173, 20, 0.12) 0%,
    rgba(250, 173, 20, 0.06) 100%
  );
  border: 1px solid rgba(250, 173, 20, 0.3);
  border-radius: 10px;
}

.start-banner-icon {
  flex-shrink: 0;
  color: #faad14;
}

.start-banner-text {
  flex: 1;
  min-width: 0;
}

.start-banner-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.start-banner-desc {
  margin-top: 2px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

/* W3: 未来执行日预览 */
.future-preview {
  margin-top: 12px;
  padding: 12px 14px;
  background: rgba(82, 196, 26, 0.06);
  border: 1px solid rgba(82, 196, 26, 0.22);
  border-radius: 10px;
}

.future-preview-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-income);
  margin-bottom: 8px;
}

.future-preview-icon {
  color: var(--color-income);
}

.future-preview-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.future-preview-pill {
  padding: 4px 10px;
  background: var(--color-bg-card);
  color: var(--color-text-primary);
  border: 1px solid rgba(82, 196, 26, 0.3);
  border-radius: 6px;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.form-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.form-footer-right {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

/* 新建模式下只有右侧两个按钮；编辑模式下左侧是删除 */
.form-footer-delete {
  /* 视觉弱化，主操作仍在右侧 */
}

.form-section {
  background: var(--color-bg-page);
  border-radius: 12px;
  padding: 18px;
  margin-bottom: 14px;
  border: 1px solid var(--color-border-light);
}

.form-section:last-child {
  margin-bottom: 0;
}

.form-item {
  margin-bottom: 16px;
}

.form-item:last-child {
  margin-bottom: 0;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.form-grid .form-item,
.form-grid-three .form-item {
  margin-bottom: 16px;
}

.form-grid-three {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}

/* Section 头 */
.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border-light);
}

.section-icon-wrap {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  color: #fff;
  flex-shrink: 0;
}

.section-icon-primary {
  background: linear-gradient(135deg, var(--color-transfer) 0%, #4dabff 100%);
}

.section-icon-success {
  background: linear-gradient(135deg, var(--color-income) 0%, #7cd85f 100%);
}

.section-icon-warning {
  background: linear-gradient(135deg, #faad14 0%, #ffcc4d 100%);
}

.section-icon-danger {
  background: linear-gradient(135deg, var(--color-expense) 0%, #ff6b6b 100%);
}

.section-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1.2;
}

.section-subtitle {
  font-size: 12px;
  color: var(--color-text-tertiary);
  line-height: 1.3;
}

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}

.required {
  color: var(--color-expense);
  margin-left: 2px;
}

.form-select {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: var(--color-bg-card);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid var(--color-border-light);
}

.form-select:hover {
  border-color: var(--color-transfer);
}

.form-select .placeholder {
  color: var(--color-text-tertiary);
}

.action-display {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}

.exempt-tag {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--color-bg-page);
  color: var(--color-text-tertiary);
}

.input-hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--color-text-tertiary);
  line-height: 1.5;
}

/* 周期 */
.cycle-type-group {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.cycle-type-item {
  padding: 10px;
  text-align: center;
  font-size: 14px;
  color: var(--color-text-secondary);
  background: var(--color-bg-card);
  border-radius: 10px;
  border: 1px solid var(--color-border-light);
  cursor: pointer;
  transition: all 0.2s;
}

.cycle-type-item:hover {
  border-color: var(--color-border);
}

.cycle-type-item.active {
  color: var(--color-transfer);
  border: 2px solid var(--color-transfer);
  background: var(--color-transfer-bg);
  padding: 9px;
}

/* 周几 */
.weekday-group {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 6px;
}

.weekday-item {
  padding: 8px 4px;
  text-align: center;
  font-size: 13px;
  color: var(--color-text-secondary);
  background: var(--color-bg-card);
  border-radius: 8px;
  border: 1px solid var(--color-border-light);
  cursor: pointer;
  transition: all 0.2s;
}

.weekday-item:hover {
  border-color: var(--color-border);
}

.weekday-item.active {
  color: var(--color-transfer);
  background: var(--color-transfer-bg);
  border-color: var(--color-transfer);
  font-weight: 600;
}

/* 月 */
.month-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 6px;
}

.month-day {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: var(--color-text-secondary);
  background: var(--color-bg-card);
  border-radius: 8px;
  border: 1px solid var(--color-border-light);
  cursor: pointer;
  transition: all 0.2s;
}

.month-day:hover {
  border-color: var(--color-border);
}

.month-day.active {
  color: var(--color-transfer);
  background: var(--color-transfer-bg);
  border-color: var(--color-transfer);
  font-weight: 600;
}

/* 年 */
.year-dates {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.year-date-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: var(--color-transfer-bg);
  color: var(--color-transfer);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
}

.year-date-pill .remove-icon {
  cursor: pointer;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.year-date-pill .remove-icon:hover {
  opacity: 1;
}

.year-date-add {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background: var(--color-bg-card);
  border: 1px dashed var(--color-border);
  border-radius: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.year-date-add:hover {
  border-color: var(--color-transfer);
  color: var(--color-transfer);
}

/* 每年日期选择器（新） */
.year-picker {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.year-preview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  background: linear-gradient(135deg, var(--color-transfer-bg) 0%, rgba(24, 144, 255, 0.04) 100%);
  border: 1px solid rgba(24, 144, 255, 0.2);
  border-radius: 12px;
}

.year-preview-label {
  font-size: 13px;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.year-preview-value {
  font-size: 22px;
  font-weight: 700;
  color: var(--color-transfer);
  letter-spacing: 1px;
  font-variant-numeric: tabular-nums;
}

.year-picker-block {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.year-picker-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.year-picker-months {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.year-picker-month {
  padding: 10px 6px;
  text-align: center;
  font-size: 13px;
  color: var(--color-text-secondary);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-light);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
}

.year-picker-month:hover {
  border-color: var(--color-border);
}

.year-picker-month.active {
  color: var(--color-transfer);
  background: var(--color-transfer-bg);
  border-color: var(--color-transfer);
  font-weight: 600;
}

.year-picker-days {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 6px;
}

.year-picker-day {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: var(--color-text-secondary);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-light);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
}

.year-picker-day:hover {
  border-color: var(--color-border);
}

.year-picker-day.active {
  color: var(--color-transfer);
  background: var(--color-transfer-bg);
  border-color: var(--color-transfer);
  font-weight: 600;
}

/* Hint 卡片 */
.hint-card {
  display: flex;
  gap: 10px;
  margin-top: 10px;
  padding: 10px 12px;
  background: rgba(24, 144, 255, 0.06);
  border: 1px solid rgba(24, 144, 255, 0.18);
  border-radius: 8px;
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
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 2px;
}

.hint-example {
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

/* 规则预览 */
.rule-preview {
  position: relative;
  margin-top: 6px;
  padding: 18px 20px;
  background: linear-gradient(
    135deg,
    var(--color-transfer-bg) 0%,
    rgba(24, 144, 255, 0.02) 100%
  );
  border: 1px solid rgba(24, 144, 255, 0.18);
  border-radius: 14px;
  overflow: hidden;
}

.rule-preview::before {
  content: '';
  position: absolute;
  inset: 0 auto 0 0;
  width: 4px;
  background: var(--color-transfer);
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-transfer);
  text-transform: uppercase;
  letter-spacing: 0.6px;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px dashed rgba(24, 144, 255, 0.22);
}

.preview-icon {
  color: var(--color-transfer);
}

.preview-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-row {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  line-height: 1.5;
}

.preview-row-label {
  flex-shrink: 0;
  width: 62px;
  color: var(--color-text-tertiary);
  font-size: 12px;
}

.preview-row-value {
  flex: 1;
  color: var(--color-text-primary);
  font-weight: 500;
  word-break: break-all;
}

.preview-row.missing .preview-row-value {
  color: var(--color-text-tertiary);
  font-weight: 400;
  font-style: italic;
}

/* 类型 pill（流入/流出/转账） */
.preview-row-pill {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.4;
  letter-spacing: 0.2px;
}

/* 内联开关 */
.form-item-inline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 8px 0;
}

.form-item-inline + .form-item-inline {
  border-top: 1px solid var(--color-border-light);
  padding-top: 16px;
  margin-top: 8px;
}

.inline-info {
  flex: 1;
  min-width: 0;
}

.inline-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.inline-desc {
  margin-top: 4px;
  font-size: 12px;
  color: var(--color-text-tertiary);
  line-height: 1.5;
}

/* 选择器 */
.picker-list {
  max-height: 50vh;
  overflow-y: auto;
}

.picker-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  margin-bottom: 8px;
  background: var(--color-bg-page);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.picker-item:hover {
  background: var(--color-bg-card);
}

.picker-item.active {
  border-color: var(--color-transfer);
  background: rgba(24, 144, 255, 0.05);
}

.picker-item.has-children {
  cursor: not-allowed;
  opacity: 0.8;
}

.picker-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.picker-name {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.picker-tags {
  display: flex;
  gap: 8px;
}

.picker-money {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.picker-hint {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.account-picker-item {
  flex-direction: row;
  justify-content: space-between;
}

.account-picker-item.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.picker-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.picker-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  flex-shrink: 0;
}

.picker-exempt {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.account-type-tag {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 500;
  flex-shrink: 0;
}

.account-type-tag.asset {
  background: var(--color-income-bg);
  color: var(--color-income);
}

.account-type-tag.liability {
  background: var(--color-expense-bg);
  color: var(--color-expense);
}

/* 分类选择器 */
.type-picker-list {
  max-height: 50vh;
  overflow-y: auto;
}

.type-picker-group {
  margin-bottom: 12px;
}

.type-picker-parent {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  background: var(--color-bg-page);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.type-picker-parent:hover {
  background: var(--color-bg-card);
}

.type-picker-parent.active {
  border-color: var(--color-transfer);
  background: rgba(24, 144, 255, 0.05);
}

.type-picker-parent.has-children {
  cursor: default;
  color: var(--color-text-secondary);
}

.type-picker-parent.has-children:hover {
  background: var(--color-bg-page);
}

.selectable-hint {
  font-size: 12px;
  font-weight: 400;
  color: var(--color-text-tertiary);
  padding: 2px 8px;
  background: var(--color-bg-card);
  border-radius: 4px;
}

.type-picker-children {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 16px 0;
}

.type-picker-child {
  padding: 8px 14px;
  font-size: 13px;
  color: var(--color-text-secondary);
  background: var(--color-bg-page);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.type-picker-child:hover {
  color: var(--color-text-primary);
  background: var(--color-bg-card);
}

.type-picker-child.active {
  color: var(--color-transfer);
  border-color: var(--color-transfer);
  background: rgba(24, 144, 255, 0.05);
}

/* 暗色 */
html.dark .rule-card {
  background: rgba(40, 40, 40, 0.6);
}

html.dark .rule-card:hover {
  background: rgba(50, 50, 50, 0.8);
}

html.dark .rule-pill {
  background: rgba(255, 255, 255, 0.06);
}

html.dark .form-section {
  background: rgba(40, 40, 40, 0.4);
}

html.dark .form-select,
html.dark .cycle-type-item,
html.dark .weekday-item,
html.dark .month-day,
html.dark .year-date-add,
html.dark .year-picker-month,
html.dark .year-picker-day,
html.dark .days-item {
  background: rgba(40, 40, 40, 0.6);
}

html.dark .section-header {
  border-bottom-color: rgba(255, 255, 255, 0.08);
}

html.dark .rule-preview {
  background: linear-gradient(
    135deg,
    rgba(24, 144, 255, 0.12) 0%,
    rgba(24, 144, 255, 0.04) 100%
  );
  border-color: rgba(24, 144, 255, 0.25);
}

html.dark .preview-header {
  border-bottom-color: rgba(24, 144, 255, 0.3);
}

html.dark .hint-card {
  background: rgba(24, 144, 255, 0.12);
  border-color: rgba(24, 144, 255, 0.25);
}

html.dark .log-row:hover {
  background: rgba(255, 255, 255, 0.04);
}

html.dark .log-row,
html.dark .log-filter {
  border-color: rgba(255, 255, 255, 0.06);
}

html.dark .log-empty-icon {
  background: rgba(255, 255, 255, 0.04);
}

html.dark .rule-actions {
  border-top-color: rgba(255, 255, 255, 0.08);
}

html.dark .future-preview-pill {
  background: rgba(40, 40, 40, 0.6);
}
</style>
