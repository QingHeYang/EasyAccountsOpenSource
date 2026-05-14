<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { typeApi, type TypeWithChildren } from '@shared/api/type'

export interface StatTypePickerValue {
  id: number
  tname: string
}

const props = defineProps<{
  /** 当前选中分类（双向） */
  modelValue: StatTypePickerValue | null
  /** popup 显示（双向） */
  open: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: StatTypePickerValue | null]
  'update:open': [value: boolean]
}>()

// ============ 数据 ============
// 拉全部分类（不按 action 过滤），用于统计场景
const types = ref<TypeWithChildren[]>([])
const loading = ref(false)
const loadFailed = ref(false)

let fetchToken = 0

async function fetchTypes() {
  const myToken = ++fetchToken
  loading.value = true
  loadFailed.value = false
  try {
    const res = await typeApi.getAll()
    if (myToken !== fetchToken) return
    if (res.data.code === 0) {
      types.value = res.data.data || []
    } else {
      types.value = []
      loadFailed.value = true
    }
  } catch (err) {
    if (myToken !== fetchToken) return
    console.error('获取分类列表失败', err)
    types.value = []
    loadFailed.value = true
  } finally {
    if (myToken === fetchToken) loading.value = false
  }
}

// ============ 搜索 ============
const keyword = ref('')
const searchVisible = ref(false)
const searchInputRef = ref<HTMLInputElement | null>(null)

function toggleSearch() {
  searchVisible.value = !searchVisible.value
  if (searchVisible.value) {
    nextTick(() => searchInputRef.value?.focus())
  } else {
    keyword.value = ''
  }
}

const filteredTypes = computed<TypeWithChildren[]>(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return types.value

  const result: TypeWithChildren[] = []
  for (const parent of types.value) {
    const parentMatch = parent.tname.toLowerCase().includes(kw)
    const matchedChildren = (parent.childrenTypes || []).filter((c) =>
      c.tname.toLowerCase().includes(kw)
    )
    if (parentMatch) {
      result.push(parent)
    } else if (matchedChildren.length > 0) {
      result.push({ ...parent, childrenTypes: matchedChildren })
    }
  }
  return result
})

// ============ action 标签样式 ============
function getActionClass(handle: number | undefined): string {
  if (handle === 0) return 'income'
  if (handle === 1) return 'expense'
  if (handle === 2) return 'transfer'
  return ''
}

// ============ 选中 ============
function isSelected(node: TypeWithChildren): boolean {
  return props.modelValue?.id === node.id
}

function selectParent(parent: TypeWithChildren) {
  // 统计场景：父无论有无 children 都可选（"全部"聚合语义）
  emit('update:modelValue', { id: parent.id, tname: parent.tname })
  closeWithDelay()
}

function selectChild(parent: TypeWithChildren, child: TypeWithChildren) {
  emit('update:modelValue', {
    id: child.id,
    tname: `${parent.tname}/${child.tname}`,
  })
  closeWithDelay()
}

function closeWithDelay() {
  setTimeout(() => emit('update:open', false), 200)
}

function close() {
  emit('update:open', false)
}

// ============ 生命周期 ============
watch(
  () => props.open,
  (val) => {
    if (val) {
      keyword.value = ''
      searchVisible.value = false
      fetchTypes()
    }
  }
)
</script>

