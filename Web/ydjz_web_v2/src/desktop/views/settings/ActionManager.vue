<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Close, ArrowRight, QuestionFilled } from '@element-plus/icons-vue'
import { actionApi, type Action, ActionHandle, ExemptMode } from '@shared/api/action'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()

// 抽屉状态
const drawerVisible = ref(false)
const showDetail = ref(false)

// 数据
const loading = ref(false)
const actions = ref<Action[]>([])
const editingAction = ref<Action | null>(null)

// 表单
const actionForm = ref({
  hname: '',
  handle: ActionHandle.IN,
  exempt: false,
  exemptMode: ExemptMode.NONE as ExemptMode,
  disable: false,
})

// 监听外部 visible 变化
watch(() => props.visible, (val) => {
  drawerVisible.value = val
  if (val) {
    loadActions()
  }
})

// 监听内部 drawer 变化同步到外部
watch(drawerVisible, (val) => {
  emit('update:visible', val)
  if (!val) {
    showDetail.value = false
    resetForm()
  }
})

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

async function loadActions() {
  loading.value = true
  try {
    const res = await actionApi.getAllWithDisabled()
    actions.value = res.data.data
  } catch (err) {
    console.error('获取收支列表失败', err)
    ElMessage.error('获取收支列表失败')
  } finally {
    loading.value = false
  }
}

function onAdd() {
  editingAction.value = null
  resetForm()
  showDetail.value = true
}

function onEdit(action: Action) {
  editingAction.value = action
  actionForm.value = {
    hname: action.hname,
    handle: action.handle,
    exempt: action.exempt,
    exemptMode: action.exemptMode ?? ExemptMode.NONE,
    disable: action.disable ?? false,
  }
  showDetail.value = true
}

function onCloseDetail() {
  showDetail.value = false
  resetForm()
}

function resetForm() {
  editingAction.value = null
  actionForm.value = {
    hname: '',
    handle: ActionHandle.IN,
    exempt: false,
    exemptMode: ExemptMode.NONE,
    disable: false,
  }
}

// 是否为转账类型
const isTransfer = computed(() => actionForm.value.handle === ActionHandle.TRANSFER)

// 帮助对话框
const showHelpDialog = ref(false)
const showDisableHelpDialog = ref(false)

// 转出账户是否不计入
const fromExempt = computed({
  get: () => actionForm.value.exemptMode === ExemptMode.FROM_EXEMPT || actionForm.value.exemptMode === ExemptMode.BOTH_EXEMPT,
  set: (val: boolean) => {
    const toExempt = actionForm.value.exemptMode === ExemptMode.TO_EXEMPT || actionForm.value.exemptMode === ExemptMode.BOTH_EXEMPT
    if (val && toExempt) {
      actionForm.value.exemptMode = ExemptMode.BOTH_EXEMPT
    } else if (val) {
      actionForm.value.exemptMode = ExemptMode.FROM_EXEMPT
    } else if (toExempt) {
      actionForm.value.exemptMode = ExemptMode.TO_EXEMPT
    } else {
      actionForm.value.exemptMode = ExemptMode.NONE
    }
  }
})

// 转入账户是否不计入
const toExempt = computed({
  get: () => actionForm.value.exemptMode === ExemptMode.TO_EXEMPT || actionForm.value.exemptMode === ExemptMode.BOTH_EXEMPT,
  set: (val: boolean) => {
    const fromExemptVal = actionForm.value.exemptMode === ExemptMode.FROM_EXEMPT || actionForm.value.exemptMode === ExemptMode.BOTH_EXEMPT
    if (val && fromExemptVal) {
      actionForm.value.exemptMode = ExemptMode.BOTH_EXEMPT
    } else if (val) {
      actionForm.value.exemptMode = ExemptMode.TO_EXEMPT
    } else if (fromExemptVal) {
      actionForm.value.exemptMode = ExemptMode.FROM_EXEMPT
    } else {
      actionForm.value.exemptMode = ExemptMode.NONE
    }
  }
})

