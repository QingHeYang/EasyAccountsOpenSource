<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showLoadingToast, closeToast, showToast, showDialog } from 'vant'
import { accountApi, AccountType } from '@shared/api/account'
import { useSmartBack } from '@shared/composables/useSmartBack'

const route = useRoute()
const router = useRouter()
const { smartBack } = useSmartBack()

// 编辑模式
const accountId = computed(() => {
  const id = route.params.id as string
  return id ? parseInt(id) : null
})
const isEdit = computed(() => accountId.value !== null)

// 表单数据
const accountName = ref('')
const accountType = ref<AccountType>(AccountType.ASSET)
const money = ref('')
const exemptMoney = ref('')
const card = ref('')
const note = ref('')

// 判断是否为负债账户
const isLiabilityAccount = computed(() => accountType.value === AccountType.LIABILITY)

// 计算净资产
const netAsset = computed(() => {
  const m = parseFloat(money.value || '0')
  const e = parseFloat(exemptMoney.value || '0')
  return (m - e).toFixed(2)
})

// 显示账户类型帮助
function showAccountTypeHelp() {
  showDialog({
    title: '账户类型说明',
    message: '资产账户：储蓄卡、现金、支付宝余额等，余额通常为正数。\n\n负债账户：信用卡、借款、花呗等，余额通常为负数，表示欠款金额。\n\n注意：账户类型创建后无法修改。',
    confirmButtonText: '我知道了',
  })
}

// 显示不计入金额帮助
function showExemptMoneyHelp() {
  showDialog({
    title: '不计入金额说明',
    message: '不计入金额一般指：资金代管、借钱收款等内容。\n\n这部分金额虽然在账户中，但不属于您的实际资产，因此不计入总金额统计。\n\n此项金额不影响正常记账，不代表实际账户的余额。',
    confirmButtonText: '我知道了',
  })
}

// 金额输入格式化（允许负数，最多两位小数）
function formatMoneyInput(value: string): string {
  // 检查是否以负号开头
  const isNegative = value.startsWith('-')
  // 只保留数字和小数点
  let result = value.replace(/[^\d.]/g, '')
  // 只保留第一个小数点
  const parts = result.split('.')
  if (parts.length > 2) {
    result = parts[0] + '.' + parts.slice(1).join('')
  }
  // 限制小数点后两位
  if (parts.length === 2 && parts[1].length > 2) {
    result = parts[0] + '.' + parts[1].slice(0, 2)
  }
  // 恢复负号（即使 result 为空也保留，允许用户先输入负号）
  if (isNegative) {
    result = '-' + result
  }
  return result
}

function onMoneyInput(e: Event) {
  const input = e.target as HTMLInputElement
  money.value = formatMoneyInput(input.value)
}

function onExemptMoneyInput(e: Event) {
  const input = e.target as HTMLInputElement
  exemptMoney.value = formatMoneyInput(input.value)
}

// 加载现有数据
async function loadAccount() {
  if (!accountId.value) return

  try {
    const res = await accountApi.getById(accountId.value)
    const account = res.data.data
    accountName.value = account.name
    accountType.value = account.accountType ?? AccountType.ASSET
    money.value = account.money || ''
    exemptMoney.value = account.exemptMoney || ''
    card.value = account.card || ''
    note.value = account.note || ''
  } catch (err) {
    showToast('获取数据失败')
    console.error(err)
  }
}

// 验证表单
function validateForm(): boolean {
  if (!accountName.value.trim()) {
    showToast('请输入账户名称')
    return false
  }
  if (!money.value) {
    showToast('请输入账户余额')
    return false
  }
  return true
}