<template>
  <van-popup
    :show="open"
    round
    position="bottom"
    teleport="body"
    :style="{ height: '70%' }"
    @update:show="(v: boolean) => emit('update:open', v)"
  >
    <div class="stp-popup">
      <!-- 头部 -->
      <div class="stp-header">
        <div class="stp-title">选择分类</div>
        <div class="stp-header-actions">
          <div
            class="stp-icon-btn"
            :class="{ active: searchVisible }"
            @click="toggleSearch"
          >
            <van-icon name="search" size="16" />
          </div>
          <div class="stp-icon-btn" @click="close">
            <van-icon name="cross" size="18" />
          </div>
        </div>
      </div>

      <!-- 搜索框 -->
      <Transition name="stp-search-collapse">
        <div v-if="searchVisible" class="stp-search">
          <van-icon name="search" size="14" class="stp-search-icon" />
          <input
            ref="searchInputRef"
            v-model="keyword"
            class="stp-search-input"
            placeholder="搜索分类..."
          />
          <van-icon
            v-if="keyword"
            name="clear"
            size="16"
            class="stp-search-clear"
            @click="keyword = ''"
          />
        </div>
      </Transition>

      <!-- 内容区 -->
      <div class="stp-body">
        <div v-if="loading" class="stp-state">
          <van-loading size="24" />
        </div>

        <van-empty
          v-else-if="loadFailed"
          image="network"
          description="加载失败"
          :image-size="80"
        >
          <van-button round type="primary" size="small" @click="fetchTypes">
            重试
          </van-button>
        </van-empty>

        <van-empty
          v-else-if="types.length === 0"
          description="暂无分类"
          :image-size="80"
        />

        <van-empty
          v-else-if="filteredTypes.length === 0"
          description="没有匹配的分类"
          :image-size="80"
        />

        <div v-else class="stp-list">
          <div
            v-for="parent in filteredTypes"
            :key="parent.id"
            class="stp-group"
            :class="{ 'has-children': parent.childrenTypes && parent.childrenTypes.length > 0 }"
          >
            <!-- 一级标题（无论有无 children 都可点选；带 action 标签） -->
            <div
              class="stp-parent"
              :class="{ active: isSelected(parent) }"
              @click="selectParent(parent)"
            >
              <div class="stp-parent-info">
                <span class="stp-parent-name">{{ parent.tname }}</span>
                <span
                  v-if="parent.action"
                  class="stp-action-tag"
                  :class="getActionClass(parent.action.handle)"
                >{{ parent.action.hname }}</span>
              </div>
            </div>

            <!-- 二级 chip 区：第一个是"全部"chip（同点击父级，便于发现） -->
            <div
              v-if="parent.childrenTypes && parent.childrenTypes.length > 0"
              class="stp-children"
            >
              <div
                class="stp-chip stp-chip-all"
                :class="{ active: isSelected(parent) }"
                @click="selectParent(parent)"
              >
                全部
              </div>
              <div
                v-for="child in parent.childrenTypes"
                :key="child.id"
                class="stp-chip"
                :class="{ active: isSelected(child) }"
                @click="selectChild(parent, child)"
              >
                {{ child.tname }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </van-popup>
</template>

<style scoped>
.stp-popup {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-card);
}

/* 头部 */
.stp-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px 12px;
  border-bottom: 1px solid var(--color-border-light);
}

.stp-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.stp-header-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.stp-icon-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--color-bg-page);
  color: var(--color-text-secondary);
  transition: background 0.15s, color 0.15s;
}

.stp-icon-btn:active {
  opacity: 0.7;
}

.stp-icon-btn.active {
  background: rgba(24, 144, 255, 0.12);
  color: var(--color-transfer);
}

/* 搜索框 */
.stp-search {
  position: relative;
  display: flex;
  align-items: center;
  margin: 12px 20px 8px;
  padding: 8px 12px;
  background: var(--color-bg-page);
  border-radius: 10px;
}

.stp-search-icon {
  color: var(--color-text-tertiary);
  margin-right: 6px;
  flex-shrink: 0;
}

.stp-search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 14px;
  color: var(--color-text-primary);
}

.stp-search-input::placeholder {
  color: var(--color-text-tertiary);
}

.stp-search-clear {
  color: var(--color-text-tertiary);
  margin-left: 6px;
  flex-shrink: 0;
}

.stp-search-clear:active {
  color: var(--color-text-primary);
}

.stp-search-collapse-enter-active,
.stp-search-collapse-leave-active {
  transition: opacity 0.2s ease, max-height 0.25s ease, margin-top 0.25s ease,
    padding-top 0.25s ease, padding-bottom 0.25s ease;
  overflow: hidden;
}

.stp-search-collapse-enter-from,
.stp-search-collapse-leave-to {
  opacity: 0;
  max-height: 0;
  margin-top: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.stp-search-collapse-enter-to,
.stp-search-collapse-leave-from {
  max-height: 60px;
}

/* 内容区 */
.stp-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 20px 20px;
}

