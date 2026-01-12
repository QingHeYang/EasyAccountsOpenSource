<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Close, ArrowRight, ArrowDown, PriceTag, Check } from '@element-plus/icons-vue'
import { templateApi, type Template } from '@shared/api/template'
import { tagApi, type Tag } from '@shared/api/tag'
import { actionApi, type Action, ActionHandle, ExemptMode } from '@shared/api/action'
import { accountApi, type Account, AccountType } from '@shared/api/account'
import { typeApi, type TypeWithChildren } from '@shared/api/type'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()

// 抽屉状态
const drawerVisible = ref(false)

// 模板数据
const templateLoading = ref(false)
const templates = ref<Template[]>([])
const tags = ref<Tag[]>([])
const selectedTagFilter = ref<Tag | null>(null)
const expandedTemplateIds = ref<number[]>([])

// 基础数据
const actions = ref<Action[]>([])
const accounts = ref<Account[]>([])

// 第二层面板：模板表单
const templatePanelVisible = ref(false)
const editingTemplate = ref<Template | null>(null)
const templateForm = ref({
  name: '',
  money: '',
  dateType: '' as string,
  actionId: undefined as number | undefined,
  selectedAction: null as Action | null,
  accountId: undefined as number | undefined,
  selectedAccount: null as Account | null,
  accountToId: undefined as number | undefined,
  selectedAccountTo: null as Account | null,
  typeId: undefined as number | undefined,
  selectedType: null as { id: number; tname: string } | null,
  tagId: undefined as number | undefined,
  selectedTag: null as Tag | null,
})
const templateTypes = ref<TypeWithChildren[]>([])

// 模板表单选择器
const showTemplateActionPicker = ref(false)
const showTemplateAccountPicker = ref(false)
const templateAccountPickerType = ref<1 | 2>(1)
const showTemplateTypePicker = ref(false)
const showTemplateTagPicker = ref(false)

// 第三层面板：标签管理
const tagPanelVisible = ref(false)
const editingTag = ref<Tag | null>(null)
const tagForm = ref({
  name: '',
  color: '',
})

// 预设颜色
const colorOptions = [
  '#FFEA00', '#ECD540', '#B8860B',
  '#90EE90', '#3CB371', '#008000', '#006400', '#013220',
  '#FFCCB6', '#FFB6C1', '#FF1493',
  '#FFA500', '#FF4500',
  '#D2B48C', '#8B4513',
  '#ADD8E6', '#48D1CC', '#120A8F', '#000080',
  '#B57EDC', '#800080', '#4B0082',
  '#FFA07A', '#FF0000', '#8B0000', '#800020', '#600000',
  '#A9A9A9', '#607B8B', '#000000',
]

// 是否为转账类型
const isTemplateTransfer = computed(() => templateForm.value.selectedAction?.handle === 2)

// 动态抽屉宽度
const drawerSize = computed(() => {
  let width = 520 // 基础宽度（模板列表）
  if (templatePanelVisible.value) width += 420 // 模板编辑面板
  if (tagPanelVisible.value) width += 340 // 标签管理面板
  return `${width}px`
})

// 监听外部 visible 变化
watch(() => props.visible, (val) => {
  drawerVisible.value = val
  if (val) {
    loadTemplates()
    loadTags()
  }
})

