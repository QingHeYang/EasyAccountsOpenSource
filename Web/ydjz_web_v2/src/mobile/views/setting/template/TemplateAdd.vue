<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showLoadingToast, closeToast, showToast, showConfirmDialog, showDialog } from 'vant'
import { templateApi } from '@shared/api/template'
import { tagApi, type Tag } from '@shared/api/tag'
import { actionApi, type Action, ActionHandle, ExemptMode } from '@shared/api/action'
import { accountApi, type Account, AccountType } from '@shared/api/account'
import { typeApi, type TypeWithChildren } from '@shared/api/type'
import { useSmartBack } from '@shared/composables/useSmartBack'

const route = useRoute()
const router = useRouter()
const { smartBack, replaceAfterSubmit } = useSmartBack()

// 编辑模式
const templateId = computed(() => {
  const id = route.params.id as string
  return id ? parseInt(id) : null
})
const isEdit = computed(() => templateId.value !== null)

// 表单数据
const templateName = ref('')
const money = ref('')
const dateType = ref<string>('')

// 选择的对象
const selectedAction = ref<Action | null>(null)
const selectedAccount = ref<Account | null>(null)
const selectedAccountTo = ref<Account | null>(null)
const selectedType = ref<{ id: number; tname: string } | null>(null)
const selectedTag = ref<Tag | null>(null)

// 列表数据
const actions = ref<Action[]>([])
const accounts = ref<Account[]>([])
const types = ref<TypeWithChildren[]>([])
const tags = ref<Tag[]>([])

// 弹窗状态
const showActionSheet = ref(false)
const showAccountSheet = ref(false)
const accountSheetType = ref<1 | 2>(1) // 1: 源账户, 2: 目标账户
const showTypeCascader = ref(false)
const showTagPanel = ref(false)
const cascaderValue = ref<number | string>('')

// 请求锁（编辑模式需要等待基础数据加载完成）
const requestLocks = ref({
  action: false,
  account: false,
  tag: false,
})

// 级联选择器配置
const cascaderFieldNames = {
  text: 'tname',
  value: 'id',
  children: 'childrenTypes',
}

// 获取收支样式类
function getActionClass(handle: number | undefined): string {
  if (handle === 0) return 'income'
  if (handle === 1) return 'expense'
  if (handle === 2) return 'transfer'
  return ''
}

// 获取收支操作文本
function getActionHandleText(handle: number | undefined): string {
  if (handle === 0) return '账户金额增加'
  if (handle === 1) return '账户金额减少'
  if (handle === 2) return '账户金额不变'
  return ''
}

// 获取不计入显示文本（内部转账根据模式显示）
function getExemptText(action: Action): string {
  if (!action.exempt) return ''
  // 收入/支出只显示"不计入"
  if (action.handle !== ActionHandle.TRANSFER) return '不计入'
  // 内部转账根据模式显示
  switch (action.exemptMode) {
    case ExemptMode.FROM_EXEMPT: return '转出不计入'
    case ExemptMode.TO_EXEMPT: return '转入不计入'
    case ExemptMode.BOTH_EXEMPT: return '两边不计入'
    default: return '不计入'
  }
}

// 是否为转账类型
const isTransfer = computed(() => selectedAction.value?.handle === 2)

// ==================== 双向限制逻辑 ====================

/**
 * 判断账户是否应该被禁用（根据已选收支类型）
 * 负债账户不能用于"不计入"类型的收支
 */
function isAccountDisabled(account: Account, panelType: 1 | 2): boolean {
  // 如果账户不是负债，不禁用
  if (account.accountType !== AccountType.LIABILITY) return false

  // 如果没选收支，或者收支不是"不计入"类型，不禁用
  if (!selectedAction.value?.exempt) return false

  // 普通不计入收支（非转账）：禁用所有负债账户
  if (selectedAction.value.handle !== ActionHandle.TRANSFER) {
    return true
  }

  // 内部转账的不计入，根据 exemptMode 判断
  const mode = selectedAction.value.exemptMode ?? ExemptMode.NONE

  if (panelType === 1) {
    // 源账户面板：禁用负债如果是转出不计入或两边不计入
    return mode === ExemptMode.FROM_EXEMPT || mode === ExemptMode.BOTH_EXEMPT
  } else {
    // 目标账户面板：禁用负债如果是转入不计入或两边不计入
    return mode === ExemptMode.TO_EXEMPT || mode === ExemptMode.BOTH_EXEMPT
  }
}

/**
 * 获取账户禁用原因提示
 */