async function onSubmit() {
  if (!actionForm.value.hname.trim()) {
    ElMessage.warning('请输入收支名称')
    return
  }

  try {
    const params = {
      hname: actionForm.value.hname.trim(),
      handle: actionForm.value.handle,
      exempt: actionForm.value.exempt,
      // exemptMode 仅对转账类型生效
      exemptMode: isTransfer.value ? actionForm.value.exemptMode : undefined,
      disable: actionForm.value.disable,
    }

    if (editingAction.value) {
      await actionApi.update(editingAction.value.id, params)
      ElMessage.success('保存成功')
    } else {
      await actionApi.add(params)
      ElMessage.success('添加成功')
    }
    onCloseDetail()
    loadActions()
  } catch (err) {
    console.error('操作失败', err)
    ElMessage.error('操作失败')
  }
}

// 计算抽屉宽度
const drawerSize = computed(() => showDetail.value ? '800px' : '480px')
</script>

<template>
  <el-drawer
    v-model="drawerVisible"
    title="收支管理"
    direction="rtl"
    :size="drawerSize"
    :z-index="3000"
    class="setting-drawer split-layout"
  >
    <!-- 抽屉头部 -->
    <template #header>
      <div class="drawer-header">
        <div class="drawer-header-left">
          <span class="drawer-title">收支管理</span>
        </div>
        <el-button :icon="Plus" type="primary" @click="onAdd">添加</el-button>
      </div>
    </template>

    <div class="drawer-split-view">
      <!-- 左侧：列表 -->
      <div class="split-list" :class="{ 'has-detail': showDetail }">
        <div v-loading="loading" class="action-list">
          <div
            v-for="action in actions"
            :key="action.id"
            class="action-item"
            :class="{ active: editingAction?.id === action.id, disabled: action.disable }"
            @click="onEdit(action)"
          >
            <div class="action-info">
              <div class="action-name">{{ action.hname }}</div>
              <div class="action-tags">
                <span
                  class="action-tag"
                  :style="{
                    color: getHandleInfo(action.handle).color,
                    background: getHandleInfo(action.handle).bg,
                  }"
                >
                  {{ getHandleInfo(action.handle).text }}
                </span>
                <span v-if="action.exempt" class="action-tag exempt">{{ getExemptText(action) }}</span>
                <span v-if="action.disable" class="action-tag disabled-tag">已禁用</span>
              </div>
            </div>
            <el-icon class="action-arrow"><ArrowRight /></el-icon>
          </div>
          <el-empty v-if="!loading && actions.length === 0" description="暂无收支类型" />
        </div>
      </div>

      <!-- 右侧：详情/表单 -->
      <Transition name="slide-detail">
        <div v-if="showDetail" class="split-detail">
          <div class="detail-header">
            <span class="detail-title">{{ editingAction ? '编辑收支' : '添加收支' }}</span>
            <el-button :icon="Close" text circle @click="onCloseDetail" />
          </div>
          <div class="detail-body">
            <div class="form-section">
              <!-- 名称 -->
              <div class="form-item">
                <label class="form-label">收支名称</label>
                <el-input
                  v-model="actionForm.hname"
                  placeholder="请输入收支名称"
                  size="large"
                  maxlength="6"
                />
              </div>

              <!-- 类型选择 -->
              <div class="form-item">
                <label class="form-label">收支类型</label>
                <div class="radio-group">
                  <div
                    class="radio-item radio-income"
                    :class="{ active: actionForm.handle === ActionHandle.IN }"
                    @click="actionForm.handle = ActionHandle.IN"
                  >
                    <div class="radio-dot"></div>
                    <span class="radio-text">流入</span>
                    <span class="radio-desc">账户金额增加</span>
                  </div>
                  <div
                    class="radio-item radio-expense"
                    :class="{ active: actionForm.handle === ActionHandle.OUT }"
                    @click="actionForm.handle = ActionHandle.OUT"
                  >
                    <div class="radio-dot"></div>
                    <span class="radio-text">流出</span>
                    <span class="radio-desc">账户金额减少</span>
                  </div>
                  <div
                    class="radio-item radio-transfer"
                    :class="{ active: actionForm.handle === ActionHandle.TRANSFER }"
                    @click="actionForm.handle = ActionHandle.TRANSFER"
                  >
                    <div class="radio-dot"></div>
                    <span class="radio-text">转账</span>
                    <span class="radio-desc">账户间流转</span>
                  </div>
                </div>
              </div>

              <!-- 转账不计入设置（仅转账时显示） -->
              <div v-if="isTransfer && actionForm.exempt" class="form-item">
                <label class="form-label">
                  不计入设置
                  <el-icon class="help-icon" @click="showHelpDialog = true"><QuestionFilled /></el-icon>
                </label>
                <div class="transfer-exempt-card">
                  <div class="transfer-account from" :class="{ active: fromExempt }">
                    <div class="transfer-account-label">转出账户</div>
                    <div class="transfer-account-switch">
                      <span class="switch-label">不计入总金额</span>
                      <el-switch v-model="fromExempt" size="small" />
                    </div>
                  </div>
                  <div class="transfer-arrow">
                    <el-icon :size="20"><ArrowRight /></el-icon>
                  </div>
                  <div class="transfer-account to" :class="{ active: toExempt }">
                    <div class="transfer-account-label">转入账户</div>
                    <div class="transfer-account-switch">
                      <span class="switch-label">不计入总金额</span>
                      <el-switch v-model="toExempt" size="small" />
                    </div>
                  </div>
                </div>
                <div class="input-hint">选择哪个账户的金额变动不计入净资产统计</div>
              </div>

              <!-- 不计入开关 -->
              <div class="form-item switch-item">
                <div class="switch-info">
                  <label class="form-label">不计入总金额</label>
                  <span class="form-hint">开启后该收支不计入统计</span>
                </div>
                <el-switch v-model="actionForm.exempt" />
              </div>

              <!-- 禁用开关（仅编辑时显示） -->
              <div v-if="editingAction" class="form-item switch-item">
                <div class="switch-info">
                  <label class="form-label">
                    禁用此收支
                    <el-icon class="help-icon" @click="showDisableHelpDialog = true"><QuestionFilled /></el-icon>
                  </label>
                  <span class="form-hint">禁用后不会出现在记账选项中</span>
                </div>
                <el-switch v-model="actionForm.disable" />
              </div>
            </div>
          </div>
          <div class="detail-footer">
            <el-button @click="onCloseDetail">取消</el-button>
            <el-button type="primary" @click="onSubmit">
              {{ editingAction ? '保存' : '添加' }}
            </el-button>
          </div>
        </div>
      </Transition>
    </div>

    <!-- 帮助对话框 -->
    <el-dialog
      v-model="showHelpDialog"
      title="不计入设置说明"
      width="400px"
      :z-index="4000"
    >
      <div class="help-content">
        <p><strong>不计入总金额</strong>一般用于资金代管、借钱还钱等场景。</p>
        <div class="help-item">
          <div class="help-item-title">转出不计入</div>
          <div class="help-item-desc">转出账户的金额变动不计入净资产</div>
        </div>
        <div class="help-item">
          <div class="help-item-title">转入不计入</div>
          <div class="help-item-desc">转入账户的金额变动不计入净资产</div>
        </div>
        <div class="help-item">
          <div class="help-item-title">都不计入</div>
          <div class="help-item-desc">两个账户的金额变动都不计入净资产</div>
        </div>
        <div class="help-warning">
          <el-icon><QuestionFilled /></el-icon>
          <span>注意：信用卡等负债账户无法选择此项</span>
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="showHelpDialog = false">我知道了</el-button>
      </template>
    </el-dialog>

    <!-- 禁用帮助对话框 -->
    <el-dialog
      v-model="showDisableHelpDialog"
      title="禁用收支说明"
      width="400px"
      :z-index="4000"
    >
      <div class="help-content">
        <p>禁用后该收支类型将不会出现在记账页面的选项中。</p>
        <div class="help-item">
          <div class="help-item-title">快记模板</div>
          <div class="help-item-desc">使用此收支的快记模板将被清空收支设置，需要重新选择</div>
        </div>
        <div class="help-item">
          <div class="help-item-title">已有账单</div>
          <div class="help-item-desc">已记录的账单不会受影响，数据会正常保留</div>
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="showDisableHelpDialog = false">我知道了</el-button>
      </template>
    </el-dialog>
  </el-drawer>