// 监听内部 drawer 变化同步到外部
watch(drawerVisible, (val) => {
  emit('update:visible', val)
  if (!val) {
    templatePanelVisible.value = false
    tagPanelVisible.value = false
    resetTemplateForm()
    resetTagForm()
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

// 获取不计入显示文本
function getExemptText(action: Action): string {
  if (!action.exempt) return ''
  if (action.handle !== ActionHandle.TRANSFER) return '不计入'
  switch (action.exemptMode) {
    case ExemptMode.FROM_EXEMPT: return '转出不计入'
    case ExemptMode.TO_EXEMPT: return '转入不计入'
    case ExemptMode.BOTH_EXEMPT: return '两边不计入'
    default: return '不计入'
  }
}

// 判断账户是否应该被禁用（根据已选收支类型）
function isAccountDisabled(account: Account, panelType: 1 | 2): boolean {
  if (account.accountType !== AccountType.LIABILITY) return false
  if (!templateForm.value.selectedAction?.exempt) return false
  if (templateForm.value.selectedAction.handle !== ActionHandle.TRANSFER) return true

  const mode = templateForm.value.selectedAction.exemptMode ?? ExemptMode.NONE
  if (panelType === 1) {
    return mode === ExemptMode.FROM_EXEMPT || mode === ExemptMode.BOTH_EXEMPT
  } else {
    return mode === ExemptMode.TO_EXEMPT || mode === ExemptMode.BOTH_EXEMPT
  }
}

// 获取账户禁用原因
function getAccountDisabledReason(account: Account, panelType: 1 | 2): string {
  if (!isAccountDisabled(account, panelType)) return ''
  return '负债账户不支持此收支类型'
}

// ============ 模板相关 ============
async function loadTemplates() {
  templateLoading.value = true
  try {
    const res = selectedTagFilter.value
      ? await templateApi.getByTagId(selectedTagFilter.value.id)
      : await templateApi.getAll()
    templates.value = res.data.data || []
  } catch (err) {
    console.error('获取模板列表失败', err)
    ElMessage.error('获取模板列表失败')
  } finally {
    templateLoading.value = false
  }
}

async function loadTags() {
  try {
    const res = await tagApi.getAll()
    tags.value = res.data.data || []
  } catch (err) {
    console.error('获取标签列表失败', err)
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

async function loadAccounts() {
  try {
    const res = await accountApi.getAll()
    accounts.value = res.data.data
  } catch (err) {
    console.error('获取账户列表失败', err)
  }
}

async function loadTemplateTypes(actionId: number) {
  try {
    const res = await typeApi.getByActionId(actionId)
    templateTypes.value = res.data.data || []
  } catch (err) {
    console.error('获取分类列表失败', err)
  }
}

function onSelectTagFilter(tag: Tag) {
  selectedTagFilter.value = tag
  loadTemplates()
}

function onClearTagFilter() {
  selectedTagFilter.value = null
  loadTemplates()
}

function toggleTemplateExpand(id: number) {
  const idx = expandedTemplateIds.value.indexOf(id)
  if (idx >= 0) {
    expandedTemplateIds.value.splice(idx, 1)
  } else {
    expandedTemplateIds.value.push(id)
  }
}

function hasTemplateDetails(item: Template): boolean {
  return !!(
    item.account?.name ||
    item.accountTo?.name ||
    item.type?.tname ||
    (item.dateType !== undefined && item.dateType !== null)
  )
}

function onAddTemplate() {
  editingTemplate.value = null
  resetTemplateForm()
  templatePanelVisible.value = true
  loadActions()
  loadAccounts()
  loadTags()
}

async function onEditTemplate(template: Template) {
  editingTemplate.value = template
  templateForm.value = {
    name: template.name,
    money: template.money || '',
    dateType: template.dateType !== undefined && template.dateType !== null ? String(template.dateType) : '',
    actionId: template.actionId,
    selectedAction: template.action || null,
    accountId: template.accountId,
    selectedAccount: template.account || null,
    accountToId: template.accountToId,
    selectedAccountTo: template.accountTo || null,
    typeId: template.typeId,
    selectedType: template.type ? { id: template.type.id, tname: template.type.tname } : null,
    tagId: template.tagId,
    selectedTag: template.tag || null,
  }

  loadActions()
  loadAccounts()
  loadTags()

  if (template.actionId) {
    loadTemplateTypes(template.actionId)
  }

  templatePanelVisible.value = true
}

function closeTemplatePanel() {
  templatePanelVisible.value = false
  resetTemplateForm()
}

function resetTemplateForm() {
  editingTemplate.value = null
  templateForm.value = {
    name: '',
    money: '',
    dateType: '',
    actionId: undefined,
    selectedAction: null,
    accountId: undefined,
    selectedAccount: null,
    accountToId: undefined,
    selectedAccountTo: null,
    typeId: undefined,
    selectedType: null,
    tagId: undefined,
    selectedTag: null,
  }
  templateTypes.value = []
}

// 模板表单选择
function onSelectTemplateAction(action: Action) {
  if (action.id === templateForm.value.actionId) {
    showTemplateActionPicker.value = false
    return
  }
  templateForm.value.actionId = action.id
  templateForm.value.selectedAction = action
  templateForm.value.accountToId = undefined
  templateForm.value.selectedAccountTo = null
  templateForm.value.typeId = undefined
  templateForm.value.selectedType = null
  showTemplateActionPicker.value = false
  loadTemplateTypes(action.id)
}

function openTemplateAccountPicker(type: 1 | 2) {
  templateAccountPickerType.value = type
  showTemplateAccountPicker.value = true
}

function onSelectTemplateAccount(account: Account) {
  if (templateAccountPickerType.value === 1) {
    templateForm.value.accountId = account.id
    templateForm.value.selectedAccount = account
  } else {
    templateForm.value.accountToId = account.id
    templateForm.value.selectedAccountTo = account
  }
  showTemplateAccountPicker.value = false
}

function openTemplateTypePicker() {
  if (!templateForm.value.actionId) {
    ElMessage.warning('请先选择收支')
    return
  }
  showTemplateTypePicker.value = true
}

function onSelectTemplateType(type: TypeWithChildren, parent?: TypeWithChildren) {
  // 如果是一级分类且有子分类，则不能选择
  if (!parent && type.childrenTypes?.length) {
    return
  }
  const tname = parent ? `${parent.tname}/${type.tname}` : type.tname
  templateForm.value.typeId = type.id
  templateForm.value.selectedType = { id: type.id, tname }
  showTemplateTypePicker.value = false
}

function onSelectTemplateTag(tag: Tag | null) {
  templateForm.value.tagId = tag?.id
  templateForm.value.selectedTag = tag
  showTemplateTagPicker.value = false
}

async function onSubmitTemplate() {
  if (!templateForm.value.name.trim()) {
    ElMessage.warning('请输入模板名称')
    return
  }

  try {
    const params = {
      id: editingTemplate.value?.id,
      name: templateForm.value.name.trim(),
      money: templateForm.value.money || undefined,
      actionId: templateForm.value.actionId,
      accountId: templateForm.value.accountId,
      accountToId: templateForm.value.accountToId,
      typeId: templateForm.value.typeId,
      tagId: templateForm.value.tagId,
      dateType: templateForm.value.dateType ? parseInt(templateForm.value.dateType) : undefined,
    }

    if (editingTemplate.value) {
      await templateApi.update(params)
      ElMessage.success('保存成功')
    } else {
      await templateApi.add(params)
      ElMessage.success('添加成功')
    }
    closeTemplatePanel()
    loadTemplates()
  } catch (err) {
    console.error('操作失败', err)
    ElMessage.error('操作失败')
  }
}

async function onDeleteTemplate() {
  if (!editingTemplate.value) return

  try {
    await ElMessageBox.confirm(
      `确定删除模板"${editingTemplate.value.name}"吗？`,
      '删除模板',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        customClass: 'high-zindex-msgbox',
      }
    )

    await templateApi.delete(editingTemplate.value.id)
    ElMessage.success('已删除')
    closeTemplatePanel()
    loadTemplates()
  } catch {
    // 取消
  }
}

// ============ 标签管理 ============
function openTagPanel() {
  tagPanelVisible.value = true
  loadTags()
}

function closeTagPanel() {
  tagPanelVisible.value = false
  resetTagForm()
}

function onAddTag() {
  editingTag.value = null
  tagForm.value = { name: '', color: '' }
}

function onEditTag(tag: Tag) {
  editingTag.value = tag
  tagForm.value = { name: tag.name, color: tag.color }
}

function resetTagForm() {
  editingTag.value = null
  tagForm.value = { name: '', color: '' }
}

function selectTagColor(color: string) {
  tagForm.value.color = color
}

async function onSubmitTag() {
  if (!tagForm.value.name.trim()) {
    ElMessage.warning('请输入标签名称')
    return
  }
  if (!tagForm.value.color) {
    ElMessage.warning('请选择标签颜色')
    return
  }

  try {
    if (editingTag.value) {
      await tagApi.update({
        id: editingTag.value.id,
        name: tagForm.value.name.trim(),
        color: tagForm.value.color,
      })
      ElMessage.success('修改成功')
    } else {
      await tagApi.add({
        name: tagForm.value.name.trim(),
        color: tagForm.value.color,
      })
      ElMessage.success('添加成功')
    }
    resetTagForm()
    loadTags()
  } catch (err) {
    console.error('操作失败', err)
    ElMessage.error('操作失败')
  }
}

async function onDeleteTag() {
  if (!editingTag.value) return

  try {
    await ElMessageBox.confirm(
      '确定删除此标签吗？\n删除后模板中的标签将一并删除',
      '删除标签',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        customClass: 'high-zindex-msgbox',
      }
    )

    await tagApi.delete(editingTag.value.id)
    ElMessage.success('已删除')
    resetTagForm()
    loadTags()
  } catch {
    // 取消
  }
}
</script>

<template>
  <el-drawer
    v-model="drawerVisible"
    title="快记模板"
    direction="rtl"
    :size="drawerSize"
    :z-index="3000"
    class="setting-drawer template-drawer"
  >
    <!-- 抽屉头部 -->
    <template #header>
      <div class="drawer-header">
        <div class="drawer-header-left">
          <span class="drawer-title">快记模板</span>
        </div>
        <div class="drawer-header-right">
          <el-button :icon="PriceTag" @click="openTagPanel">标签管理</el-button>
          <el-button :icon="Plus" type="primary" @click="onAddTemplate">添加模板</el-button>
        </div>
      </div>
    </template>

    <div class="template-panels-container">
      <!-- 第一层：模板列表面板 -->
      <div class="panel template-list-panel">
        <!-- 标签筛选 -->
        <div class="tag-filter-card">
          <div class="filter-left">
            <el-icon><PriceTag /></el-icon>
            <span>按标签筛选</span>
          </div>
          <div class="filter-right">
            <div v-if="selectedTagFilter" class="selected-filter-tag" :style="{ background: selectedTagFilter.color }" @click="onClearTagFilter">
              {{ selectedTagFilter.name }}
              <el-icon :size="12"><Close /></el-icon>
            </div>
            <div v-else-if="tags.length" class="tag-chips">
              <div
                v-for="tag in tags"
                :key="tag.id"
                class="tag-chip"
                :style="{ background: tag.color }"
                @click="onSelectTagFilter(tag)"
              >
                {{ tag.name }}
              </div>
            </div>
            <span v-else class="no-tags-hint">暂无标签</span>
          </div>
        </div>

        <!-- 模板列表 -->
        <div v-loading="templateLoading" class="template-list">
          <div v-for="item in templates" :key="item.id" class="template-card">
            <div class="template-main" @click="onEditTemplate(item)">
              <div class="template-row">
                <div class="template-left">
                  <span class="template-name">{{ item.name }}</span>
                  <span
                    v-if="item.action"
                    class="action-tag"
                    :style="{
                      color: getHandleInfo(item.action.handle).color,
                      background: getHandleInfo(item.action.handle).bg,
                    }"
                  >
                    {{ item.action.hname }}
                  </span>
                </div>
                <div class="template-right">
                  <div
                    v-if="item.tag"
                    class="template-tag"
                    :style="{ background: item.tag.color }"
                  >
                    {{ item.tag.name }}
                  </div>
                  <!-- 展开/收起按钮 -->
                  <el-icon
                    v-if="hasTemplateDetails(item)"
                    class="expand-icon"
                    :class="{ rotated: expandedTemplateIds.includes(item.id) }"
                    @click.stop="toggleTemplateExpand(item.id)"
                  >
                    <ArrowDown />
                  </el-icon>
                </div>
              </div>
              <div v-if="item.money" class="template-money">
                <span class="money-symbol">¥</span>
                <span class="money-value">{{ item.money }}</span>
              </div>
            </div>
                        <Transition name="expand">
              <div v-if="expandedTemplateIds.includes(item.id)" class="template-details">
                <div v-if="item.account" class="detail-row">
                  <span class="detail-label">{{ item.accountTo ? '转出账户' : '账户' }}</span>
                  <span class="detail-value">{{ item.account.name }}</span>
                </div>
                <div v-if="item.accountTo" class="detail-row">
                  <span class="detail-label">转入账户</span>
                  <span class="detail-value transfer">{{ item.accountTo.name }}</span>
                </div>
                <div v-if="item.type" class="detail-row">
                  <span class="detail-label">分类</span>
                  <span class="detail-value">{{ item.type.tname }}</span>
                </div>
                <div v-if="item.dateType !== undefined && item.dateType !== null" class="detail-row">
                  <span class="detail-label">日期</span>
                  <span class="detail-value">{{ item.dateType === 1 ? '补上月' : '记本月' }}</span>
                </div>
              </div>
            </Transition>
          </div>
          <el-empty v-if="!templateLoading && templates.length === 0" description="暂无模板" />
        </div>
      </div>

      <!-- 第二层：模板编辑面板 -->
      <Transition name="slide-panel">
        <div v-if="templatePanelVisible" class="panel template-edit-panel">
          <div class="panel-header">
            <span class="panel-title">{{ editingTemplate ? '编辑模板' : '添加模板' }}</span>
            <el-button :icon="Close" text circle @click="closeTemplatePanel" />
          </div>
          <div class="panel-body">
            <div class="form-section">
              <!-- 模板名称 -->
              <div class="form-item">
                <label class="form-label">模板名称 <span class="required">*</span></label>
                <el-input v-model="templateForm.name" placeholder="请输入模板名称" size="large" />
              </div>

              <!-- 金额 -->
              <div class="form-item">
                <label class="form-label">金额</label>
                <el-input v-model="templateForm.money" placeholder="可留空" size="large">
                  <template #prefix>¥</template>
                </el-input>
              </div>

              <!-- 收支 -->
              <div class="form-item">
                <label class="form-label">收支类型</label>
                <div class="form-select" @click="showTemplateActionPicker = true">
                  <span v-if="templateForm.selectedAction" class="action-display">
                    <span
                      class="action-tag"
                      :style="{
                        color: getHandleInfo(templateForm.selectedAction.handle).color,
                        background: getHandleInfo(templateForm.selectedAction.handle).bg,
                      }"
                    >
                      {{ templateForm.selectedAction.hname }}
                    </span>
                    <span v-if="templateForm.selectedAction.exempt" class="exempt-tag">{{ getExemptText(templateForm.selectedAction) }}</span>
                  </span>
                  <span v-else class="placeholder">点击选择收支</span>
                  <el-icon><ArrowRight /></el-icon>
                </div>
              </div>

              <!-- 账户 -->
              <div class="form-item">
                <label class="form-label">{{ isTemplateTransfer ? '转出账户' : '选择账户' }}</label>
                <div class="form-select" @click="openTemplateAccountPicker(1)">
                  <span :class="{ placeholder: !templateForm.selectedAccount }">
                    {{ templateForm.selectedAccount?.name || '点击选择账户' }}
                  </span>
                  <el-icon><ArrowRight /></el-icon>
                </div>
              </div>

              <!-- 转入账户（转账） -->
              <div v-if="isTemplateTransfer" class="form-item">
                <label class="form-label">转入账户</label>
                <div class="form-select" @click="openTemplateAccountPicker(2)">
                  <span :class="{ placeholder: !templateForm.selectedAccountTo }">
                    {{ templateForm.selectedAccountTo?.name || '点击选择转入账户' }}
                  </span>
                  <el-icon><ArrowRight /></el-icon>
                </div>
              </div>

              <!-- 分类 -->
              <div class="form-item">
                <label class="form-label">账单分类</label>
                <div class="form-select" @click="openTemplateTypePicker">
                  <span :class="{ placeholder: !templateForm.selectedType }">
                    {{ templateForm.selectedType?.tname || '点击选择分类' }}
                  </span>
                  <el-icon><ArrowRight /></el-icon>
                </div>
              </div>

              <!-- 日期类型 -->
              <div class="form-item">
                <label class="form-label">账单日期</label>
                <div class="date-type-group">
                  <div
                    class="date-type-item"
                    :class="{ active: templateForm.dateType === '1' }"
                    @click="templateForm.dateType = '1'"
                  >
                    补上月
                  </div>
                  <div
                    class="date-type-item"
                    :class="{ active: templateForm.dateType === '0' }"
                    @click="templateForm.dateType = '0'"
                  >
                    记本月
                  </div>
                </div>
                <div class="input-hint">补上月 = 上月最后一天，记本月 = 当天</div>
              </div>
            </div>

            <!-- 标签选择 -->
            <div class="form-section">
              <div class="form-item">
                <label class="form-label">绑定标签</label>
                <div class="form-select" @click="showTemplateTagPicker = true">
                  <div
                    v-if="templateForm.selectedTag"
                    class="selected-filter-tag"
                    :style="{ background: templateForm.selectedTag.color }"
                  >
                    {{ templateForm.selectedTag.name }}
                  </div>
                  <span v-else class="placeholder">点击选择标签</span>
                  <el-icon><ArrowRight /></el-icon>
                </div>
              </div>
            </div>
          </div>
          <div class="panel-footer">
            <el-button v-if="editingTemplate" type="danger" plain @click="onDeleteTemplate">删除</el-button>
            <el-button @click="closeTemplatePanel">取消</el-button>
            <el-button type="primary" @click="onSubmitTemplate">
              {{ editingTemplate ? '保存' : '添加' }}
            </el-button>
          </div>
        </div>
      </Transition>

      <!-- 第三层：标签管理面板 -->
      <Transition name="slide-panel">
        <div v-if="tagPanelVisible" class="panel tag-manage-panel">
          <div class="panel-header">
            <span class="panel-title">标签管理</span>
            <el-button :icon="Close" text circle @click="closeTagPanel" />
          </div>
          <div class="panel-body">
            <div class="tag-manage-content">
              <!-- 标签列表 -->
              <div class="tag-grid">
                <div
                  v-for="tag in tags"
                  :key="tag.id"
                  class="tag-card"
                  :class="{ editing: editingTag?.id === tag.id }"
                  :style="{ background: tag.color }"
                  @click="onEditTag(tag)"
                >
                  {{ tag.name }}
                </div>
              </div>
              <el-empty v-if="!tags.length" description="暂无标签" :image-size="60" />

              <!-- 新建/编辑表单 -->
              <div class="tag-form-section">
                <div class="tag-form-header">
                  <span>{{ editingTag ? '编辑标签' : '新建标签' }}</span>
                  <el-button v-if="editingTag" text size="small" @click="resetTagForm">取消编辑</el-button>
                </div>
                <div class="tag-form">
                  <div class="form-item">
                    <label class="form-label">标签名称</label>
                    <el-input v-model="tagForm.name" placeholder="请输入标签名" maxlength="4" show-word-limit />
                  </div>
                  <div class="form-item">
                    <div class="color-header">
                      <label class="form-label">标签颜色</label>
                      <div
                        v-if="tagForm.name && tagForm.color"
                        class="color-preview"
                        :style="{ background: tagForm.color }"
                      >
                        {{ tagForm.name }}
                      </div>
                    </div>
                    <div class="color-grid">
                      <div
                        v-for="color in colorOptions"
                        :key="color"
                        class="color-item"
                        :class="{ selected: tagForm.color === color }"
                        :style="{ background: color }"
                        @click="selectTagColor(color)"
                      >
                        <el-icon v-if="tagForm.color === color" :size="14" color="#fff"><Check /></el-icon>
                      </div>
                    </div>
                  </div>
                  <div class="tag-form-actions">
                    <el-button type="primary" @click="onSubmitTag">
                      {{ editingTag ? '保存修改' : '新建标签' }}
                    </el-button>
                    <el-button v-if="editingTag" type="danger" plain @click="onDeleteTag">删除标签</el-button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </div>

    <!-- 收支选择器 -->
    <el-dialog
      v-model="showTemplateActionPicker"
      title="选择收支"
      width="520"
      :z-index="4000"
      class="picker-dialog"
    >
      <div class="picker-list">
        <div
          v-for="action in actions"
          :key="action.id"
          class="picker-item"
          :class="{ active: templateForm.actionId === action.id }"
          @click="onSelectTemplateAction(action)"
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
              <span v-if="action.exempt" class="exempt-tag">{{ getExemptText(action) }}</span>
            </div>
          </div>
        </div>
        <el-empty v-if="!actions.length" description="暂无收支类型" :image-size="60" />
      </div>
    </el-dialog>

    <!-- 账户选择器 -->
    <el-dialog
      v-model="showTemplateAccountPicker"
      :title="templateAccountPickerType === 1 ? (isTemplateTransfer ? '选择转出账户' : '选择账户') : '选择转入账户'"
      width="520"
      :z-index="4000"
      class="picker-dialog"
    >
      <div class="picker-list">
        <el-tooltip
          v-for="account in accounts"
          :key="account.id"
          :content="getAccountDisabledReason(account, templateAccountPickerType)"
          :disabled="!isAccountDisabled(account, templateAccountPickerType)"
          placement="right"
        >
          <div
            class="picker-item account-picker-item"
            :class="{ disabled: isAccountDisabled(account, templateAccountPickerType) }"
            @click="!isAccountDisabled(account, templateAccountPickerType) && onSelectTemplateAccount(account)"
          >
            <div class="picker-left">
              <span
                class="account-type-tag"
                :class="account.accountType === AccountType.LIABILITY ? 'liability' : 'asset'"
              >
                {{ account.accountType === AccountType.LIABILITY ? '负债' : '资产' }}
              </span>
              <div class="picker-info">
                <span class="picker-name">{{ account.name }}</span>
                <span v-if="account.note" class="picker-hint">{{ account.note }}</span>
              </div>
            </div>
            <div class="picker-right">
              <span class="picker-money">¥{{ account.money }}</span>
              <span v-if="account.exemptMoney && parseFloat(account.exemptMoney) !== 0" class="picker-exempt">
                不计入 ¥{{ account.exemptMoney }}
              </span>
            </div>
          </div>
        </el-tooltip>
        <el-empty v-if="!accounts.length" description="暂无账户" :image-size="60" />
      </div>
    </el-dialog>

    <!-- 分类选择器 -->
    <el-dialog
      v-model="showTemplateTypePicker"
      title="选择分类"
      width="520"
      :z-index="4000"
      class="picker-dialog"
    >
      <div class="type-picker-list">
        <div v-for="parent in templateTypes" :key="parent.id" class="type-picker-group">
          <div
            class="type-picker-parent"
            :class="{
              active: templateForm.typeId === parent.id,
              'has-children': parent.childrenTypes?.length
            }"
            @click="onSelectTemplateType(parent)"
          >
            {{ parent.tname }}
            <span v-if="!parent.childrenTypes?.length" class="selectable-hint">可选</span>
          </div>
          <div v-if="parent.childrenTypes?.length" class="type-picker-children">
            <div
              v-for="child in parent.childrenTypes"
              :key="child.id"
              class="type-picker-child"
              :class="{ active: templateForm.typeId === child.id }"
              @click="onSelectTemplateType(child, parent)"
            >
              {{ child.tname }}
            </div>
          </div>
        </div>
        <el-empty v-if="!templateTypes.length" description="暂无分类" :image-size="60" />
      </div>
    </el-dialog>

    <!-- 标签选择器 -->
    <el-dialog
      v-model="showTemplateTagPicker"
      title="选择标签"
      width="520"
      :z-index="4000"
      class="picker-dialog"
    >
      <div v-if="tags.length" class="tag-picker-grid">
        <div
          v-for="tag in tags"
          :key="tag.id"
          class="tag-picker-item"
          :class="{ active: templateForm.tagId === tag.id }"
          :style="{ background: tag.color, '--tag-color': tag.color }"
          @click="onSelectTemplateTag(tag)"
        >
          {{ tag.name }}
        </div>
      </div>
      <el-empty v-else description="暂无标签" :image-size="60" />
      <template #footer>
        <el-button @click="onSelectTemplateTag(null)">清空标签</el-button>
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

