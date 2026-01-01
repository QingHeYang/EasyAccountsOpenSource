<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showLoadingToast, closeToast, showToast, showConfirmDialog } from 'vant'
import { typeApi, type Type, type TypeWithChildren } from '@shared/api/type'
import { actionApi, type Action } from '@shared/api/action'
import { useSmartBack } from '@shared/composables/useSmartBack'

const route = useRoute()
const router = useRouter()
const { smartBack } = useSmartBack()

// 编辑模式
const typeId = computed(() => {
  const id = route.params.id as string
  return id ? parseInt(id) : null
})
const isEdit = computed(() => typeId.value !== null)

// 表单数据
const tname = ref('')
const parentId = ref<number>(-1)
const parentName = ref('')
const actionId = ref<number | undefined>(undefined)
const selectedAction = ref<Action | null>(null)
const analysisDisable = ref(false)
const curParent = ref(-1) // 当前分类的原始父级

// 是否可以编辑收支（父级有收支时不可编辑）
const canEditAction = ref(true)

// 选择器状态
const showParentPicker = ref(false)
const showActionSheet = ref(false)

// 数据列表
const parentList = ref<TypeWithChildren[]>([])
const actionList = ref<Action[]>([])

// 父级选择器列表
const parentColumns = computed(() => {
  return parentList.value.map(item => ({
    text: item.tname,
    value: item.id,
  }))
})

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

// 加载分类数据（编辑模式）
async function loadType() {
  if (!typeId.value) return

  try {
    const res = await typeApi.getById(typeId.value)
    const data = res.data.data
    tname.value = data.tname
    curParent.value = data.parent
    analysisDisable.value = data.analysisDisable

    if (data.action) {
      selectedAction.value = data.action
      actionId.value = data.action.id
    }

    // 如果是二级分类，加载父级信息
    if (data.parent !== -1 && data.parent !== 0) {
      const parentRes = await typeApi.getById(data.parent)
      const parentData = parentRes.data.data
      parentId.value = parentData.id
      parentName.value = parentData.tname

      // 父级有收支时，子分类不可编辑收支
      if (parentData.action) {
        canEditAction.value = false
      }
    }
  } catch (err) {
    showToast('获取数据失败')
    console.error(err)
  }
}

// 加载一级分类列表
async function loadParentList() {
  try {
    const res = await typeApi.getByParent(-1)
    parentList.value = res.data.data || []
  } catch (err) {
    console.error('获取一级分类失败', err)
  }
}

// 加载收支列表
async function loadActionList() {
  try {
    const res = await actionApi.getAll()
    actionList.value = res.data.data || []
  } catch (err) {
    console.error('获取收支列表失败', err)
  }
}

// 打开父级选择器
function openParentPicker() {
  // 编辑模式下，一级分类不可更改父级
  if (isEdit.value && (curParent.value === -1 || curParent.value === 0)) {
    showToast('当前已经是一级分类了')
    return
  }
  loadParentList()
  showParentPicker.value = true
}

// 确认选择父级
function onParentConfirm({ selectedOptions }: { selectedOptions: Array<{ text: string; value: number }> }) {
  showParentPicker.value = false
  if (selectedOptions.length > 0) {
    const selected = selectedOptions[0]
    parentId.value = selected.value
    parentName.value = selected.text

    // 查找选中的父级分类
    const parent = parentList.value.find(p => p.id === selected.value)
    if (parent?.action) {
      // 父级有收支，自动继承
      selectedAction.value = parent.action
      actionId.value = parent.action.id
      canEditAction.value = false
    } else {
      // 父级无收支，可自由绑定
      selectedAction.value = null
      actionId.value = undefined
      canEditAction.value = true
    }
  }
}

// 取消/清空父级
function onParentCancel() {
  showParentPicker.value = false
  if (isEdit.value) {
    // 编辑模式下清空父级（变成一级分类）
    parentId.value = -1
    parentName.value = ''
    canEditAction.value = true
  }
}