function getAccountDisabledReason(account: Account, panelType: 1 | 2): string {
  if (!isAccountDisabled(account, panelType)) return ''
  return '负债账户不支持此收支类型'
}

// 加载收支列表
async function fetchActions() {
  try {
    const res = await actionApi.getAll()
    actions.value = res.data.data || []
    requestLocks.value.action = true
    checkAndLoadTemplate()
  } catch (err) {
    console.error('获取收支列表失败', err)
  }
}

// 加载账户列表
async function fetchAccounts() {
  try {
    const res = await accountApi.getAll()
    accounts.value = res.data.data || []
    requestLocks.value.account = true
    checkAndLoadTemplate()
  } catch (err) {
    console.error('获取账户列表失败', err)
  }
}

// 加载标签列表
async function fetchTags() {
  try {
    const res = await tagApi.getAll()
    tags.value = res.data.data || []
    requestLocks.value.tag = true
    checkAndLoadTemplate()
  } catch (err) {
    console.error('获取标签列表失败', err)
  }
}

// 根据收支ID加载分类列表
async function fetchTypesByAction() {
  if (!selectedAction.value) return
  try {
    const res = await typeApi.getByActionId(selectedAction.value.id)
    types.value = res.data.data || []
  } catch (err) {
    console.error('获取分类列表失败', err)
  }
}

// 检查是否可以加载模板详情
function checkAndLoadTemplate() {
  if (isEdit.value && requestLocks.value.action && requestLocks.value.account && requestLocks.value.tag) {
    loadTemplate()
  }
}

// 加载模板详情
async function loadTemplate() {
  if (!templateId.value) return

  try {
    const res = await templateApi.getById(templateId.value)
    const data = res.data.data

    templateName.value = data.name
    money.value = data.money || ''
    dateType.value = data.dateType !== undefined && data.dateType !== null ? String(data.dateType) : ''

    // 匹配收支
    if (data.actionId) {
      selectedAction.value = actions.value.find(a => a.id === data.actionId) || null
      if (selectedAction.value) {
        fetchTypesByAction()
      }
    }

    // 匹配账户
    if (data.accountId) {
      selectedAccount.value = accounts.value.find(a => a.id === data.accountId) || null
    }

    // 匹配目标账户
    if (data.accountToId) {
      selectedAccountTo.value = accounts.value.find(a => a.id === data.accountToId) || null
    }

    // 匹配分类
    if (data.typeId && data.type) {
      selectedType.value = { id: data.typeId, tname: data.type.tname }
      cascaderValue.value = data.typeId
    }

    // 匹配标签
    if (data.tagId) {
      selectedTag.value = tags.value.find(t => t.id === data.tagId) || null
    }
  } catch (err) {
    showToast('获取模板详情失败')
    console.error(err)
  }
}

// 选择收支
function onSelectAction(action: Action) {
  if (action.id === selectedAction.value?.id) {
    showActionSheet.value = false
    return
  }
  selectedAction.value = action
  selectedAccountTo.value = null
  selectedType.value = null
  cascaderValue.value = ''
  showActionSheet.value = false
  fetchTypesByAction()
}

// 打开账户选择
function openAccountSheet(type: 1 | 2) {
  accountSheetType.value = type
  showAccountSheet.value = true
}

// 选择账户
function onSelectAccount(account: Account) {
  if (accountSheetType.value === 1) {
    selectedAccount.value = account
  } else {
    selectedAccountTo.value = account
  }
  showAccountSheet.value = false
}

// 打开分类选择
function openTypeCascader() {
  if (!selectedAction.value) {
    showToast('请先选择收支')
    return
  }
  showTypeCascader.value = true
}

// 选择分类
function onTypeCascaderFinish({ selectedOptions }: { selectedOptions: Array<{ tname: string; id: number }> }) {
  showTypeCascader.value = false
  if (selectedOptions.length > 0) {
    const lastOption = selectedOptions[selectedOptions.length - 1]
    selectedType.value = {
      id: lastOption.id,
      tname: selectedOptions.map(o => o.tname).join('/'),
    }
  }
}

// 选择标签
function onSelectTag(tag: Tag) {
  selectedTag.value = tag
  showTagPanel.value = false
}

// 清除标签
function onClearTag() {
  selectedTag.value = null
}

// 显示日期类型说明
function showDateTypeHelp() {
  showDialog({
    title: '模板账单日期',
    message: '补上月 - 上个月最后一天\n记本月 - 本月记账当天',
  })
}

