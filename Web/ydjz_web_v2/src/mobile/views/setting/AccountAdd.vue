<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showLoadingToast, closeToast, showToast } from 'vant'
import { accountApi } from '@shared/api/account'
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
const money = ref('')
const exemptMoney = ref('')
const card = ref('')
const note = ref('')

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
  // 恢复负号
  if (isNegative && result) {
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
    // Account 的 id 只在 URL 中，body 不需要
    const params = {
      name: accountName.value.trim(),
      money: String(money.value),
      card: card.value || '',
      exemptMoney: exemptMoney.value || '',
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
          <label class="form-label">不计入金额</label>
          <div class="input-with-prefix">
            <span class="input-prefix">¥</span>
            <input
              :value="exemptMoney"
              @input="onExemptMoneyInput"
              type="text"
              inputmode="decimal"
              class="form-input"
              placeholder="不计入总资产的金额"
            />
          </div>
          <p class="form-hint">该金额包含在账户余额中，但不计入总资产</p>
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
  display: block;
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
