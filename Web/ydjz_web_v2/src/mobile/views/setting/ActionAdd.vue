<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showLoadingToast, closeToast, showToast } from 'vant'
import { actionApi, ActionHandle } from '@shared/api/action'
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

// 加载现有数据
async function loadAction() {
  if (!actionId.value) return

  try {
    const res = await actionApi.getById(actionId.value)
    const action = res.data.data
    actionName.value = action.hname
    handleType.value = String(action.handle)
    exempt.value = action.exempt
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
.action-add-page .page-header {
  background: rgba(245, 245, 245, 0.8);
}

html.dark .action-add-page .page-header {
  background: rgba(10, 10, 10, 0.8);
}
</style>