// 金额输入格式化
function formatMoneyInput(value: string): string {
  let result = value.replace(/[^\d.]/g, '')
  const parts = result.split('.')
  if (parts.length > 2) {
    result = parts[0] + '.' + parts.slice(1).join('')
  }
  if (parts.length === 2 && parts[1].length > 2) {
    result = parts[0] + '.' + parts[1].slice(0, 2)
  }
  return result
}

function onMoneyInput(e: Event) {
  const input = e.target as HTMLInputElement
  money.value = formatMoneyInput(input.value)
}

// 验证表单
function validateForm(): boolean {
  if (!templateName.value.trim()) {
    showToast('请输入模板名称')
    return false
  }
  return true
}

// 提交
async function onSubmit() {
  if (!validateForm()) return

  try {
    await showConfirmDialog({
      title: '确认',
      message: `确定提交"${templateName.value}"吗？`,
    })
  } catch {
    return
  }

  showLoadingToast({
    message: isEdit.value ? '保存中...' : '添加中...',
    forbidClick: true,
  })

  try {
    const params = {
      id: isEdit.value ? templateId.value! : undefined,
      name: templateName.value.trim(),
      money: money.value || undefined,
      actionId: selectedAction.value?.id,
      accountId: selectedAccount.value?.id,
      accountToId: selectedAccountTo.value?.id,
      typeId: selectedType.value?.id,
      tagId: selectedTag.value?.id,
      dateType: dateType.value ? parseInt(dateType.value) : undefined,
    }

    if (isEdit.value) {
      await templateApi.update(params)
    } else {
      await templateApi.add(params)
    }

    closeToast()
    showToast(isEdit.value ? '保存成功' : '添加成功')
    replaceAfterSubmit('/setting/template')
  } catch (err) {
    closeToast()
    showToast('操作失败')
    console.error(err)
  }
}

// 删除模板
async function onDelete() {
  try {
    await showConfirmDialog({
      title: '确认',
      message: `确定删除"${templateName.value}"吗？`,
    })

    await templateApi.delete(templateId.value!)
    showToast('已删除')
    replaceAfterSubmit('/setting/template')
  } catch {
    // 取消
  }
}

// 导航
function onBack() {
  smartBack('/setting/template')
}

function toTagManage() {
  router.push('/setting/template/tag')
}

onMounted(() => {
  // 重置滚动位置，避免从其他页面滚动状态透传
  window.scrollTo(0, 0)

  fetchActions()
  fetchAccounts()
  fetchTags()
})
</script>

