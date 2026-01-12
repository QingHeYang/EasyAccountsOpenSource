<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showLoadingToast, closeToast, showToast, showDialog } from 'vant'
import { actionApi, ActionHandle, ExemptMode } from '@shared/api/action'
import { useSmartBack } from '@shared/composables/useSmartBack'

const route = useRoute()
const router = useRouter()
const { smartBack } = useSmartBack()

// 编辑模式
const actionId = computed(() => {
  const id = route.params.id as string
  return id ? parseInt(id) : null
})
const isEdit = computed(() => actionId.value !== null)

// 表单数据
const actionName = ref('')
const handleType = ref<string>('0')
const exempt = ref(false)
const exemptMode = ref<ExemptMode>(ExemptMode.NONE)
const disable = ref(false)

// 是否为转账类型
const isTransfer = computed(() => handleType.value === '2')

// 转出账户不计入总金额
const fromNotCount = computed({
  get: () => exemptMode.value === ExemptMode.FROM_EXEMPT || exemptMode.value === ExemptMode.BOTH_EXEMPT,
  set: (val: boolean) => {
    const toVal = exemptMode.value === ExemptMode.TO_EXEMPT || exemptMode.value === ExemptMode.BOTH_EXEMPT
    if (val && toVal) {
      exemptMode.value = ExemptMode.BOTH_EXEMPT
    } else if (val) {
      exemptMode.value = ExemptMode.FROM_EXEMPT
    } else if (toVal) {
      exemptMode.value = ExemptMode.TO_EXEMPT
    } else {
      exemptMode.value = ExemptMode.NONE
    }
  }
})

// 转入账户不计入总金额
const toNotCount = computed({
  get: () => exemptMode.value === ExemptMode.TO_EXEMPT || exemptMode.value === ExemptMode.BOTH_EXEMPT,
  set: (val: boolean) => {
    const fromVal = exemptMode.value === ExemptMode.FROM_EXEMPT || exemptMode.value === ExemptMode.BOTH_EXEMPT
    if (val && fromVal) {
      exemptMode.value = ExemptMode.BOTH_EXEMPT
    } else if (val) {
      exemptMode.value = ExemptMode.TO_EXEMPT
    } else if (fromVal) {
      exemptMode.value = ExemptMode.FROM_EXEMPT
    } else {
      exemptMode.value = ExemptMode.NONE
    }
  }
})

// 显示帮助
function showHelp() {
  showDialog({
    title: '不计入总金额说明',
    message: '不计入总金额一般用于资金代管、借钱还钱等场景。\n\n• 转出不计入：转出账户的金额变动不计入总金额\n• 转入不计入：转入账户的金额变动不计入总金额\n• 都不计入：两个账户的金额变动都不计入总金额',
    confirmButtonText: '我知道了',
  })
}

// 显示禁用帮助
function showDisableHelp() {
  showDialog({
    title: '禁用收支说明',
    message: '禁用后该收支类型将不会出现在记账页面的选项中。\n\n• 快记模板：使用此收支的快记模板将被清空收支设置，需要重新选择\n\n• 已有账单：已记录的账单不会受影响，数据会正常保留',
    confirmButtonText: '我知道了',
  })
}

// 加载现有数据
async function loadAction() {
  if (!actionId.value) return

  try {
    const res = await actionApi.getById(actionId.value)
    const action = res.data.data
    actionName.value = action.hname
    handleType.value = String(action.handle)
    exempt.value = action.exempt
    exemptMode.value = action.exemptMode ?? ExemptMode.NONE
    disable.value = action.disable ?? false
  } catch (err) {
    showToast('获取数据失败')
    console.error(err)
  }
}

// 提交
async function onSubmit() {
  if (!actionName.value.trim()) {
    showToast('请输入收支名称')
    return
  }

  showLoadingToast({
    message: isEdit.value ? '保存中...' : '添加中...',
    forbidClick: true,
  })

  try {
    const params = {
      hname: actionName.value.trim(),
      handle: parseInt(handleType.value) as ActionHandle,
      exempt: exempt.value,
      // exemptMode 仅对转账类型生效
      exemptMode: isTransfer.value ? exemptMode.value : undefined,
      // 禁用状态仅在编辑时提交
      disable: isEdit.value ? disable.value : undefined,
    }

    if (isEdit.value && actionId.value) {
      await actionApi.update(actionId.value, params)
    } else {
      await actionApi.add(params)
    }

    closeToast()
    showToast(isEdit.value ? '保存成功' : '添加成功')
    router.push('/setting/action')
  } catch (err) {
    closeToast()
    showToast('操作失败')
    console.error(err)
  }
}

function onBack() {
  smartBack('/setting/action')
}

onMounted(() => {
  if (isEdit.value) {
    loadAction()
  }
})
</script>