.drawer-header-right {
  display: flex;
  gap: 8px;
}

.drawer-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

/* 面板容器 */
.template-panels-container {
  display: flex;
  height: 100%;
}

/* 通用面板 */
.panel {
  display: flex;
  flex-direction: column;
  background: var(--color-bg-card);
  border-right: 1px solid var(--color-border);
  overflow: hidden;
}

.panel:last-child {
  border-right: none;
}

.template-list-panel {
  width: 520px;
  min-width: 520px;
}

.template-edit-panel {
  width: 420px;
  min-width: 420px;
  background: linear-gradient(180deg, var(--color-bg-page) 0%, var(--color-bg-card) 100%);
}

.tag-manage-panel {
  width: 340px;
  min-width: 340px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border-light);
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.panel-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.panel-footer {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--color-border-light);
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
}

.panel-footer .el-button {
  flex: 1;
  height: 44px;
  border-radius: 12px;
  font-weight: 500;
}

/* 面板动画 */
.slide-panel-enter-active,
.slide-panel-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-panel-enter-from,
.slide-panel-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

/* 标签筛选卡片 */
.tag-filter-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: var(--color-bg-card);
  border-bottom: 1px solid var(--color-border-light);
}

.filter-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.filter-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.tag-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.tag-chip {
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 12px;
  color: #fff;
  cursor: pointer;
  transition: opacity 0.2s;
}