<template>
  <div class="template-add-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="header-left" @click="onBack">
        <van-icon name="arrow-left" size="20" />
      </div>
      <div class="header-title">{{ isEdit ? '编辑模板' : '添加模板' }}</div>
      <div class="header-right" @click="toTagManage">
        <van-icon name="label-o" size="20" />
      </div>
    </div>

    <!-- 表单 -->
    <div class="page-body">
      <!-- 基本信息 -->
      <div class="form-card">
        <div class="form-item">
          <label class="form-label required">模板名称</label>
          <input
            v-model="templateName"
            type="text"
            class="form-input"
            placeholder="请输入模板名称"
          />
        </div>

        <div class="form-item">
          <label class="form-label">模板金额</label>
          <div class="input-with-prefix">
            <span class="input-prefix">¥</span>
            <input
              :value="money"
              @input="onMoneyInput"
              type="text"
              inputmode="decimal"
              class="form-input"
              placeholder="0.00"
            />
          </div>
        </div>
      </div>

      <!-- 关联选择 -->
      <div class="form-card">
        <!-- 选择收支 -->
        <div class="form-item" @click="showActionSheet = true">
          <label class="form-label">选择模板收支</label>
          <div class="form-select">
            <span v-if="selectedAction" class="action-display">
              <span class="action-tag" :class="getActionClass(selectedAction.handle)">
                {{ selectedAction.hname }}
              </span>
              <span v-if="selectedAction.exempt" class="exempt-tag">{{ getExemptText(selectedAction) }}</span>
            </span>
            <span v-else class="placeholder">点击选择收支</span>
            <van-icon name="arrow" size="16" />
          </div>
        </div>

        <!-- 选择账户 -->
        <div class="form-item" @click="openAccountSheet(1)">
          <label class="form-label">{{ isTransfer ? '选择模板转出账户' : '选择模板账户' }}</label>
          <div class="form-select">
            <span :class="{ placeholder: !selectedAccount }">
              {{ selectedAccount?.name || '点击选择账户' }}
            </span>
            <van-icon name="arrow" size="16" />
          </div>
        </div>

        <!-- 目标账户（转账时显示） -->
        <div v-if="isTransfer" class="form-item" @click="openAccountSheet(2)">
          <label class="form-label">选择模板转入账户</label>
          <div class="form-select">
            <span :class="{ placeholder: !selectedAccountTo }">
              {{ selectedAccountTo?.name || '点击选择转入账户' }}
            </span>
            <van-icon name="arrow" size="16" />
          </div>
        </div>

        <!-- 选择分类 -->
        <div class="form-item" @click="openTypeCascader">
          <label class="form-label">模板账单分类</label>
          <div class="form-select">
            <span :class="{ placeholder: !selectedType }">
              {{ selectedType?.tname || '点击选择分类' }}
            </span>
            <van-icon name="arrow" size="16" />
          </div>
        </div>

        <!-- 日期类型 -->
        <div class="form-item">
          <label class="form-label">
            <van-icon name="question-o" size="14" @click.stop="showDateTypeHelp" />
            模板账单日期
          </label>
          <div class="radio-group">
            <div
              class="radio-item"
              :class="{ active: dateType === '1' }"
              @click="dateType = '1'"
            >
              补上月
            </div>
            <div
              class="radio-item"
              :class="{ active: dateType === '0' }"
              @click="dateType = '0'"
            >
              记本月
            </div>
          </div>
        </div>
      </div>

      <!-- 标签选择 -->
      <div class="form-card">
        <div class="form-item" @click="showTagPanel = !showTagPanel">
          <label class="form-label">标签筛选</label>
          <div class="form-select">
            <div
              v-if="selectedTag"
              class="selected-tag"
              :style="{ background: selectedTag.color }"
              @click.stop="onClearTag"
            >
              {{ selectedTag.name }}
              <van-icon name="cross" size="12" />
            </div>
            <span v-else class="placeholder">点击选择标签</span>
            <van-icon :name="showTagPanel ? 'arrow-up' : 'arrow-down'" size="16" />
          </div>
        </div>

        <div v-show="showTagPanel" class="tag-panel">
          <div v-if="tags.length" class="tag-list">
            <div
              v-for="tag in tags"
              :key="tag.id"
              class="tag-item"
              :style="{ background: tag.color }"
              @click="onSelectTag(tag)"
            >
              {{ tag.name }}
            </div>
          </div>
          <div v-else class="no-tags">暂无标签</div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <button class="submit-btn" @click="onSubmit">
          {{ isEdit ? '保存修改' : '新建模板' }}
        </button>
        <button v-if="isEdit" class="delete-btn" @click="onDelete">
          删除模板
        </button>
      </div>
    </div>

    <!-- 收支选择器 -->
    <van-action-sheet v-model:show="showActionSheet" title="选择账单收支" teleport="body">
      <div class="action-list">
        <div
          v-for="action in actions"
          :key="action.id"
          class="action-item"
          @click="onSelectAction(action)"
        >
          <div class="action-info">
            <span class="action-name">{{ action.hname }}</span>
            <div class="action-tags">
              <span class="action-tag" :class="getActionClass(action.handle)">
                {{ getActionHandleText(action.handle) }}
              </span>
              <span v-if="action.exempt" class="exempt-tag">{{ getExemptText(action) }}</span>
            </div>
          </div>
          <van-icon
            v-if="selectedAction?.id === action.id"
            name="success"
            class="check-icon"
          />
        </div>
      </div>
    </van-action-sheet>

    <!-- 账户选择器 -->
    <van-action-sheet v-model:show="showAccountSheet" title="选择账户" teleport="body">
      <div class="account-list">
        <div
          v-for="account in accounts"
          :key="account.id"
          class="account-item"
          :class="{
            active: accountSheetType === 1
              ? selectedAccount?.id === account.id
              : selectedAccountTo?.id === account.id,
            disabled: isAccountDisabled(account, accountSheetType)
          }"
          @click="!isAccountDisabled(account, accountSheetType) && onSelectAccount(account)"
        >
          <div class="account-left">
            <div
              class="account-type-tag"
              :class="account.accountType === AccountType.LIABILITY ? 'liability' : 'asset'"
            >
              {{ account.accountType === AccountType.LIABILITY ? '负债' : '资产' }}
            </div>
            <div class="account-info">
              <span class="account-name">{{ account.name }}</span>
              <span v-if="isAccountDisabled(account, accountSheetType)" class="disabled-reason">
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

    <!-- 分类级联选择器 -->
    <van-popup v-model:show="showTypeCascader" round position="bottom" teleport="body">
      <van-cascader
        v-model="cascaderValue"
        title="选择账单分类"
        :options="types"
        :field-names="cascaderFieldNames"
        @close="showTypeCascader = false"
        @finish="onTypeCascaderFinish"
      />
    </van-popup>
  </div>