// 打开收支选择器
function openActionSheet() {
  if (!canEditAction.value) {
    showToast('当前分类不可绑定收支')
    return
  }
  loadActionList()
  showActionSheet.value = true
}

// 选择收支
function onSelectAction(action: Action) {
  // 一级分类绑定收支时提示
  if (curParent.value === -1 || curParent.value === 0 || parentId.value === -1) {
    showConfirmDialog({
      title: '注意',
      message: '一级分类绑定收支后\n二级分类将自动同步绑定该收支\n是否继续？',
    })
      .then(() => {
        selectedAction.value = action
        actionId.value = action.id
        showActionSheet.value = false
      })
      .catch(() => {
        // 取消
      })
  } else {
    selectedAction.value = action
    actionId.value = action.id
    showActionSheet.value = false
  }
}

// 清空收支绑定
function clearAction() {
  selectedAction.value = null
  actionId.value = undefined
  showActionSheet.value = false
}

// 验证表单
function validateForm(): boolean {
  if (!tname.value.trim()) {
    showToast('请输入分类名称')
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
    if (isEdit.value && typeId.value) {
      // 编辑模式
      await typeApi.update(typeId.value, {
        tname: tname.value.trim(),
        parent: parentId.value === -1 ? undefined : parentId.value,
        actionId: actionId.value,  // undefined 时 JSON 不传此字段
        analysisDisable: analysisDisable.value,
      })
    } else {
      // 新增模式
      await typeApi.add({
        tname: tname.value.trim(),
        parent: parentId.value === -1 ? undefined : parentId.value,
        actionId: actionId.value,  // undefined 时 JSON 不传此字段
        analysisDisable: analysisDisable.value,
      })
    }

    closeToast()
    showToast(isEdit.value ? '保存成功' : '添加成功')
    router.push('/setting/type')
  } catch (err) {
    closeToast()
    showToast('操作失败')
    console.error(err)
  }
}

// 归档
async function onArchive() {
  const msg = curParent.value === -1
    ? '确定将此分类归档吗？\n注意，一级分类归档会连带子分类一起归档\n归档后将不再显示，但不会删除数据'
    : '确定将此分类归档吗？\n归档后将不再显示，但不会删除数据'

  try {
    await showConfirmDialog({
      title: '归档',
      message: msg,
    })

    await typeApi.archive(typeId.value!, true)
    showToast('已归档')
    router.push('/setting/type')
  } catch {
    // 取消
  }
}

// 停用
async function onDelete() {
  const msg = curParent.value === -1
    ? '确定停用此分类吗？\n注意，一级分类停用会连带子分类一起停用\n停用后将无法再使用此分类'
    : '确定停用此分类吗？\n停用后将无法再使用此分类'

  try {
    await showConfirmDialog({
      title: '停用',
      message: msg,
    })

    await typeApi.delete(typeId.value!)
    showToast('已停用')
    router.push('/setting/type')
  } catch {
    // 取消
  }
}

function onBack() {
  smartBack('/setting/type')
}

onMounted(() => {
  if (isEdit.value) {
    loadType()
  }
})
</script>