<template>
  <div class="action-add-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="header-left" @click="onBack">
        <van-icon name="arrow-left" size="20" />
      </div>
      <div class="header-title">{{ isEdit ? '编辑收支' : '添加收支' }}</div>
      <div class="header-right"></div>
    </div>

    <!-- 表单 -->
    <div class="page-body">
      <div class="form-card">
        <!-- 名称 -->
        <div class="form-item">
          <label class="form-label">收支名称</label>
          <input
            v-model="actionName"
            type="text"
            class="form-input"
            placeholder="请输入收支名称"
            maxlength="6"
          />
        </div>

        <!-- 类型选择 -->
        <div class="form-item">
          <label class="form-label">收支类型</label>
          <div class="radio-group">
            <label
              class="radio-item radio-income"
              :class="{ active: handleType === '0' }"
              @click="handleType = '0'"
            >
              <div class="radio-dot"></div>
              <span>流入</span>
              <span class="radio-desc">账户金额增加</span>
            </label>
            <label
              class="radio-item radio-expense"
              :class="{ active: handleType === '1' }"
              @click="handleType = '1'"
            >
              <div class="radio-dot"></div>
              <span>流出</span>
              <span class="radio-desc">账户金额减少</span>
            </label>
            <label
              class="radio-item radio-transfer"
              :class="{ active: handleType === '2' }"
              @click="handleType = '2'"
            >
              <div class="radio-dot"></div>
              <span>转账</span>
              <span class="radio-desc">账户金额不变</span>
            </label>
          </div>
        </div>

        <!-- 不计入开关 -->
        <div class="form-item switch-item">
          <div class="switch-info">
            <label class="form-label">不计入总金额</label>
            <span class="form-hint">开启后该收支不计入统计</span>
          </div>
          <van-switch v-model="exempt" size="24" />
        </div>

        <!-- 转账不计入设置（仅转账且开启不计入时显示） -->
        <div v-if="isTransfer && exempt" class="form-item">
          <label class="form-label">
            不计入设置
            <van-icon name="question-o" class="help-icon" @click="showHelp" />
          </label>
          <div class="transfer-card">
            <div class="transfer-account from" :class="{ active: fromNotCount }">
              <div class="account-label">转出账户</div>
              <div class="account-switch">
                <span>不计入</span>
                <van-switch v-model="fromNotCount" size="20" />
              </div>
            </div>
            <div class="transfer-arrow">
              <van-icon name="arrow" />
            </div>
            <div class="transfer-account to" :class="{ active: toNotCount }">
              <div class="account-label">转入账户</div>
              <div class="account-switch">
                <span>不计入</span>
                <van-switch v-model="toNotCount" size="20" />
              </div>
            </div>
          </div>
          <span class="form-hint">选择哪个账户的金额变动不计入总金额</span>
        </div>

        <!-- 禁用开关（仅编辑时显示） -->
        <div v-if="isEdit" class="form-item switch-item">
          <div class="switch-info">
            <label class="form-label">
              禁用此收支
              <van-icon name="question-o" class="help-icon" @click="showDisableHelp" />
            </label>
            <span class="form-hint">禁用后不会出现在记账选项中</span>
          </div>
          <van-switch v-model="disable" size="24" />
        </div>
      </div>

      <!-- 提交按钮 -->
      <button class="submit-btn" @click="onSubmit">
        {{ isEdit ? '保存修改' : '添加收支' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.action-add-page {
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

/* 单选组 */
.radio-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.radio-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: var(--color-bg-page);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.radio-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid var(--color-text-tertiary);
  transition: all 0.2s;
}

/* 流入 - 绿色 */
.radio-income.active {
  background: var(--color-income-bg);
}

.radio-income.active .radio-dot {
  border-color: var(--color-income);
  background: var(--color-income);
  box-shadow: inset 0 0 0 4px var(--color-bg-card);
}

/* 流出 - 红色 */
.radio-expense.active {
  background: var(--color-expense-bg);
}

.radio-expense.active .radio-dot {
  border-color: var(--color-expense);
  background: var(--color-expense);
  box-shadow: inset 0 0 0 4px var(--color-bg-card);
}

/* 转账 - 蓝色 */
.radio-transfer.active {
  background: var(--color-transfer-bg);
}

.radio-transfer.active .radio-dot {
  border-color: var(--color-transfer);
  background: var(--color-transfer);
  box-shadow: inset 0 0 0 4px var(--color-bg-card);
}

.radio-item span:not(.radio-desc) {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.radio-desc {
  margin-left: auto;
  font-size: 13px;
  color: var(--color-text-tertiary);
}

/* 开关项 */
.switch-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.switch-info {
  flex: 1;
}

.switch-info .form-label {
  margin-bottom: 4px;
}

.form-hint {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.form-hint.warning {
  display: block;
  color: var(--color-expense);
  margin-top: 4px;
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

/* 帮助图标 */
.form-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.help-icon {
  font-size: 16px;
  color: var(--color-text-tertiary);
}

/* 转账不计入设置卡片 */
.transfer-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: var(--color-bg-page);
  border-radius: 12px;
  margin-bottom: 8px;
}

.transfer-account {
  flex: 1;
  padding: 12px;
  background: var(--color-bg-card);
  border-radius: 10px;
  border: 2px solid transparent;
  transition: all 0.2s;
}

.transfer-account.from {
  background: rgba(245, 34, 45, 0.06);
}

.transfer-account.to {
  background: rgba(82, 196, 26, 0.06);
}

.transfer-account.from.active {
  border-color: var(--color-expense);
  background: rgba(245, 34, 45, 0.12);
}

.transfer-account.to.active {
  border-color: var(--color-income);
  background: rgba(82, 196, 26, 0.12);
}

.account-label {
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-bottom: 8px;
}

.transfer-account.from .account-label {
  color: var(--color-expense);
}

.transfer-account.to .account-label {
  color: var(--color-income);
}

.account-switch {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.transfer-arrow {
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}
</style>

<!-- 非 scoped 样式 -->
<style>
.action-add-page .page-header {
  background: rgba(245, 245, 245, 0.8);
}

html.dark .action-add-page .page-header {
  background: rgba(10, 10, 10, 0.8);
}
</style>