.tag-chip:hover {
  opacity: 0.85;
}

.selected-filter-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 12px;
  color: #fff;
  cursor: pointer;
}

.selected-filter-tag:hover {
  opacity: 0.85;
}

.no-tags-hint {
  font-size: 13px;
  color: var(--color-text-tertiary);
}

/* 模板列表 */
.template-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.template-card {
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(8px);
  border-radius: 14px;
  margin-bottom: 12px;
  border: 1.5px solid rgba(0, 0, 0, 0.04);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.template-main {
  padding: 16px 20px;
  cursor: pointer;
  transition: background 0.2s;
}

.template-main:hover {
  background: rgba(0, 0, 0, 0.02);
}

.template-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.template-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.template-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.template-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.template-tag {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  color: #fff;
  font-weight: 500;
}

.expand-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all 0.2s;
}

.expand-icon:hover {
  background: rgba(0, 0, 0, 0.06);
  color: var(--color-text-secondary);
}

.expand-icon.rotated {
  transform: rotate(180deg);
}

.template-money {
  display: flex;
  align-items: baseline;
  gap: 2px;
  margin-top: 10px;
}

.money-symbol {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.money-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: -0.5px;
}

.template-details {
  padding: 12px 20px 16px;
  margin-top: 4px;
  border-top: 1px dashed var(--color-border-light);
}