<template>
  <div class="type-add-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="header-left" @click="onBack">
        <van-icon name="arrow-left" size="20" />
      </div>
      <div class="header-title">{{ isEdit ? '编辑分类' : '添加分类' }}</div>
      <div class="header-right" @click="onSubmit">
        <van-icon name="success" size="20" />
      </div>
    </div>

    <!-- 表单 -->
    <div class="page-body">
      <div class="form-card">
        <!-- 分类名称 -->
        <div class="form-item">
          <label class="form-label required">分类名称</label>
          <input
            v-model="tname"
            type="text"
            class="form-input"
            placeholder="请输入分类名称"
          />
        </div>

        <!-- 父级分类 -->
        <div class="form-item" @click="openParentPicker">
          <label class="form-label">父级分类</label>
          <div class="form-select">
            <span :class="{ placeholder: !parentName }">
              {{ parentName || '不选择则为一级分类' }}
            </span>
            <van-icon name="arrow" size="16" />
          </div>
        </div>

        <!-- 绑定收支 -->
        <div class="form-item" @click="openActionSheet">
          <label class="form-label">绑定收支</label>
          <div class="form-select" :class="{ disabled: !canEditAction }">
            <span v-if="selectedAction" class="action-display">
              <span class="action-tag" :class="getActionClass(selectedAction.handle)">
                {{ selectedAction.hname }}
              </span>
              <span v-if="selectedAction.exempt" class="exempt-tag">不计入</span>
            </span>
            <span v-else class="placeholder">点击绑定收支类型</span>
            <van-icon name="arrow" size="16" />
          </div>
        </div>

        <!-- 不参与统计 -->
        <div class="form-item switch-item">
          <label class="form-label">不参与统计</label>
          <van-switch v-model="analysisDisable" size="20" />
        </div>
      </div>

      <!-- 操作按钮（编辑模式） -->
      <div v-if="isEdit" class="action-buttons">
        <button class="action-btn archive" @click="onArchive">
          <van-icon name="tosend" />
          归档
        </button>
        <button class="action-btn delete" @click="onDelete">
          <van-icon name="close" />
          停用
        </button>
      </div>
    </div>

    <!-- 父级选择器 -->
    <van-popup v-model:show="showParentPicker" round position="bottom" teleport="body">
      <van-picker
        title="选择一级分类"
        :columns="parentColumns"
        @confirm="onParentConfirm"
        @cancel="onParentCancel"
        :cancel-button-text="isEdit ? '清空' : '取消'"
      />
    </van-popup>

    <!-- 收支选择器 -->
    <van-action-sheet
      v-model:show="showActionSheet"
      title="绑定收支"
      cancel-text="清空绑定"
      close-on-click-action
      teleport="body"
      @cancel="clearAction"
    >
      <div class="action-list">
        <div
          v-for="action in actionList"
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
              <span v-if="action.exempt" class="exempt-tag">不计入</span>
            </div>
          </div>
          <van-icon
            v-if="actionId === action.id"
            name="success"
            class="check-icon"
          />
        </div>
      </div>
    </van-action-sheet>
  </div>
</template>

<style scoped>
.type-add-page {
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
  background: var(--color-transfer);
  color: #fff;
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
  border-radius: 12px;
  outline: none;
  box-sizing: border-box;
}

.form-input::placeholder {
  color: var(--color-text-tertiary);
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

.form-select.disabled {
  opacity: 0.6;
}

.form-select .placeholder {
  color: var(--color-text-tertiary);
}

.switch-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.switch-item .form-label {
  margin-bottom: 0;
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

/* 操作按钮 */
.action-buttons {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 14px;
  font-size: 15px;
  font-weight: 500;
  border: none;
  border-radius: 12px;
  cursor: pointer;
}

.action-btn.archive {
  background: var(--color-note);
  color: #fff;
}

.action-btn.delete {
  background: var(--color-expense);
  color: #fff;
}

.action-btn:active {
  opacity: 0.8;
}

/* 收支列表 */
.action-list {
  padding: 16px;
}

.action-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: var(--color-bg-page);
  border-radius: 12px;
  margin-bottom: 10px;
}

.action-item:last-child {
  margin-bottom: 0;
}

.action-item:active {
  opacity: 0.8;
}

.action-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.action-name {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.action-tags {
  display: flex;
  align-items: center;
  gap: 8px;
}

.check-icon {
  color: var(--color-transfer);
  font-size: 20px;
}
</style>

<!-- 非 scoped 样式 -->
<style>
.type-add-page .page-header {
  background: rgba(245, 245, 245, 0.8);
}

html.dark .type-add-page .page-header {
  background: rgba(10, 10, 10, 0.8);
}
</style>
