<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Close,
  ArrowRight,
  FolderOpened,
  Folder,
  Upload,
  Download,
  InfoFilled,
  Edit
} from '@element-plus/icons-vue'
import { typeApi, type TypeWithChildren } from '@shared/api/type'
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
const types = ref<TypeWithChildren[]>([])
const archivedTypes = ref<TypeWithChildren[]>([])
const expandedTypeIds = ref<number[]>([])
const editingType = ref<TypeWithChildren | null>(null)
const typeViewMode = ref<'list' | 'archive'>('list')

// 收支数据
const actions = ref<Action[]>([])

// 表单
const typeForm = ref({
  tname: '',
  parentId: -1 as number,
  parentName: '',
  actionId: undefined as number | undefined,
  selectedAction: null as Action | null,
  analysisDisable: false,
})
const canEditAction = ref(true)
const curParent = ref(-1)

// 选择器
const showParentPicker = ref(false)
const parentList = ref<TypeWithChildren[]>([])
const showActionPicker = ref(false)

// 监听外部 visible 变化
watch(() => props.visible, (val) => {
  drawerVisible.value = val
  if (val) {
    typeViewMode.value = 'list'
    loadTypes()
    loadArchivedTypes()
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

// 抽屉宽度
const drawerSize = computed(() => showDetail.value ? '800px' : '480px')

// 是否是一级分类
const isFirstLevelType = computed(() => {
  return curParent.value === -1 || curParent.value === 0 || typeForm.value.parentId === -1
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

async function loadTypes() {
  loading.value = true
  try {
    const res = await typeApi.getAll()
    types.value = res.data.data || []
  } catch (err) {
    console.error('获取分类列表失败', err)
    ElMessage.error('获取分类列表失败')
  } finally {
    loading.value = false
  }
}

async function loadArchivedTypes() {
  try {
    const res = await typeApi.getArchived()
    archivedTypes.value = res.data.data || []
  } catch (err) {
    console.error('获取归档分类失败', err)
  }
}

async function loadParentList() {
  try {
    const res = await typeApi.getByParent(-1)
    parentList.value = res.data.data || []
  } catch (err) {
    console.error('获取一级分类失败', err)
  }
}

async function loadActions() {
  try {
    const res = await actionApi.getAll()
    actions.value = res.data.data
  } catch (err) {
    console.error('获取收支列表失败', err)
  }
}

function toggleTypeExpand(id: number) {
  const idx = expandedTypeIds.value.indexOf(id)
  if (idx >= 0) {
    expandedTypeIds.value.splice(idx, 1)
  } else {
    expandedTypeIds.value.push(id)
  }
}

function isTypeExpanded(id: number) {
  return expandedTypeIds.value.includes(id)
}

function onAdd() {
  editingType.value = null
  resetForm()
  canEditAction.value = true
  curParent.value = -1
  showDetail.value = true
  loadParentList()
  loadActions()
}

async function onEdit(type: TypeWithChildren) {
  editingType.value = type
  curParent.value = type.parent

  typeForm.value = {
    tname: type.tname,
    parentId: type.parent,
    parentName: '',
    actionId: type.action?.id,
    selectedAction: type.action || null,
    analysisDisable: type.analysisDisable,
  }

  // 加载父级信息
  if (type.parent !== -1 && type.parent !== 0) {
    try {
      const res = await typeApi.getById(type.parent)
      const parentData = res.data.data
      typeForm.value.parentName = parentData.tname
      if (parentData.action) {
        canEditAction.value = false
      } else {
        canEditAction.value = true
      }
    } catch {
      canEditAction.value = true
    }
  } else {
    canEditAction.value = true
  }

  showDetail.value = true
  loadParentList()
  loadActions()
}

function onCloseDetail() {
  showDetail.value = false
  resetForm()
}

function resetForm() {
  editingType.value = null
  typeForm.value = {
    tname: '',
    parentId: -1,
    parentName: '',
    actionId: undefined,
    selectedAction: null,
    analysisDisable: false,
  }
  canEditAction.value = true
  curParent.value = -1
}

// 选择父级分类
function openParentPicker() {
  if (editingType.value && (curParent.value === -1 || curParent.value === 0)) {
    ElMessage.warning('当前已经是一级分类了')
    return
  }
  loadParentList()
  showParentPicker.value = true
}

function onSelectParent(parent: TypeWithChildren | null) {
  showParentPicker.value = false

  if (parent) {
    typeForm.value.parentId = parent.id
    typeForm.value.parentName = parent.tname

    if (parent.action) {
      typeForm.value.selectedAction = parent.action
      typeForm.value.actionId = parent.action.id
      canEditAction.value = false
    } else {
      typeForm.value.selectedAction = null
      typeForm.value.actionId = undefined
      canEditAction.value = true
    }
  } else {
    typeForm.value.parentId = -1
    typeForm.value.parentName = ''
    canEditAction.value = true
  }
}

// 选择收支
function openActionPicker() {
  if (!canEditAction.value) {
    ElMessage.warning('当前分类不可绑定收支')
    return
  }
  loadActions()
  showActionPicker.value = true
}

function onSelectTypeAction(action: Action | null) {
  typeForm.value.selectedAction = action
  typeForm.value.actionId = action?.id
  showActionPicker.value = false
}

async function onSubmit() {
  if (!typeForm.value.tname.trim()) {
    ElMessage.warning('请输入分类名称')
    return
  }

  try {
    const params = {
      tname: typeForm.value.tname.trim(),
      parent: typeForm.value.parentId === -1 ? undefined : typeForm.value.parentId,
      actionId: typeForm.value.actionId,
      analysisDisable: typeForm.value.analysisDisable,
    }

    if (editingType.value) {
      await typeApi.update(editingType.value.id, params)
      ElMessage.success('保存成功')
    } else {
      await typeApi.add(params)
      ElMessage.success('添加成功')
    }
    onCloseDetail()
    loadTypes()
  } catch (err) {
    console.error('操作失败', err)
    ElMessage.error('操作失败')
  }
}

async function onArchive() {
  if (!editingType.value) return

  const isParent = curParent.value === -1 || curParent.value === 0
  const msg = isParent
    ? '一级分类归档会连带子分类一起归档，归档后将不再显示，但不会删除数据。确定归档吗？'
    : '归档后将不再显示，但不会删除数据。确定归档吗？'

  try {
    await ElMessageBox.confirm(msg, '归档分类', {
      confirmButtonText: '确定归档',
      cancelButtonText: '取消',
      type: 'warning',
      customClass: 'high-zindex-msgbox',
    })

    await typeApi.archive(editingType.value.id, true)
    ElMessage.success('已归档')
    onCloseDetail()
    loadTypes()
    loadArchivedTypes()
  } catch {
    // 取消
  }
}

async function onDelete() {
  if (!editingType.value) return

  const isParent = curParent.value === -1 || curParent.value === 0
  const msg = isParent
    ? '一级分类停用会连带子分类一起停用，停用后将无法再使用此分类。确定停用吗？'
    : '停用后将无法再使用此分类。确定停用吗？'

  try {
    await ElMessageBox.confirm(msg, '停用分类', {
      confirmButtonText: '确定停用',
      cancelButtonText: '取消',
      type: 'warning',
      customClass: 'high-zindex-msgbox',
    })

    await typeApi.delete(editingType.value.id)
    ElMessage.success('已停用')
    onCloseDetail()
    loadTypes()
  } catch {
    // 取消
  }
}

async function onRestore(type: TypeWithChildren) {
  const isParent = type.parent === -1 || type.parent === 0
  const msg = isParent
    ? `一级分类取出后，下属二级分类会一同取出。确定取出"${type.tname}"吗？`
    : `二级分类取出后，会回到一级分类中。确定取出"${type.tname}"吗？`

  try {
    await ElMessageBox.confirm(msg, '取出归档', {
      confirmButtonText: '确定取出',
      cancelButtonText: '取消',
      type: 'info',
      customClass: 'high-zindex-msgbox',
    })

    await typeApi.archive(type.id, false)
    ElMessage.success('取出成功')
    loadArchivedTypes()
    loadTypes()
  } catch {
    // 取消
  }
}
</script>

<template>
  <el-drawer
    v-model="drawerVisible"
    title="分类管理"
    direction="rtl"
    :size="drawerSize"
    :z-index="3000"
    class="setting-drawer split-layout"
  >
    <!-- 抽屉头部 -->
    <template #header>
      <div class="drawer-header">
        <div class="drawer-header-left">
          <span class="drawer-title">分类管理</span>
        </div>
        <el-button :icon="Plus" type="primary" @click="onAdd">添加</el-button>
      </div>
    </template>

    <div class="drawer-split-view">
      <!-- 左侧：列表 -->
      <div class="split-list" :class="{ 'has-detail': showDetail }">
        <!-- 工具栏 -->
        <div class="type-toolbar">
          <div class="capsule-tabs">
            <!-- 滑块 -->
            <div class="slider-track">
              <div class="slider" :class="{ 'at-archive': typeViewMode === 'archive' }"></div>
            </div>
            <!-- Tab 项 -->
            <div
              class="capsule-tab"
              :class="{ active: typeViewMode === 'list' }"
              @click="typeViewMode = 'list'"
            >
              <el-icon><Folder /></el-icon>
              <span>分类列表</span>
            </div>
            <div
              class="capsule-tab"
              :class="{ active: typeViewMode === 'archive' }"
              @click="typeViewMode = 'archive'"
            >
              <el-icon><FolderOpened /></el-icon>
              <span>归档</span>
            </div>
          </div>
        </div>

        <!-- 分类列表 -->
        <div v-if="typeViewMode === 'list'" v-loading="loading" class="type-list">
          <div v-for="parent in types" :key="parent.id" class="type-group">
            <div
              class="type-parent"
              :class="{ active: editingType?.id === parent.id }"
            >
              <div class="parent-left" @click="toggleTypeExpand(parent.id)">
                <el-icon class="expand-icon" :class="{ rotated: isTypeExpanded(parent.id) }">
                  <ArrowRight />
                </el-icon>
                <span class="parent-name">{{ parent.tname }}</span>
                <span
                  v-if="parent.action"
                  class="action-tag"
                  :style="{
                    color: getHandleInfo(parent.action.handle).color,
                    background: getHandleInfo(parent.action.handle).bg,
                  }"
                >
                  {{ parent.action.hname }}
                </span>
              </div>
              <el-button class="edit-btn" text :icon="Edit" @click="onEdit(parent)" />
            </div>
            <Transition name="expand">
              <div v-if="isTypeExpanded(parent.id)" class="type-children">
                <div
                  v-for="child in parent.childrenTypes"
                  :key="child.id"
                  class="type-child"
                  :class="{ active: editingType?.id === child.id }"
                  @click="onEdit(child)"
                >
                  <div class="child-left">
                    <span class="child-name">{{ child.tname }}</span>
                    <span
                      v-if="child.action"
                      class="action-tag small"
                      :style="{
                        color: getHandleInfo(child.action.handle).color,
                        background: getHandleInfo(child.action.handle).bg,
                      }"
                    >
                      {{ child.action.hname }}
                    </span>
                  </div>
                  <el-icon class="child-edit-icon"><Edit /></el-icon>
                </div>
                <div v-if="!parent.childrenTypes?.length" class="no-children">
                  暂无子分类
                </div>
              </div>
            </Transition>
          </div>
          <el-empty v-if="!loading && types.length === 0" description="暂无分类" />
        </div>

        <!-- 归档列表 -->
        <div v-else class="archive-list">
          <div v-for="parent in archivedTypes" :key="parent.id" class="type-group archived">
            <div class="type-parent">
              <div class="parent-left" @click="toggleTypeExpand(parent.id)">
                <el-icon class="expand-icon" :class="{ rotated: isTypeExpanded(parent.id) }">
                  <ArrowRight />
                </el-icon>
                <span class="parent-name">{{ parent.tname }}</span>
              </div>
              <el-button type="primary" text :icon="Upload" @click="onRestore(parent)">取出</el-button>
            </div>
            <Transition name="expand">
              <div v-if="isTypeExpanded(parent.id)" class="type-children">
                <div
                  v-for="child in parent.childrenTypes"
                  :key="child.id"
                  class="type-child archived"
                >
                  <span class="child-name">{{ child.tname }}</span>
                  <el-button type="primary" text size="small" :icon="Upload" @click="onRestore(child)">取出</el-button>
                </div>
                <div v-if="!parent.childrenTypes?.length" class="no-children">
                  暂无子分类
                </div>
              </div>
            </Transition>
          </div>
          <el-empty v-if="archivedTypes.length === 0" description="暂无归档分类" />
        </div>
      </div>

      <!-- 右侧：详情/表单 -->
      <Transition name="slide-detail">
        <div v-if="showDetail" class="split-detail">
          <div class="detail-header">
            <span class="detail-title">{{ editingType ? '编辑分类' : '添加分类' }}</span>
            <el-button :icon="Close" text circle @click="onCloseDetail" />
          </div>
          <div class="detail-body">
            <div class="form-section">
              <!-- 分类名称 -->
              <div class="form-item">
                <label class="form-label">分类名称 <span class="required">*</span></label>
                <el-input
                  v-model="typeForm.tname"
                  placeholder="请输入分类名称"
                  size="large"
                />
              </div>

              <!-- 父级分类 -->
              <div class="form-item">
                <label class="form-label">父级分类</label>
                <div
                  class="form-select"
                  :class="{ disabled: editingType && isFirstLevelType }"
                  @click="openParentPicker"
                >
                  <span :class="{ placeholder: !typeForm.parentName }">
                    {{ typeForm.parentName || (isFirstLevelType ? '无（一级分类）' : '点击选择父级分类') }}
                  </span>
                  <el-icon><ArrowRight /></el-icon>
                </div>
              </div>

              <!-- 收支绑定 -->
              <div class="form-item">
                <label class="form-label">收支绑定</label>
                <div
                  class="form-select"
                  :class="{ disabled: !canEditAction }"
                  @click="openActionPicker"
                >
                  <span v-if="typeForm.selectedAction" class="action-display">
                    <span
                      class="action-tag"
                      :style="{
                        color: getHandleInfo(typeForm.selectedAction.handle).color,
                        background: getHandleInfo(typeForm.selectedAction.handle).bg,
                      }"
                    >
                      {{ typeForm.selectedAction.hname }}
                    </span>
                    <span v-if="typeForm.selectedAction.exempt" class="exempt-tag">不计入</span>
                  </span>
                  <span v-else class="placeholder">{{ canEditAction ? '点击选择收支' : '继承自父级' }}</span>
                  <el-icon><ArrowRight /></el-icon>
                </div>
                <div class="input-hint">绑定收支后，选择此分类时自动选择对应收支</div>
              </div>

              <!-- 不计入分析 -->
              <div class="form-item switch-item">
                <div class="switch-info">
                  <label class="form-label">不计入分析</label>
                  <span class="form-hint">开启后此分类不计入统计分析</span>
                </div>
                <el-switch v-model="typeForm.analysisDisable" />
              </div>
            </div>
          </div>
          <div class="detail-footer">
            <div v-if="editingType" class="footer-danger">
              <el-button type="warning" text @click="onArchive">
                <el-icon><Download /></el-icon>
                <span>归档分类</span>
              </el-button>
              <span class="footer-divider"></span>
              <el-button type="danger" text @click="onDelete">停用分类</el-button>
            </div>
            <div class="footer-main">
              <el-button @click="onCloseDetail">取消</el-button>
              <el-button type="primary" @click="onSubmit">
                {{ editingType ? '保存修改' : '添加分类' }}
              </el-button>
            </div>
          </div>
        </div>
      </Transition>
    </div>

    <!-- 父级选择器 -->
    <el-dialog
      v-model="showParentPicker"
      title="选择父级分类"
      width="400"
      :z-index="4000"
      class="picker-dialog"
    >
      <div class="picker-tip">
        <el-icon><InfoFilled /></el-icon>
        <span>选择一个一级分类作为父级，或点击下方按钮设为一级分类</span>
      </div>
      <div class="picker-list">
        <div
          v-for="parent in parentList"
          :key="parent.id"
          class="picker-item"
          :class="{ active: typeForm.parentId === parent.id }"
          @click="onSelectParent(parent)"
        >
          <div class="picker-info">
            <span class="picker-name">{{ parent.tname }}</span>
            <div v-if="parent.action" class="picker-tags">
              <span
                class="action-tag"
                :style="{
                  color: getHandleInfo(parent.action.handle).color,
                  background: getHandleInfo(parent.action.handle).bg,
                }"
              >
                {{ parent.action.hname }}
              </span>
            </div>
          </div>
        </div>
        <el-empty v-if="parentList.length === 0" description="暂无一级分类" :image-size="60" />
      </div>
      <template #footer>
        <el-button @click="onSelectParent(null)">设为一级分类</el-button>
      </template>
    </el-dialog>

    <!-- 收支选择器 -->
    <el-dialog
      v-model="showActionPicker"
      title="选择收支"
      width="400"
      :z-index="4000"
      class="picker-dialog"
    >
      <div class="picker-list">
        <div
          v-for="action in actions"
          :key="action.id"
          class="picker-item"
          :class="{ active: typeForm.actionId === action.id }"
          @click="onSelectTypeAction(action)"
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
              <span v-if="action.exempt" class="exempt-tag">不计入</span>
            </div>
          </div>
        </div>
        <el-empty v-if="actions.length === 0" description="暂无收支类型" :image-size="60" />
      </div>
      <template #footer>
        <el-button @click="onSelectTypeAction(null)">清空收支</el-button>
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

/* 分栏布局 - 使用全局样式 .drawer-split-view */
.split-list {
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
  flex-direction: column;
  gap: 12px;
  padding: 16px 24px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-top: 1px solid var(--color-border-light);
}

.footer-main {
  display: flex;
  gap: 12px;
}

.footer-main .el-button {
  flex: 1;
  height: 44px;
  border-radius: 12px;
  font-weight: 500;
}

.footer-danger {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 4px;
  padding-bottom: 8px;
  border-bottom: 1px dashed var(--color-border-light);
}

.footer-danger .el-button {
  font-size: 13px;
}

.footer-divider {
  width: 1px;
  height: 14px;
  background: var(--color-border);
  margin: 0 8px;
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

/* 工具栏 */
.type-toolbar {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 16px;
}

/* 胶囊 Tab - 毛玻璃效果 */
.capsule-tabs {
  position: relative;
  display: flex;
  align-items: center;
  height: 40px;
  padding: 0 4px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.5);
}

/* 滑块轨道 */
.slider-track {
  position: absolute;
  top: 4px;
  bottom: 4px;
  left: 4px;
  right: 4px;
  pointer-events: none;
}

/* 滑块 */
.slider {
  width: 50%;
  height: 100%;
  background: var(--color-transfer);
  border-radius: 16px;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slider.at-archive {
  transform: translateX(100%);
}

/* Tab 项 */
.capsule-tab {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 0 20px;
  height: 32px;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: color 0.2s ease;
  white-space: nowrap;
}

.capsule-tab:hover:not(.active) {
  color: var(--color-text-primary);
}

.capsule-tab.active {
  color: #ffffff;
}

/* 分类列表 */
.type-list,
.archive-list {
  min-height: 200px;
}

.type-group {
  margin-bottom: 10px;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border-radius: 14px;
  border: 1.5px solid rgba(0, 0, 0, 0.04);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.type-group.archived {
  opacity: 0.8;
}

.type-parent {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.type-parent:hover {
  background: rgba(0, 0, 0, 0.02);
}

.type-parent.active {
  background: linear-gradient(135deg, rgba(24, 144, 255, 0.08) 0%, rgba(24, 144, 255, 0.04) 100%);
}

.parent-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.expand-icon {
  font-size: 12px;
  color: var(--color-text-tertiary);
  transition: transform 0.2s;
}

.expand-icon.rotated {
  transform: rotate(90deg);
}

.parent-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.edit-btn {
  color: var(--color-text-secondary);
}

.edit-btn:hover {
  color: var(--color-transfer);
}

/* 二级分类 */
.type-children {
  border-top: 1px solid var(--color-border-light);
  padding: 12px 16px 16px;
  background: rgba(0, 0, 0, 0.02);
}

.type-child {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  margin-top: 8px;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-light);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.type-child:first-child {
  margin-top: 0;
}

.type-child:hover {
  background: #fff;
  border-color: var(--color-border);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.type-child.active {
  background: linear-gradient(135deg, rgba(24, 144, 255, 0.08) 0%, rgba(24, 144, 255, 0.04) 100%);
  border: 1.5px solid var(--color-transfer);
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.15);
}

.type-child.archived {
  cursor: default;
  opacity: 0.7;
}

.type-child.archived:hover {
  transform: none;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.child-name {
  font-size: 14px;
  color: var(--color-text-primary);
}

.child-edit-icon {
  color: var(--color-text-tertiary);
  opacity: 0;
  transition: all 0.2s;
}

.type-child:hover .child-edit-icon {
  opacity: 1;
  color: var(--color-transfer);
}

.no-children {
  padding: 16px;
  text-align: center;
  font-size: 13px;
  color: var(--color-text-tertiary);
}

/* 展开动画 */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}

/* 表单样式 */
.form-section {
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 16px;
  padding: 24px;
  border: 1px solid var(--color-border);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
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

.required {
  color: var(--color-expense);
}

.input-hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--color-text-tertiary);
}

/* 表单选择器 */
.form-select {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid var(--color-border-light);
}

.form-select:hover {
  background: rgba(255, 255, 255, 1);
  border-color: var(--color-border);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
}

.form-select.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.form-select.disabled:hover {
  background: rgba(255, 255, 255, 0.8);
  border-color: transparent;
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

.action-tag.small {
  font-size: 11px;
  padding: 2px 6px;
}

.child-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.exempt-tag {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--color-bg-page);
  color: var(--color-text-tertiary);
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

/* 选择器弹窗 */
.picker-tip {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px 14px;
  margin-bottom: 12px;
  background: var(--color-transfer-bg);
  border-radius: 10px;
  font-size: 13px;
  color: var(--color-transfer);
  line-height: 1.5;
}

.picker-tip .el-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.picker-list {
  max-height: 400px;
  overflow-y: auto;
}

.picker-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  margin-bottom: 8px;
  background: var(--color-bg-page);
  border-radius: 12px;
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

.picker-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
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
</style>