.template-details .detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--color-border-light);
}

.template-details .detail-row:last-child {
  border-bottom: none;
}

.template-details .detail-label {
  font-size: 14px;
  color: var(--color-text-tertiary);
}

.template-details .detail-value {
  font-size: 14px;
  color: var(--color-text-primary);
}

.template-details .detail-value.transfer {
  color: var(--color-transfer);
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
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
  border: 1px solid var(--color-border);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.form-item {
  margin-bottom: 20px;
}

.form-item:last-child {
  margin-bottom: 0;
}

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: 10px;
}

.required {
  color: var(--color-expense);
}

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

.exempt-tag {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--color-bg-page);
  color: var(--color-text-tertiary);
}

.input-hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--color-text-tertiary);
}

/* 日期类型选择 */
.date-type-group {
  display: flex;
  gap: 12px;
}

.date-type-item {
  flex: 1;
  padding: 12px;
  text-align: center;
  font-size: 14px;
  color: var(--color-text-secondary);
  background: rgba(255, 255, 255, 0.8);
  border-radius: 10px;
  border: 1px solid var(--color-border-light);
  cursor: pointer;
  transition: all 0.2s;
}

.date-type-item:hover {
  background: rgba(255, 255, 255, 1);
  border-color: var(--color-border);
}

.date-type-item.active {
  color: var(--color-transfer);
  border: 2px solid var(--color-transfer);
  background: var(--color-transfer-bg);
}

