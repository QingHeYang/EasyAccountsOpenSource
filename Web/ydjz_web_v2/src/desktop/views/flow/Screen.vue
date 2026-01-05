<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, RefreshRight, Download, Filter, Close, Top } from '@element-plus/icons-vue'
import { screenApi, type ScreenFlowParams } from '@shared/api/screen'
import { actionApi, type Action } from '@shared/api/action'
import { accountApi, type Account } from '@shared/api/account'
import { typeApi } from '@shared/api/type'
import { flowApi, type Flow } from '@shared/api/flow'
import { consumeScreenParams, hasScreenParams, type ScreenParams } from '@shared/services/screenParams'
import FlowItem from '@desktop/components/FlowItem.vue'
import FlowEditor from '@desktop/components/flow/FlowEditor.vue'

// 路由
const route = useRoute()

// ==================== 筛选条件 ====================
const searchNote = ref('')
const fastChoose = ref<number>(0) // 0当月 1上月 2全年 3上年
const startDate = ref('')
const endDate = ref('')
const singleMonth = ref(true)
const accountId = ref<number>(-1)
const handleType = ref<number>(3) // 0流入 1流出 2转账 3全部
const collectOnly = ref(false)
const chooseActions = ref<number[]>([])
const chooseTypes = ref<number[]>([])

// ==================== 数据 ====================
const loading = ref(false)
const flows = ref<Flow[]>([])
const totalIn = ref('0.00')
const totalOut = ref('0.00')
const totalEarn = ref('0.00')

const allActions = ref<Action[]>([])
const allAccounts = ref<Account[]>([])
const allTypes = ref<any[]>([])

// 编辑器状态
const showEditor = ref(false)
const editFlowId = ref<number | null>(null)

// 抽屉状态
const showDrawer = ref(false)

// 返回顶部
const listWrapperRef = ref<HTMLElement | null>(null)
const showBackTop = ref(false)

function onListScroll(e: Event) {
  const target = e.target as HTMLElement
  showBackTop.value = target.scrollTop > 300
}

function scrollToTop() {
  listWrapperRef.value?.scrollTo({ top: 0, behavior: 'smooth' })
}

// ==================== 选项 ====================
const fastOptions = [
  { label: '当月', value: 0 },
  { label: '上月', value: 1 },
  { label: '全年', value: 2 },
  { label: '上年', value: 3 },
]

const handleOptions = [
  { label: '全部', value: 3 },
  { label: '收入', value: 0 },
  { label: '支出', value: 1 },
  { label: '转账', value: 2 },
]

// ==================== 计算属性 ====================
// 按日期分组的流水
const groupedFlows = computed(() => {
  const groups: { date: string; dateLabel: string; flows: Flow[] }[] = []
  let currentDate = ''

  flows.value.forEach(flow => {
    if (flow.fdate !== currentDate) {
      currentDate = flow.fdate
      const parts = flow.fdate.split('-')
      const dateLabel = `${parseInt(parts[1])}月${parseInt(parts[2])}日`
      groups.push({ date: currentDate, dateLabel, flows: [] })
    }
    groups[groups.length - 1].flows.push(flow)
  })

  return groups
})

// 是否有激活的筛选条件
const hasActiveFilters = computed(() => {
  return accountId.value !== -1 ||
    handleType.value !== 3 ||
    chooseActions.value.length > 0 ||
    chooseTypes.value.length > 0 ||
    collectOnly.value
})

// 检查一级分类是否全选
function isParentAllSelected(parentType: any): boolean {
  if (!parentType.childrenTypes?.length) {
    return chooseTypes.value.includes(parentType.id)
  }
  return parentType.childrenTypes.every((child: any) => chooseTypes.value.includes(child.id))
}

// 检查一级分类是否部分选中
function isParentPartialSelected(parentType: any): boolean {
  if (!parentType.childrenTypes?.length) return false
  const selectedCount = parentType.childrenTypes.filter((child: any) => chooseTypes.value.includes(child.id)).length
  return selectedCount > 0 && selectedCount < parentType.childrenTypes.length
}