.stp-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
}

.stp-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 群组卡 */
.stp-group {
  background: var(--color-bg-page);
  border-radius: 12px;
  border: 1px solid var(--color-border-light, rgba(0, 0, 0, 0.06));
  overflow: hidden;
  transition: border-color 0.2s, background 0.2s;
}

/* 一级标题 */
.stp-parent {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  cursor: pointer;
  transition: background 0.15s;
}

/* 有 children 的一级：标题段更紧凑 + 字号小一档（视觉弱化） */
.stp-group.has-children .stp-parent {
  padding: 10px 14px 6px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.stp-parent:active {
  background: var(--color-bg-card);
}

/* 选中：用群组卡边框和背景做整体高亮 */
.stp-group .stp-parent.active {
  color: var(--color-transfer);
}

.stp-group:has(.stp-parent.active) {
  border-color: var(--color-transfer);
  background: rgba(24, 144, 255, 0.06);
}

.stp-parent-info {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.stp-parent-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stp-action-tag {
  flex-shrink: 0;
  padding: 1px 8px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 500;
}

.stp-action-tag.income {
  background: rgba(82, 196, 26, 0.12);
  color: var(--color-income);
}

.stp-action-tag.expense {
  background: rgba(245, 34, 45, 0.12);
  color: var(--color-expense);
}

.stp-action-tag.transfer {
  background: rgba(24, 144, 255, 0.12);
  color: var(--color-transfer);
}

/* 二级 chip 区 */
.stp-children {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 6px 12px 12px;
}

.stp-chip {
  padding: 7px 14px;
  background: var(--color-bg-card);
  border: 1.5px solid transparent;
  border-radius: 10px;
  font-size: 13px;
  color: var(--color-text-secondary);
  transition: all 0.15s;
}

.stp-chip:active {
  background: var(--color-bg-card);
  color: var(--color-text-primary);
}

.stp-chip.active {
  background: rgba(24, 144, 255, 0.1);
  border-color: var(--color-transfer);
  color: var(--color-transfer);
  font-weight: 500;
}

/* "全部"chip 跟普通 chip 视觉区分一点（虚边框） */
.stp-chip-all {
  border-style: dashed;
  border-color: var(--color-border);
}

.stp-chip-all.active {
  border-style: solid;
}
</style>

<style>
/* === 暗黑模式 === */
html.dark .stp-popup {
  background: #1e1e1e;
}

html.dark .stp-popup .stp-header {
  border-bottom-color: rgba(255, 255, 255, 0.08);
}

html.dark .stp-popup .stp-icon-btn {
  background: rgba(255, 255, 255, 0.06);
}

html.dark .stp-popup .stp-icon-btn.active {
  background: rgba(116, 192, 252, 0.18);
  color: #74C0FC;
}

html.dark .stp-popup .stp-search {
  background: rgba(255, 255, 255, 0.06);
}

html.dark .stp-popup .stp-search-input {
  background: transparent;
  color: var(--color-text-primary);
}

html.dark .stp-popup .stp-group {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
}

html.dark .stp-popup .stp-group:has(.stp-parent.active) {
  background: rgba(116, 192, 252, 0.1);
  border-color: #74C0FC;
}

html.dark .stp-popup .stp-group .stp-parent.active {
  color: #74C0FC;
}

html.dark .stp-popup .stp-action-tag.income {
  background: rgba(105, 219, 124, 0.18);
  color: #69DB7C;
}

html.dark .stp-popup .stp-action-tag.expense {
  background: rgba(255, 107, 107, 0.18);
  color: #FF6B6B;
}

html.dark .stp-popup .stp-action-tag.transfer {
  background: rgba(116, 192, 252, 0.18);
  color: #74C0FC;
}

html.dark .stp-popup .stp-chip {
  background: rgba(255, 255, 255, 0.06);
  color: var(--color-text-secondary);
}

html.dark .stp-popup .stp-chip.active {
  background: rgba(116, 192, 252, 0.14);
  border-color: #74C0FC;
  color: #74C0FC;
}

html.dark .stp-popup .stp-chip-all {
  border-color: rgba(255, 255, 255, 0.18);
}
</style>