// 提交
async function onSubmit() {
  if (!validateForm()) return

  showLoadingToast({
    message: isEdit.value ? '保存中...' : '添加中...',
    forbidClick: true,
  })

  try {
    // 负债账户不允许设置不计入金额
    const submitExemptMoney = isLiabilityAccount.value ? '' : (exemptMoney.value || '')

    const params = {
      name: accountName.value.trim(),
      accountType: accountType.value,
      money: String(money.value),
      card: card.value || '',
      exemptMoney: submitExemptMoney,
      note: note.value || '',
    }

    if (isEdit.value && accountId.value) {
      await accountApi.update(accountId.value, params)
    } else {
      await accountApi.add(params)
    }

    closeToast()
    showToast(isEdit.value ? '保存成功' : '添加成功')
    router.push('/setting/account')
  } catch (err) {
    closeToast()
    showToast('操作失败')
    console.error(err)
  }
}

function onBack() {
  smartBack('/setting/account')
}

onMounted(() => {
  if (isEdit.value) {
    loadAccount()
  }
})
</script>

<template>
  <div class="account-add-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="header-left" @click="onBack">
        <van-icon name="arrow-left" size="20" />
      </div>
      <div class="header-title">{{ isEdit ? '编辑账户' : '添加账户' }}</div>
      <div class="header-right"></div>
    </div>

    <!-- 表单 -->
    <div class="page-body">
      <div class="form-card">
        <!-- 账户名称 -->
        <div class="form-item">
          <label class="form-label required">账户名称</label>
          <input
            v-model="accountName"
            type="text"
            class="form-input"
            placeholder="请输入账户名称"
          />
        </div>

        <!-- 账户类型 -->
        <div class="form-item">
          <label class="form-label required">
            账户类型
            <van-icon name="question-o" class="help-icon" @click="showAccountTypeHelp" />
          </label>
          <div class="type-radio-group" :class="{ disabled: isEdit }">
            <div
              class="type-radio-item"
              :class="{ active: accountType === AccountType.ASSET }"
              @click="!isEdit && (accountType = AccountType.ASSET)"
            >
              <div class="type-radio-dot"></div>
              <span class="type-radio-text">资产账户</span>
            </div>
            <div
              class="type-radio-item liability"
              :class="{ active: accountType === AccountType.LIABILITY }"
              @click="!isEdit && (accountType = AccountType.LIABILITY)"
            >
              <div class="type-radio-dot"></div>
              <span class="type-radio-text">负债账户</span>
            </div>
          </div>
          <p v-if="isEdit" class="form-hint warning">账户类型创建后无法修改</p>
          <p v-else-if="isLiabilityAccount" class="form-hint">负债账户余额通常为负数，如 -5000 表示欠款</p>
          <p v-else class="form-hint">资产账户余额通常为正数，表示实际持有金额</p>
        </div>

        <!-- 账户余额 -->
        <div class="form-item">
          <label class="form-label required">账户余额</label>
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

        <!-- 不计入金额 -->
        <div class="form-item">
          <label class="form-label">
            不计入金额
            <van-icon name="question-o" class="help-icon" @click="showExemptMoneyHelp" />
          </label>
          <div class="input-with-prefix" :class="{ disabled: isLiabilityAccount }">
            <span class="input-prefix">¥</span>
            <input
              :value="exemptMoney"
              @input="onExemptMoneyInput"
              type="text"
              inputmode="decimal"
              class="form-input"
              placeholder="0.00"
              :disabled="isLiabilityAccount"
            />
          </div>
          <p v-if="isLiabilityAccount" class="form-hint warning">
            负债账户不支持设置不计入金额
          </p>
          <template v-else>
            <p class="form-hint">此金额不计入总金额统计</p>
            <div class="net-asset-card">
              <div class="formula-text">账户净资产 = 账户余额 - 不计入金额</div>
              <div class="formula-calc">
                <span class="net-asset-value">{{ netAsset }}</span>
                <span class="calc-symbol">=</span>
                <span class="calc-value">({{ money || '0.00' }})</span>
                <span class="calc-symbol">-</span>
                <span class="calc-value">({{ exemptMoney || '0.00' }})</span>
              </div>
            </div>
          </template>
        </div>

        <!-- 卡号 -->
        <div class="form-item">
          <label class="form-label">银行卡号</label>
          <input
            v-model="card"
            type="text"
            class="form-input"
            placeholder="请输入银行卡号（选填）"
          />
        </div>

        <!-- 备注 -->
        <div class="form-item">
          <label class="form-label">备注</label>
          <textarea
            v-model="note"
            class="form-textarea"
            placeholder="请输入备注信息（选填）"
            rows="3"
            maxlength="50"
          ></textarea>
          <div class="textarea-counter">{{ note.length }}/50</div>
        </div>
      </div>

      <!-- 提交按钮 -->
      <button class="submit-btn" @click="onSubmit">
        {{ isEdit ? '保存修改' : '添加账户' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.account-add-page {
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

.header-right {
  background: transparent;
}

.header-left:active {
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

.help-icon {
  font-size: 16px;
  color: var(--color-text-tertiary);
}

/* 账户类型选择 */
.type-radio-group {
  display: flex;
  gap: 12px;
}

.type-radio-group.disabled {
  opacity: 0.6;
  pointer-events: none;
}

.type-radio-item {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  background: var(--color-bg-page);
  border-radius: 12px;
  border: 2px solid transparent;
  transition: all 0.2s;
}

.type-radio-dot {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid var(--color-text-tertiary);
  transition: all 0.2s;
  flex-shrink: 0;
}

.type-radio-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.type-radio-item.active {
  background: var(--color-transfer-bg);
  border-color: var(--color-transfer);
}

.type-radio-item.active .type-radio-dot {
  border-color: var(--color-transfer);
  background: var(--color-transfer);
  box-shadow: inset 0 0 0 3px var(--color-bg-card);
}

.type-radio-item.active .type-radio-text {
  color: var(--color-transfer);
}

.type-radio-item.liability.active {
  background: var(--color-expense-bg);
  border-color: var(--color-expense);
}

.type-radio-item.liability.active .type-radio-dot {
  border-color: var(--color-expense);
  background: var(--color-expense);
  box-shadow: inset 0 0 0 3px var(--color-bg-card);
}

.type-radio-item.liability.active .type-radio-text {
  color: var(--color-expense);
}

/* 净资产计算卡片 */
.net-asset-card {
  margin-top: 10px;
  padding: 12px 14px;
  background: var(--color-bg-page);
  border-radius: 10px;
}

.formula-text {
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-bottom: 6px;
}

.formula-calc {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
}

.net-asset-value {
  font-weight: 600;
  color: var(--color-transfer);
}

.calc-symbol {
  color: var(--color-text-tertiary);
}

.calc-value {
  color: var(--color-text-secondary);
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  font-size: 16px;
  color: var(--color-text-primary);
  background: var(--color-bg-page);
  border: none;
  box-sizing: border-box;
  border-radius: 12px;
  outline: none;
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

.input-with-prefix.disabled {
  opacity: 0.5;
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

.form-hint {
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-top: 8px;
  padding-left: 4px;
}

.form-hint.warning {
  color: var(--color-expense);
}

/* 文本域 */
.form-textarea {
  width: 100%;
  padding: 12px 16px;
  font-size: 16px;
  color: var(--color-text-primary);
  background: var(--color-bg-page);
  border: none;
  border-radius: 12px;
  outline: none;
  resize: none;
  font-family: inherit;
  box-sizing: border-box;
}

.form-textarea::placeholder {
  color: var(--color-text-tertiary);
}

.textarea-counter {
  text-align: right;
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-top: 6px;
}

/* 提交按钮 */
.submit-btn {
  width: 100%;
  margin-top: 24px;
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
</style>

<!-- 非 scoped 样式 -->
<style>
.account-add-page .page-header {
  background: rgba(245, 245, 245, 0.8);
}

html.dark .account-add-page .page-header {
  background: rgba(10, 10, 10, 0.8);
}
</style>