</template>

<style scoped>
/* 抽屉头部 */
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

.drawer-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

/* 分栏布局 */
.split-list {
  width: 100%;
  padding: 20px;
  transition: width 0.3s ease;
  background: var(--color-bg-card);
}

.split-list.has-detail {
  width: 340px;
  border-right: 1px solid var(--color-border);
}

.split-detail {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, var(--color-bg-page) 0%, var(--color-bg-card) 100%);
  overflow: hidden;
  position: relative;
}

.split-detail::before {
  content: '';
  position: absolute;
  top: -60px;
  right: -60px;
  width: 200px;
  height: 200px;
  background: linear-gradient(135deg, var(--color-transfer) 0%, var(--color-income) 100%);
  border-radius: 50%;
  opacity: 0.08;
  filter: blur(40px);
  pointer-events: none;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  background: transparent;
  position: relative;
  z-index: 1;
}

.detail-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.detail-body {
  flex: 1;
  padding: 0 24px 24px;
  overflow-y: auto;
  position: relative;
  z-index: 1;
}

.detail-footer {
  display: flex;
  gap: 12px;
  padding: 16px 24px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-top: 1px solid var(--color-border-light);
}

.detail-footer .el-button {
  flex: 1;
  height: 44px;
  border-radius: 12px;
  font-weight: 500;
}