/* 标签管理 */
.tag-manage-content {
  padding: 0;
}

.tag-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 0 0 20px;
}

.tag-card {
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  color: #fff;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.tag-card:hover {
  opacity: 0.9;
}

.tag-card.editing {
  border-color: var(--color-text-primary);
  box-shadow: 0 0 0 2px var(--color-bg-card);
}

.tag-form-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--color-border-light);
}

.tag-form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.tag-form .form-item {
  margin-bottom: 16px;
}

.color-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.color-header .form-label {
  margin-bottom: 0;
}

.color-preview {
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 12px;
  color: #fff;
}

.color-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 8px;
}

.color-item {
  aspect-ratio: 1;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.color-item:hover {
  opacity: 0.85;
  transform: scale(1.05);
}

.color-item.selected {
  box-shadow: 0 0 0 2px var(--color-bg-card), 0 0 0 4px var(--color-text-primary);
}

.tag-form-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.tag-form-actions .el-button {
  flex: 1;
}

/* 选择器弹窗 */
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

.picker-money {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.picker-hint {
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-top: 4px;
}

/* 账户选择器样式 */
.account-picker-item {
  flex-direction: row;
  justify-content: space-between;
}

.account-picker-item.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.picker-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.picker-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  flex-shrink: 0;
}

.picker-exempt {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.account-type-tag {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 4px;
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

/* 分类选择器 */
.type-picker-list {
  max-height: 400px;
  overflow-y: auto;
}

.type-picker-group {
  margin-bottom: 12px;
}

.type-picker-parent {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  background: var(--color-bg-page);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.type-picker-parent:hover {
  background: var(--color-bg-card);
}

.type-picker-parent.active {
  border-color: var(--color-transfer);
  background: rgba(24, 144, 255, 0.05);
}

/* 有子分类的一级分类不可选 */
.type-picker-parent.has-children {
  cursor: default;
  color: var(--color-text-secondary);
}

.type-picker-parent.has-children:hover {
  background: var(--color-bg-page);
}

.selectable-hint {
  font-size: 12px;
  font-weight: 400;
  color: var(--color-text-tertiary);
  padding: 2px 8px;
  background: var(--color-bg-card);
  border-radius: 4px;
}

.type-picker-children {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 16px 0;
}

.type-picker-child {
  padding: 8px 14px;
  font-size: 13px;
  color: var(--color-text-secondary);
  background: var(--color-bg-page);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.type-picker-child:hover {
  color: var(--color-text-primary);
  background: var(--color-bg-card);
}

.type-picker-child.active {
  color: var(--color-transfer);
  border-color: var(--color-transfer);
  background: rgba(24, 144, 255, 0.05);
}

/* 标签选择器 */
.tag-picker-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.tag-picker-item {
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 13px;
  color: #fff;
  font-weight: 500;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tag-picker-item:hover {
  opacity: 0.85;
  transform: scale(1.02);
}

.tag-picker-item.active {
  border-color: color-mix(in srgb, var(--tag-color) 70%, black);
  box-shadow: 0 2px 8px color-mix(in srgb, var(--tag-color) 50%, transparent);
}
</style>