// 切换一级分类（全选/取消全选所有子分类）
function toggleParentType(parentType: any, checked: boolean) {
  if (!parentType.childrenTypes?.length) {
    // 没有子分类时，直接选中/取消父分类本身
    toggleType(parentType.id)
    return
  }

  if (checked) {
    // 全选：添加所有子分类
    parentType.childrenTypes.forEach((child: any) => {
      if (!chooseTypes.value.includes(child.id)) {
        chooseTypes.value.push(child.id)
      }
    })
  } else {
    // 取消全选：移除所有子分类
    parentType.childrenTypes.forEach((child: any) => {
      const idx = chooseTypes.value.indexOf(child.id)
      if (idx > -1) {
        chooseTypes.value.splice(idx, 1)
      }
    })
  }
}

// ==================== 方法 ====================
function formatDate(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function onFastChoose(value: number) {
  fastChoose.value = value
  const now = new Date()

  switch (value) {
    case 0: // 当月
      startDate.value = formatDate(new Date(now.getFullYear(), now.getMonth(), 1))
      endDate.value = ''
      singleMonth.value = true
      break
    case 1: // 上月
      startDate.value = formatDate(new Date(now.getFullYear(), now.getMonth() - 1, 1))
      endDate.value = ''
      singleMonth.value = true
      break
    case 2: // 全年
      startDate.value = formatDate(new Date(now.getFullYear(), 0, 1))
      endDate.value = formatDate(now)
      singleMonth.value = false
      break
    case 3: // 上年
      startDate.value = formatDate(new Date(now.getFullYear() - 1, 0, 1))
      endDate.value = formatDate(new Date(now.getFullYear() - 1, 11, 31))
      singleMonth.value = false
      break
  }

  fetchFlows()
}

async function fetchFlows() {
  loading.value = true

  try {
    const params: ScreenFlowParams = {
      startDate: startDate.value,
      endDate: endDate.value || undefined,
      singleMonth: singleMonth.value,
      accountId: accountId.value === -1 ? undefined : accountId.value,
      chooseHandle: handleType.value,
      collect: collectOnly.value || undefined,
      actions: chooseActions.value.length > 0 ? chooseActions.value : undefined,
      types: chooseTypes.value.length > 0 ? chooseTypes.value : undefined,
      note: searchNote.value || undefined,
    }

    const res = await screenApi.getFlowByScreen(params)
    const data = res.data.data

    flows.value = data.flows || []
    totalIn.value = data.totalIn || '0.00'
    totalOut.value = data.totalOut || '0.00'
    totalEarn.value = data.totalEarn || '0.00'
  } catch (err) {
    console.error('筛选失败:', err)
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function fetchActions() {
  try {
    const res = await actionApi.getAll()
    allActions.value = res.data.data || []
  } catch (err) {
    console.error(err)
  }
}

async function fetchAccounts() {
  try {
    const res = await accountApi.getAll()
    allAccounts.value = [{ id: -1, name: '全部账户', money: '0' } as Account, ...(res.data.data || [])]
  } catch (err) {
    console.error(err)
  }
}

async function fetchTypes() {
  try {
    const res = await typeApi.getAllNoLimit()
    allTypes.value = res.data.data || []
  } catch (err) {
    console.error(err)
  }
}

function onSearch() {
  fetchFlows()
}

function applyFilter() {
  showDrawer.value = false
  fetchFlows()
}

// 清除单个筛选条件并刷新
function clearFilterAndRefresh(type: 'account' | 'handle' | 'actions' | 'types' | 'collect') {
  switch (type) {
    case 'account':
      accountId.value = -1
      break
    case 'handle':
      handleType.value = 3
      break
    case 'actions':
      chooseActions.value = []
      break
    case 'types':
      chooseTypes.value = []
      break
    case 'collect':
      collectOnly.value = false
      break
  }
  fetchFlows()
}

function toggleAction(actionId: number) {
  const idx = chooseActions.value.indexOf(actionId)
  if (idx > -1) {
    chooseActions.value.splice(idx, 1)
  } else {
    chooseActions.value.push(actionId)
  }
}

function toggleType(typeId: number) {
  const idx = chooseTypes.value.indexOf(typeId)
  if (idx > -1) {
    chooseTypes.value.splice(idx, 1)
  } else {
    chooseTypes.value.push(typeId)
  }
}

// 根据 handle 获取样式类
function getHandleClass(handle: number | undefined): string {
  if (handle === 0) return 'income'
  if (handle === 1) return 'expense'
  if (handle === 2) return 'transfer'
  return ''
}

function resetFilter() {
  accountId.value = -1
  handleType.value = 3
  collectOnly.value = false
  chooseActions.value = []
  chooseTypes.value = []
  startDate.value = ''
  endDate.value = ''
  searchNote.value = ''
  fastChoose.value = 0
  onFastChoose(0)
}

// 流水操作
function toFlowDetail(flow: Flow) {
  editFlowId.value = flow.id
  showEditor.value = true
}

function onEditorSuccess() {
  fetchFlows()
}

async function onCollect(flow: Flow) {
  try {
    await flowApi.toggleCollect(flow.id, !flow.collect)
    ElMessage.success(flow.collect ? '已取消收藏' : '已收藏')
    fetchFlows()
  } catch (err) {
    ElMessage.error('操作失败')
  }
}

function onDelete(flow: Flow) {
  ElMessageBox.confirm(
    `确定删除 ¥${flow.money} 的「${flow.tname}」记录吗？`,
    '确认删除',
    {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await flowApi.delete(flow.id)
      ElMessage.success('已删除')
      fetchFlows()
    } catch (err) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

// 生成 Excel
function onMakeExcel() {
  ElMessageBox.prompt('请输入Excel标题', '生成Excel', {
    confirmButtonText: '生成',
    cancelButtonText: '取消',
    inputPlaceholder: '请输入标题',
  }).then(async ({ value }) => {
    if (!value?.trim()) {
      ElMessage.warning('请输入标题')
      return
    }

    const loadingMsg = ElMessage({
      message: '生成中...',
      type: 'info',
      duration: 0,
    })

    try {
      const params: ScreenFlowParams = {
        startDate: startDate.value,
        endDate: endDate.value || undefined,
        singleMonth: singleMonth.value,
        accountId: accountId.value === -1 ? undefined : accountId.value,
        chooseHandle: handleType.value,
        collect: collectOnly.value || undefined,
        actions: chooseActions.value.length > 0 ? chooseActions.value : undefined,
        types: chooseTypes.value.length > 0 ? chooseTypes.value : undefined,
        note: searchNote.value || undefined,
      }

      const res = await screenApi.makeExcel(value, params)
      loadingMsg.close()

      const result = res.data.data
      if (result.success) {
        ElMessage.success(result.log)
      } else {
        ElMessage.error(result.log)
      }
    } catch (err) {
      loadingMsg.close()
      ElMessage.error('生成失败')
    }
  }).catch(() => {})
}

// 应用外部传入的筛选参数
function applyExternalParams(params: ScreenParams) {
  // 先重置所有筛选条件到默认值（避免残留）
  startDate.value = ''
  endDate.value = ''
  singleMonth.value = false  // 默认不限月份，避免没有日期时报错
  accountId.value = -1
  handleType.value = 3
  collectOnly.value = false
  chooseActions.value = []
  chooseTypes.value = []
  searchNote.value = ''
  fastChoose.value = -1

  // 再设置新的参数
  if (params.startDate) {
    startDate.value = params.startDate
  }
  if (params.endDate) {
    endDate.value = params.endDate
  }
  if (params.singleMonth !== undefined) {
    singleMonth.value = params.singleMonth
  }
  if (params.chooseHandle !== undefined) {
    handleType.value = Number(params.chooseHandle)
  }
  if (params.actions && params.actions.length > 0) {
    chooseActions.value = params.actions.map(a => Number(a))
  }
  if (params.types && params.types.length > 0) {
    chooseTypes.value = params.types.map(t => Number(t))
  }
  if (params.accountId !== undefined) {
    accountId.value = Number(params.accountId)
  }
  if (params.collect !== undefined) {
    collectOnly.value = params.collect === true || params.collect === 'true'
  }
  if (params.note) {
    searchNote.value = params.note
  }
}

// ==================== 生命周期 ====================

// 监听路由变化（处理已在筛选页时从 AI 再次跳转的情况）
watch(() => route.fullPath, () => {
  // 只在有外部参数时处理（避免其他路由变化触发）
  if (hasScreenParams()) {
    const externalParams = consumeScreenParams()
    if (externalParams) {
      applyExternalParams(externalParams)
      fetchFlows()
    }
  }
})

onMounted(() => {
  // 检查是否有外部传入的筛选参数（如从 AI 工具跳转）
  const externalParams = consumeScreenParams()

  if (externalParams) {
    // 应用外部参数
    applyExternalParams(externalParams)
  } else {
    // 默认初始化日期为当月
    const now = new Date()
    startDate.value = formatDate(new Date(now.getFullYear(), now.getMonth(), 1))
  }

  fetchActions()
  fetchAccounts()
  fetchTypes()
  fetchFlows()
})
</script>

<template>
  <div class="screen-page" v-loading="loading">
    <div class="screen-layout">
      <!-- 左侧：账单列表 -->
      <div class="left-column">
        <div class="list-panel">
          <!-- 列表头 -->
          <div class="list-header">
            <span class="col-date">日期</span>
            <span class="col-type">分类</span>
            <span class="col-account">账户</span>
            <span class="col-remark">备注</span>
            <span class="col-money">金额</span>
            <span class="col-actions">操作</span>
          </div>

          <!-- 流水列表 -->
          <div class="flow-list-wrapper" ref="listWrapperRef" @scroll="onListScroll">
            <div class="flow-list" v-if="groupedFlows.length">
              <div class="flow-group" v-for="group in groupedFlows" :key="group.date">
                <div class="group-header">{{ group.dateLabel }}</div>
                <div class="group-items">
                  <FlowItem
                    v-for="flow in group.flows"
                    :key="flow.id"
                    :flow="flow"
                    @click="toFlowDetail"
                    @collect="onCollect"
                    @delete="onDelete"
                  />
                </div>
              </div>
            </div>

            <el-empty v-else description="暂无筛选结果" />

            <!-- 返回顶部 -->
            <Transition name="fade">
              <div v-show="showBackTop" class="back-top" @click="scrollToTop">
                <el-icon><Top /></el-icon>
              </div>
            </Transition>
          </div>
        </div>
      </div>

      <!-- 右侧 -->
      <div class="right-column">
        <!-- 结余面板 -->
        <div class="stats-card">
          <div class="stat-row">
            <span class="stat-label">收入</span>
            <span class="stat-value income">+{{ totalIn }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">支出</span>
            <span class="stat-value expense">-{{ totalOut }}</span>
          </div>
          <el-divider />
          <div class="stat-row">
            <span class="stat-label">结余</span>
            <span class="stat-value balance">{{ totalEarn }}</span>
          </div>
        </div>

        <!-- 快速筛选 -->
        <div class="quick-card">
          <el-input
            v-model="searchNote"
            placeholder="搜索备注关键词"
            clearable
            @keyup.enter="onSearch"
            @clear="onSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>

          <div class="fast-options">
            <span
              v-for="opt in fastOptions"
              :key="opt.value"
              class="fast-item"
              :class="{ active: fastChoose === opt.value }"
              @click="onFastChoose(opt.value)"
            >
              {{ opt.label }}
            </span>
          </div>

          <div class="quick-actions">
            <div class="action-btn filter-btn" @click="showDrawer = true">
              <el-icon><Filter /></el-icon>
              <span>更多筛选</span>
            </div>
            <div class="action-btn excel-btn" @click="onMakeExcel">
              <el-icon><Download /></el-icon>
              <span>导出</span>
            </div>
          </div>

          <div class="filter-summary" v-if="hasActiveFilters">
            <span class="summary-label">已筛选：</span>
            <span class="summary-tags">
              <el-tag v-if="accountId !== -1" size="small" closable @close="clearFilterAndRefresh('account')">
                {{ allAccounts.find(a => a.id === accountId)?.name }}
              </el-tag>
              <el-tag v-if="handleType !== 3" size="small" closable @close="clearFilterAndRefresh('handle')">
                {{ handleOptions.find(h => h.value === handleType)?.label }}
              </el-tag>
              <el-tag v-if="chooseActions.length" size="small" closable @close="clearFilterAndRefresh('actions')">
                {{ chooseActions.length }}个类型
              </el-tag>
              <el-tag v-if="chooseTypes.length" size="small" closable @close="clearFilterAndRefresh('types')">
                {{ chooseTypes.length }}个分类
              </el-tag>
              <el-tag v-if="collectOnly" size="small" closable @close="clearFilterAndRefresh('collect')">
                仅收藏
              </el-tag>
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 筛选抽屉 -->
    <el-drawer
      v-model="showDrawer"
      direction="rtl"
      size="420px"
      :with-header="false"
      class="screen-filter-drawer"
    >
      <div class="drawer-header">
        <span class="drawer-title">筛选条件</span>
        <el-button text circle @click="showDrawer = false">
          <el-icon :size="18"><Close /></el-icon>
        </el-button>
      </div>
      <div class="drawer-body">
        <!-- 日期范围卡片 -->
        <div class="filter-card">
          <div class="card-title">日期范围</div>
          <div class="date-range">
            <div class="date-row">
              <span class="date-label">开始</span>
              <el-date-picker
                v-model="startDate"
                type="date"
                placeholder="开始日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                @change="fastChoose = -1"
              />
            </div>
            <div class="date-row">
              <span class="date-label">结束</span>
              <el-date-picker
                v-model="endDate"
                type="date"
                placeholder="结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                @change="fastChoose = -1"
              />
            </div>
          </div>
          <div class="switch-row">
            <div class="switch-info">
              <span class="switch-label">整月模式</span>
              <span class="switch-hint">仅查看开始月份的数据</span>
            </div>
            <el-switch v-model="singleMonth" />
          </div>
        </div>

        <!-- 筛选条件卡片 -->
        <div class="filter-card">
          <div class="card-title">筛选条件</div>

          <!-- 账户 -->
          <div class="filter-item">
            <label class="item-label">账户</label>
            <div class="filter-tags">
              <span
                v-for="account in allAccounts"
                :key="account.id"
                class="tag-item"
                :class="{ active: accountId === account.id }"
                @click="accountId = account.id"
              >
                {{ account.name }}
              </span>
            </div>
          </div>

          <!-- 资金流向 -->
          <div class="filter-item">
            <label class="item-label">资金流向</label>
            <div class="filter-tags">
              <span
                v-for="opt in handleOptions"
                :key="opt.value"
                class="tag-item"
                :class="{ active: handleType === opt.value }"
                @click="handleType = opt.value"
              >
                {{ opt.label }}
              </span>
            </div>
          </div>

          <!-- 收支类型 -->
          <div class="filter-item">
            <label class="item-label">收支类型</label>
            <div class="filter-tags">
              <span
                v-for="action in allActions"
                :key="action.id"
                class="tag-item"
                :class="[
                  getHandleClass(action.handle),
                  { active: chooseActions.includes(action.id) }
                ]"
                @click="toggleAction(action.id)"
              >
                {{ action.hname }}
              </span>
            </div>
          </div>

          <!-- 只看收藏 -->
          <div class="switch-row last">
            <div class="switch-info">
              <span class="switch-label">只看收藏</span>
              <span class="switch-hint">仅显示已收藏的账单</span>
            </div>
            <el-switch v-model="collectOnly" />
          </div>
        </div>

        <!-- 分类选择卡片 -->
        <div class="filter-card">
          <div class="card-title">
            <span>分类筛选</span>
            <span v-if="chooseTypes.length > 0" class="selected-count">已选 {{ chooseTypes.length }}</span>
          </div>
          <div class="type-list">
            <div
              v-for="parentType in allTypes"
              :key="parentType.id"
              class="type-group"
            >
              <div class="type-group-header">
                <el-checkbox
                  :model-value="isParentAllSelected(parentType)"
                  :indeterminate="isParentPartialSelected(parentType)"
                  @change="(val: boolean) => toggleParentType(parentType, val)"
                >
                  {{ parentType.tname }}
                </el-checkbox>
              </div>
              <div class="type-group-children" v-if="parentType.childrenTypes?.length">
                <el-checkbox
                  v-for="child in parentType.childrenTypes"
                  :key="child.id"
                  :model-value="chooseTypes.includes(child.id)"
                  @change="toggleType(child.id)"
                  class="type-checkbox"
                >
                  {{ child.tname }}
                </el-checkbox>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="drawer-footer">
        <el-button @click="resetFilter">重置条件</el-button>
        <el-button type="primary" @click="applyFilter">应用筛选</el-button>
      </div>
    </el-drawer>

    <!-- 账单编辑器 -->
    <FlowEditor
      v-model:visible="showEditor"
      :flow-id="editFlowId"
      @success="onEditorSuccess"
    />
  </div>
</template>

<style scoped>
.screen-page {
  position: relative;
  height: calc(100vh - 140px);
}

/* 主布局 */
.screen-layout {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 20px;
  height: 100%;
}

/* 左侧列 */
.left-column {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

/* 账单列表面板 */
.list-panel {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

/* 列表头 */
.list-header {
  display: grid;
  grid-template-columns: 60px 220px 200px 1fr 120px 80px;
  gap: 16px;
  padding: 12px 16px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-tertiary);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.col-money,
.col-actions {
  text-align: right;
}

/* 流水列表容器 */
.flow-list-wrapper {
  flex: 1;
  overflow-y: auto;
  margin-top: 8px;
  position: relative;
}

/* 返回顶部 */
.back-top {
  position: sticky;
  bottom: 16px;
  left: 100%;
  width: 40px;
  height: 40px;
  margin-left: auto;
  margin-right: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-transfer);
  color: #fff;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(116, 192, 252, 0.4);
  transition: all 0.2s ease;
  z-index: 10;
}

.back-top:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(116, 192, 252, 0.5);
}

.back-top:active {
  transform: translateY(0);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.flow-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.flow-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.group-header {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-tertiary);
  padding: 12px 16px 8px;
  background: var(--color-bg-page);
  border-radius: 8px 8px 0 0;
  margin-top: 8px;
}

.flow-group:first-child .group-header {
  margin-top: 0;
}

.group-items {
  display: flex;
  flex-direction: column;
  background: var(--color-bg-card);
  border-radius: 0 0 8px 8px;
}

/* 右侧列 */
.right-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
  min-height: 0;
}

/* 结余面板 */
.stats-card {
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.stat-label {
  font-size: 14px;
  color: var(--color-text-tertiary);
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
}

.stat-value.income {
  color: var(--color-income);
}

.stat-value.expense {
  color: var(--color-expense);
}

.stat-value.balance {
  color: var(--color-transfer);
}

.stats-card .el-divider {
  margin: 8px 0;
}

/* 快速筛选卡片 */
.quick-card {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.fast-options {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.fast-item {
  padding: 5px 10px;
  background: var(--color-bg-page);
  border-radius: 12px;
  font-size: 12px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.fast-item:hover {
  background: var(--color-bg-elevated);
}

.fast-item.active {
  background: var(--color-transfer);
  color: #fff;
}

.quick-actions {
  display: flex;
  gap: 10px;
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.25s ease;
}

.filter-btn {
  background: linear-gradient(135deg, var(--color-transfer) 0%, #5ba3e8 100%);
  color: #fff;
  box-shadow: 0 4px 12px rgba(116, 192, 252, 0.35);
}

.filter-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(116, 192, 252, 0.45);
}

.filter-btn:active {
  transform: translateY(0);
}

.excel-btn {
  background: rgba(255, 255, 255, 0.7);
  color: var(--color-text-secondary);
  border: 1.5px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.excel-btn:hover {
  background: rgba(255, 255, 255, 0.95);
  color: var(--color-text-primary);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.excel-btn:active {
  transform: translateY(0);
}

.action-btn .el-icon {
  font-size: 16px;
}

.filter-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  padding-top: 10px;
  border-top: 1px solid var(--color-border);
}

.summary-label {
  font-size: 12px;
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

.summary-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.summary-tags .el-tag {
  border-radius: 10px;
}

/* ==================== 抽屉样式 ==================== */

/* 抽屉头部 */
.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
  background: linear-gradient(180deg, var(--color-bg-page) 0%, var(--color-bg-card) 100%);
}

.drawer-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

/* 抽屉内容 */
.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: var(--color-bg-page);
}

/* 抽屉底部 */
.drawer-footer {
  display: flex;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid var(--color-border);
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(12px);
}

.drawer-footer .el-button {
  flex: 1;
  height: 42px;
  border-radius: 10px;
  font-weight: 500;
}

/* 筛选卡片 */
.filter-card {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
  border: 1px solid rgba(0, 0, 0, 0.04);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.filter-card:last-child {
  margin-bottom: 0;
}

.card-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border-light);
}

.selected-count {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-transfer);
  background: var(--color-transfer-bg);
  padding: 2px 8px;
  border-radius: 10px;
}

/* 筛选项 */
.filter-item {
  margin-bottom: 16px;
}

.filter-item:last-child {
  margin-bottom: 0;
}

.item-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin-bottom: 10px;
}

/* 开关行 */
.switch-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 12px;
  margin-top: 12px;
}

.switch-row.last {
  margin-top: 16px;
}

.switch-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.switch-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.switch-hint {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

/* 日期范围 */
.date-range {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.date-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.date-row :deep(.el-date-editor) {
  flex: 1;
}

.date-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-tertiary);
  width: 36px;
  flex-shrink: 0;
}

/* 标签样式 */
.filter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-item {
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1.5px solid rgba(0, 0, 0, 0.06);
}

.tag-item:hover {
  background: rgba(255, 255, 255, 0.9);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.tag-item.active {
  background: var(--color-transfer);
  color: #fff;
  border-color: var(--color-transfer);
  box-shadow: 0 2px 8px rgba(116, 192, 252, 0.3);
}

/* 收支类型颜色 */
.tag-item.income {
  color: var(--color-income);
  background: var(--color-income-bg);
}

.tag-item.income.active {
  background: var(--color-income);
  color: #fff;
}

.tag-item.expense {
  color: var(--color-expense);
  background: var(--color-expense-bg);
}

.tag-item.expense.active {
  background: var(--color-expense);
  color: #fff;
}

.tag-item.transfer {
  color: var(--color-transfer);
  background: var(--color-transfer-bg);
}

.tag-item.transfer.active {
  background: var(--color-transfer);
  color: #fff;
}

/* 分类列表 */
.type-list {
  max-height: 280px;
  overflow-y: auto;
  border-radius: 8px;
  background: var(--color-bg-page);
  padding: 8px;
}

.type-group {
  margin-bottom: 12px;
}

.type-group:last-child {
  margin-bottom: 0;
}

.type-group-header {
  padding: 8px 4px;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: 8px;
}

.type-group-header :deep(.el-checkbox__label) {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.type-group-children {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  padding-left: 24px;
}

.type-checkbox {
  margin-right: 0 !important;
}

.type-checkbox :deep(.el-checkbox__label) {
  font-size: 13px;
  color: var(--color-text-secondary);
}

</style>

<!-- 暗色模式 -->
<style>
html.dark .screen-page .list-panel,
html.dark .screen-page .stats-card,
html.dark .screen-page .quick-card {
  background: rgba(40, 40, 40, 0.6);
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .screen-page .group-header {
  background: rgba(30, 30, 30, 0.6);
}

html.dark .screen-page .group-items {
  background: rgba(40, 40, 40, 0.4);
}

html.dark .screen-page .fast-item {
  background: rgba(50, 50, 50, 0.6);
}

html.dark .screen-page .excel-btn {
  background: rgba(50, 50, 50, 0.6);
  border-color: rgba(255, 255, 255, 0.1);
  color: var(--color-text-secondary);
}

html.dark .screen-page .excel-btn:hover {
  background: rgba(60, 60, 60, 0.8);
  color: var(--color-text-primary);
}

html.dark .screen-page .type-list {
  background: rgba(30, 30, 30, 0.6);
}

html.dark .screen-page .type-group-header {
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .screen-page .filter-summary {
  border-color: rgba(255, 255, 255, 0.1);
}

/* ==================== 抽屉暗色模式 ==================== */
html.dark .screen-filter-drawer .el-drawer__body {
  background: var(--color-bg-card);
}

html.dark .screen-filter-drawer .drawer-header {
  background: linear-gradient(180deg, var(--color-bg-card) 0%, var(--color-bg-page) 100%);
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .screen-filter-drawer .drawer-body {
  background: var(--color-bg-page);
}

html.dark .screen-filter-drawer .drawer-footer {
  background: rgba(30, 30, 30, 0.9);
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .screen-filter-drawer .filter-card {
  background: rgba(40, 40, 40, 0.6);
  border-color: rgba(255, 255, 255, 0.06);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
}

html.dark .screen-filter-drawer .card-title {
  border-color: rgba(255, 255, 255, 0.1);
}

html.dark .screen-filter-drawer .switch-row {
  background: rgba(50, 50, 50, 0.4);
}

html.dark .screen-filter-drawer .tag-item {
  background: rgba(50, 50, 50, 0.6);
  border-color: rgba(255, 255, 255, 0.08);
}

html.dark .screen-filter-drawer .tag-item:hover {
  background: rgba(60, 60, 60, 0.8);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

html.dark .screen-filter-drawer .type-list {
  background: rgba(30, 30, 30, 0.6);
}

html.dark .screen-filter-drawer .type-group-header {
  border-color: rgba(255, 255, 255, 0.1);
}
</style>

<!-- 抽屉全局样式 -->
<style>
.screen-filter-drawer .el-drawer__body {
  padding: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
</style>