/* 详情面板动画 */
.slide-detail-enter-active,
.slide-detail-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-detail-enter-from,
.slide-detail-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

/* 收支列表 */
.action-list {
  min-height: 200px;
}

.action-item {
  display: flex;
  align-items: center;
  padding: 16px 18px;
  margin-bottom: 10px;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.25s ease;
  border: 1.5px solid rgba(0, 0, 0, 0.04);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.action-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
  border-color: rgba(0, 0, 0, 0.06);
}

.action-item.active {
  border-color: var(--color-transfer);
  background: linear-gradient(135deg, rgba(24, 144, 255, 0.08) 0%, rgba(24, 144, 255, 0.04) 100%);
  box-shadow: 0 4px 16px rgba(24, 144, 255, 0.15);
}

.action-info {
  flex: 1;
}

.action-name {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 6px;
}

.action-tags {
  display: flex;
  gap: 8px;
}

.action-tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}

.action-tag.exempt {
  color: var(--color-text-secondary);
  background: var(--color-bg-card);
}

.action-tag.disabled-tag {
  color: var(--color-text-tertiary);
  background: var(--color-bg-page);
}

.action-item.disabled {
  opacity: 0.6;
}

.action-item.disabled .action-name {
  text-decoration: line-through;
  color: var(--color-text-tertiary);
}

.action-arrow {
  color: var(--color-text-tertiary);
  font-size: 14px;
}

/* 表单样式 */
.form-section {
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 16px;
  padding: 24px;
  border: 1px solid rgba(0, 0, 0, 0.04);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
}

.form-item {
  margin-bottom: 24px;
}

.form-item:last-child {
  margin-bottom: 0;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.help-icon {
  font-size: 14px;
  color: var(--color-text-tertiary);
  cursor: help;
}

.help-icon:hover {
  color: var(--color-transfer);
}

/* 帮助对话框 */
.help-content p {
  margin: 0 0 16px;
  font-size: 14px;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.help-item {
  padding: 12px 14px;
  margin-bottom: 10px;
  background: var(--color-bg-page);
  border-radius: 10px;
}

.help-item:last-child {
  margin-bottom: 0;
}

.help-item-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}

.help-item-desc {
  font-size: 13px;
  color: var(--color-text-tertiary);
}

.help-warning {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 10px 14px;
  background: var(--color-expense-bg);
  border-radius: 8px;
  font-size: 13px;
  color: var(--color-expense);
}

/* 单选组 */
.radio-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.radio-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s ease;
  border: 2px solid transparent;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}

.radio-item:hover {
  background: rgba(255, 255, 255, 0.9);
  transform: translateX(4px);
}

.radio-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid var(--color-text-tertiary);
  transition: all 0.25s ease;
  flex-shrink: 0;
}

