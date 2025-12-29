<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Close, ArrowRight } from '@element-plus/icons-vue'
import { actionApi, type Action, ActionHandle } from '@shared/api/action'

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

async function loadActions() {
  loading.value = true
  try {
    const res = await actionApi.getAll()
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
  }
}

async function onSubmit() {
  if (!actionForm.value.hname.trim()) {
    ElMessage.warning('请输入收支名称')
    return
  }

  try {
    if (editingAction.value) {
      await actionApi.update(editingAction.value.id, {
        hname: actionForm.value.hname.trim(),
        handle: actionForm.value.handle,
        exempt: actionForm.value.exempt,
      })
      ElMessage.success('保存成功')
    } else {
      await actionApi.add({
        hname: actionForm.value.hname.trim(),
        handle: actionForm.value.handle,
        exempt: actionForm.value.exempt,
      })
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
            :class="{ active: editingAction?.id === action.id }"
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
                <span v-if="action.exempt" class="action-tag exempt">不计入</span>
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

              <!-- 不计入开关 -->
              <div class="form-item switch-item">
                <div class="switch-info">
                  <label class="form-label">不计入总金额</label>
                  <span class="form-hint">开启后该收支不计入统计</span>
                </div>
                <el-switch v-model="actionForm.exempt" />
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
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
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
</style>