</template>

<style scoped>
.template-add-page {
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

.header-left:active,
.header-right:active {
  opacity: 0.7;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.page-body {
  padding: 76px 16px 24px;
}

/* 表单卡片 */
.form-card {
  background: var(--color-bg-card);
  border-radius: 16px;
  padding: 8px 0;
  margin-bottom: 16px;
}

.form-item {
  padding: 16px 20px;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin-bottom: 12px;
}

.form-label.required::after {
  content: '*';
  color: var(--color-expense);
  margin-left: 4px;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  font-size: 16px;
  color: var(--color-text-primary);
  background: var(--color-bg-page);
  border: none;
  border-radius: 12px;
  outline: none;
  box-sizing: border-box;
}

.form-input::placeholder {
  color: var(--color-text-tertiary);
}

/* 带前缀的输入框 */
.input-with-prefix {
  display: flex;
  align-items: center;
  background: var(--color-bg-page);
  border-radius: 12px;
  padding-left: 16px;
}

.input-prefix {
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.input-with-prefix .form-input {
  background: transparent;
  padding-left: 8px;
}

.form-select {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--color-bg-page);
  border-radius: 12px;
  font-size: 16px;
  color: var(--color-text-primary);
}

.form-select .placeholder {
  color: var(--color-text-tertiary);
}

/* 收支显示 */
.action-display {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-tag {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 6px;
  font-weight: 500;
}

.action-tag.income {
  background: var(--color-income-bg);
  color: var(--color-income);
}

.action-tag.expense {
  background: var(--color-expense-bg);
  color: var(--color-expense);
}

.action-tag.transfer {
  background: var(--color-transfer-bg);
  color: var(--color-transfer);
}

.exempt-tag {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--color-bg-page);
  color: var(--color-text-tertiary);
}

/* 单选组 */
.radio-group {
  display: flex;
  gap: 12px;
}

.radio-item {
  flex: 1;
  padding: 12px;
  text-align: center;
  font-size: 14px;
  color: var(--color-text-secondary);
  background: var(--color-bg-page);
  border-radius: 10px;
  border: 2px solid transparent;
}

.radio-item.active {
  color: var(--color-transfer);
  border-color: var(--color-transfer);
  background: var(--color-transfer-bg);
}

/* 标签相关 */
.selected-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  color: #fff;
}

.tag-panel {
  padding: 0 20px 16px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tag-item {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  color: #fff;
}

.tag-item:active {
  opacity: 0.8;
}

.no-tags {
  text-align: center;
  font-size: 14px;
  color: var(--color-text-tertiary);
  padding: 20px 0;
}

/* 操作按钮 */
.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 8px;
}

.submit-btn {
  width: 100%;
  padding: 16px;
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  background: var(--color-transfer);
  border: none;
  border-radius: 14px;
  cursor: pointer;
}

.submit-btn:active {
  opacity: 0.9;
}

.delete-btn {
  width: 100%;
  padding: 16px;
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  background: var(--color-expense);
  border: none;
  border-radius: 14px;
  cursor: pointer;
}

.delete-btn:active {
  opacity: 0.9;
}

/* 收支/账户选择列表 */
.action-list,
.account-list {
  padding: 16px;
}

.action-item,
.account-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: var(--color-bg-page);
  border-radius: 12px;
  margin-bottom: 10px;
}

.action-item:last-child,
.account-item:last-child {
  margin-bottom: 0;
}

.action-item:active,
.account-item:active {
  opacity: 0.8;
}

.action-info,
.account-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-name,
.account-name {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.action-tags {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 账户选择器新样式 */
.account-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.account-type-tag {
  font-size: 11px;
  padding: 4px 8px;
  border-radius: 6px;
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

.account-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.account-balance {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.account-exempt {
  font-size: 11px;
  color: var(--color-text-tertiary);
}

/* 账户选中状态 */
.account-item.active {
  border: 2px solid var(--color-transfer);
  background: var(--color-transfer-bg);
}

/* 账户禁用状态 */
.account-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.account-item.disabled:active {
  opacity: 0.5;
}

.disabled-reason {
  font-size: 11px;
  color: var(--color-expense);
  margin-top: 4px;
}

.check-icon {
  color: var(--color-transfer);
  font-size: 20px;
}
</style>

<!-- 非 scoped 样式 -->
<style>
.template-add-page .page-header {
  background: rgba(245, 245, 245, 0.8);
}

html.dark .template-add-page .page-header {
  background: rgba(10, 10, 10, 0.8);
}
</style>