.radio-text {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.radio-desc {
  margin-left: auto;
  font-size: 13px;
  color: var(--color-text-tertiary);
}

/* 流入 */
.radio-income.active {
  background: linear-gradient(135deg, rgba(82, 196, 26, 0.12) 0%, rgba(82, 196, 26, 0.06) 100%);
  border-color: var(--color-income);
  box-shadow: 0 4px 16px rgba(82, 196, 26, 0.2);
}

.radio-income.active .radio-dot {
  border-color: var(--color-income);
  background: var(--color-income);
  box-shadow: inset 0 0 0 3px #fff, 0 0 0 2px var(--color-income);
}

.radio-income.active .radio-text {
  color: var(--color-income);
}

/* 流出 */
.radio-expense.active {
  background: linear-gradient(135deg, rgba(245, 34, 45, 0.12) 0%, rgba(245, 34, 45, 0.06) 100%);
  border-color: var(--color-expense);
  box-shadow: 0 4px 16px rgba(245, 34, 45, 0.2);
}

.radio-expense.active .radio-dot {
  border-color: var(--color-expense);
  background: var(--color-expense);
  box-shadow: inset 0 0 0 3px #fff, 0 0 0 2px var(--color-expense);
}

.radio-expense.active .radio-text {
  color: var(--color-expense);
}

/* 转账 */
.radio-transfer.active {
  background: linear-gradient(135deg, rgba(24, 144, 255, 0.12) 0%, rgba(24, 144, 255, 0.06) 100%);
  border-color: var(--color-transfer);
  box-shadow: 0 4px 16px rgba(24, 144, 255, 0.2);
}

.radio-transfer.active .radio-dot {
  border-color: var(--color-transfer);
  background: var(--color-transfer);
  box-shadow: inset 0 0 0 3px #fff, 0 0 0 2px var(--color-transfer);
}

.radio-transfer.active .radio-text {
  color: var(--color-transfer);
}

/* 开关项 */
.switch-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}

.switch-info {
  flex: 1;
}

.switch-info .form-label {
  margin-bottom: 4px;
  text-transform: none;
  font-size: 15px;
  letter-spacing: 0;
}

.form-hint {
  font-size: 13px;
  color: var(--color-text-tertiary);
}

.form-hint.warning {
  color: var(--color-expense);
  display: block;
  margin-top: 4px;
}

.input-hint {
  margin-top: 10px;
  font-size: 12px;
  color: var(--color-text-tertiary);
}

/* 转账不计入卡片 */
.transfer-exempt-card {
  display: flex;
  align-items: stretch;
  gap: 0;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid var(--color-border-light);
}

.transfer-account {
  flex: 1;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: all 0.25s ease;
}

.transfer-account.from {
  background: rgba(245, 34, 45, 0.04);
}

.transfer-account.to {
  background: rgba(82, 196, 26, 0.04);
}

.transfer-account.active.from {
  background: rgba(245, 34, 45, 0.12);
}

.transfer-account.active.to {
  background: rgba(82, 196, 26, 0.12);
}

.transfer-account-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  text-align: center;
}

.transfer-account.from .transfer-account-label {
  color: var(--color-expense);
}

.transfer-account.to .transfer-account-label {
  color: var(--color-income);
}

.transfer-account-switch {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.switch-label {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.transfer-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 12px;
  color: var(--color-transfer);
  background: rgba(24, 144, 255, 0.08);
}

/* 暗黑模式 */
html.dark .transfer-exempt-card {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .transfer-account.from {
  background: rgba(245, 34, 45, 0.15);
}

html.dark .transfer-account.to {
  background: rgba(82, 196, 26, 0.15);
}

html.dark .transfer-account.active.from {
  background: rgba(245, 34, 45, 0.3);
}

html.dark .transfer-account.active.to {
  background: rgba(82, 196, 26, 0.3);
}

html.dark .transfer-arrow {
  background: rgba(24, 144, 255, 0.2);
}

html.dark .transfer-account-label {
  color: var(--color-text-primary);
}

html.dark .transfer-account.from .transfer-account-label {
  color: #ff7875;
}

html.dark .transfer-account.to .transfer-account-label {
  color: #95de64;
}

html.dark .switch-label {
  color: var(--color-text-secondary);
}
</style>
