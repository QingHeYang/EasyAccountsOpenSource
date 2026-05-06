<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { typeApi, type TypeWithChildren } from '@shared/api/type'

export interface TypePickerValue {
  id: number
  tname: string
}

const props = defineProps<{
  /** 当前收支 id（变化时自动重新拉分类树） */
  actionId: number | null
  /** 当前选中分类（双向） */
  modelValue: TypePickerValue | null
  /** popup 显示（双向） */
  open: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: TypePickerValue | null]
  'update:open': [value: boolean]
}>()

// ============ 数据 ============
const types = ref<TypeWithChildren[]>([])
const loading = ref(false)
const loadFailed = ref(false)

// 竞态守卫：每次发起 fetch 拿一个 token，回包时校验
let fetchToken = 0

async function fetchTypes() {
  if (!props.actionId) {
    types.value = []
    return
  }
  const myToken = ++fetchToken
  loading.value = true
  loadFailed.value = false
  try {
    const res = await typeApi.getByActionId(props.actionId)
    if (myToken !== fetchToken) return // 已被新请求覆盖，丢弃
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
    // 展开后下一帧 focus
    nextTick(() => searchInputRef.value?.focus())
  } else {
    // 收起时清空关键词，避免隐藏的过滤器还在生效
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
      // 父匹配：保留全部子
      result.push(parent)
    } else if (matchedChildren.length > 0) {
      // 子匹配：仅保留匹配的子
      result.push({ ...parent, childrenTypes: matchedChildren })
    }
  }
  return result
})

// ============ 选中 ============
function isParentSelected(parent: TypeWithChildren): boolean {
  return props.modelValue?.id === parent.id
}

function isChildSelected(child: TypeWithChildren): boolean {
  return props.modelValue?.id === child.id
}

function selectParent(parent: TypeWithChildren) {
  // 业务规则：仅当父无子分类时可选父
  if (parent.childrenTypes && parent.childrenTypes.length > 0) return
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
  // 延迟 200ms 让用户看到选中态再关
  setTimeout(() => emit('update:open', false), 200)
}

function close() {
  emit('update:open', false)
}

// ============ 生命周期 ============
// 每次 popup 打开时重新拉（按用户决策 A）
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

// actionId 在打开期间变化也要重拉（防止外部切换）
watch(
  () => props.actionId,
  () => {
    if (props.open) fetchTypes()
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
    <div class="tp-popup">
      <!-- 头部 -->
      <div class="tp-header">
        <div class="tp-title">选择账单分类</div>
        <div class="tp-header-actions">
          <div
            class="tp-icon-btn"
            :class="{ active: searchVisible }"
            @click="toggleSearch"
          >
            <van-icon name="search" size="16" />
          </div>
          <div class="tp-icon-btn" @click="close">
            <van-icon name="cross" size="18" />
          </div>
        </div>
      </div>

      <!-- 搜索框（点搜索按钮才展开） -->
      <Transition name="tp-search-collapse">
        <div v-if="searchVisible" class="tp-search">
          <van-icon name="search" size="14" class="tp-search-icon" />
          <input
            ref="searchInputRef"
            v-model="keyword"
            class="tp-search-input"
            placeholder="搜索分类..."
          />
          <van-icon
            v-if="keyword"
            name="clear"
            size="16"
            class="tp-search-clear"
            @click="keyword = ''"
          />
        </div>
      </Transition>

      <!-- 内容区 -->
      <div class="tp-body">
        <!-- 加载中 -->
        <div v-if="loading" class="tp-state">
          <van-loading size="24" />
        </div>

        <!-- 加载失败 -->
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

        <!-- 没收支 -->
        <van-empty
          v-else-if="!actionId"
          description="请先选择收支类型"
          :image-size="80"
        />

        <!-- 空数据 -->
        <van-empty
          v-else-if="types.length === 0"
          description="该收支类型暂无分类"
          :image-size="80"
        />

        <!-- 搜索无结果 -->
        <van-empty
          v-else-if="filteredTypes.length === 0"
          description="没有匹配的分类"
          :image-size="80"
        />

        <!-- 网格列表 -->
        <div v-else class="tp-list">
          <div
            v-for="parent in filteredTypes"
            :key="parent.id"
            class="tp-group"
          >
            <!-- 一级标题：有子节点 → 不可点击；无子节点 → 整行可点击 + "可选" hint -->
            <div
              class="tp-parent"
              :class="{
                'has-children': parent.childrenTypes && parent.childrenTypes.length > 0,
                active: isParentSelected(parent),
              }"
              @click="selectParent(parent)"
            >
              <span class="tp-parent-name">{{ parent.tname }}</span>
              <span
                v-if="!parent.childrenTypes || parent.childrenTypes.length === 0"
                class="tp-parent-hint"
              >可选</span>
            </div>

            <!-- 二级 chip -->
            <div
              v-if="parent.childrenTypes && parent.childrenTypes.length > 0"
              class="tp-children"
            >
              <div
                v-for="child in parent.childrenTypes"
                :key="child.id"
                class="tp-chip"
                :class="{ active: isChildSelected(child) }"
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
.tp-popup {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-card);
}

/* 头部 */
.tp-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px 12px;
  border-bottom: 1px solid var(--color-border-light);
}

.tp-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.tp-header-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tp-icon-btn {
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

.tp-icon-btn:active {
  opacity: 0.7;
}

.tp-icon-btn.active {
  background: rgba(24, 144, 255, 0.12);
  color: var(--color-transfer);
}

/* 搜索框 */
.tp-search {
  position: relative;
  display: flex;
  align-items: center;
  margin: 12px 20px 8px;
  padding: 8px 12px;
  background: var(--color-bg-page);
  border-radius: 10px;
}

.tp-search-icon {
  color: var(--color-text-tertiary);
  margin-right: 6px;
  flex-shrink: 0;
}

.tp-search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 14px;
  color: var(--color-text-primary);
}

.tp-search-input::placeholder {
  color: var(--color-text-tertiary);
}

.tp-search-clear {
  color: var(--color-text-tertiary);
  margin-left: 6px;
  flex-shrink: 0;
}

.tp-search-clear:active {
  color: var(--color-text-primary);
}

/* 搜索框展开/收起动画 */
.tp-search-collapse-enter-active,
.tp-search-collapse-leave-active {
  transition: opacity 0.2s ease, max-height 0.25s ease, margin-top 0.25s ease,
    padding-top 0.25s ease, padding-bottom 0.25s ease;
  overflow: hidden;
}

.tp-search-collapse-enter-from,
.tp-search-collapse-leave-to {
  opacity: 0;
  max-height: 0;
  margin-top: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.tp-search-collapse-enter-to,
.tp-search-collapse-leave-from {
  max-height: 60px;
}

/* 内容区 */
.tp-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 20px 20px;
}

.tp-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
}

.tp-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 群组：每个一级分类作为一张独立卡片，块间界限分明 */
.tp-group {
  background: var(--color-bg-page);
  border-radius: 12px;
  border: 1px solid var(--color-border-light, rgba(0, 0, 0, 0.06));
  overflow: hidden;
}

/* 一级（带 children）：标题段，作为卡片头部 */
.tp-parent.has-children {
  display: flex;
  align-items: center;
  padding: 10px 14px 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  cursor: default;
  pointer-events: none;
  letter-spacing: 0.3px;
}

.tp-parent.has-children .tp-parent-name::before {
  content: '';
  display: inline-block;
  width: 3px;
  height: 12px;
  background: var(--color-transfer);
  border-radius: 2px;
  margin-right: 8px;
  vertical-align: -1px;
  opacity: 0.7;
}

/* 一级（无 children）：作为完整可点行卡 */
.tp-parent:not(.has-children) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  border: 2px solid transparent;
  border-radius: 12px;
  margin: -1px;
  transition: all 0.2s;
}

.tp-parent:not(.has-children):active {
  background: var(--color-bg-card);
}

.tp-parent.active:not(.has-children) {
  border-color: var(--color-transfer);
  background: rgba(24, 144, 255, 0.08);
  color: var(--color-transfer);
}

.tp-parent-hint {
  padding: 2px 8px;
  background: var(--color-bg-card);
  border-radius: 6px;
  font-size: 11px;
  font-weight: 400;
  color: var(--color-text-tertiary);
}

.tp-parent.active:not(.has-children) .tp-parent-hint {
  background: rgba(24, 144, 255, 0.15);
  color: var(--color-transfer);
}

/* 二级 chip 区 */
.tp-children {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 6px 12px 12px;
}

.tp-chip {
  padding: 7px 14px;
  background: var(--color-bg-card);
  border: 1.5px solid transparent;
  border-radius: 10px;
  font-size: 13px;
  color: var(--color-text-secondary);
  transition: all 0.15s;
}

.tp-chip:active {
  background: var(--color-bg-card);
  color: var(--color-text-primary);
}

.tp-chip.active {
  background: rgba(24, 144, 255, 0.1);
  border-color: var(--color-transfer);
  color: var(--color-transfer);
  font-weight: 500;
}
</style>

<style>
/* === 暗黑模式 === */
html.dark .tp-popup {
  background: #1e1e1e;
}

html.dark .tp-popup .tp-header {
  border-bottom-color: rgba(255, 255, 255, 0.08);
}

html.dark .tp-popup .tp-icon-btn {
  background: rgba(255, 255, 255, 0.06);
}

html.dark .tp-popup .tp-icon-btn.active {
  background: rgba(116, 192, 252, 0.18);
  color: #74C0FC;
}

/* 搜索框：胶囊半透明白底（不透明，否则失去圆角识别） */
html.dark .tp-popup .tp-search {
  background: rgba(255, 255, 255, 0.06);
}

html.dark .tp-popup .tp-search-input {
  background: transparent;
  color: var(--color-text-primary);
}

/* 群组卡片 */
html.dark .tp-popup .tp-group {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
}

/* 一级标题（无 children 可点击态）  */
html.dark .tp-popup .tp-parent.active:not(.has-children) {
  background: rgba(116, 192, 252, 0.14);
  border-color: #74C0FC;
  color: #74C0FC;
}

html.dark .tp-popup .tp-parent-hint {
  background: rgba(255, 255, 255, 0.08);
}

html.dark .tp-popup .tp-parent.active:not(.has-children) .tp-parent-hint {
  background: rgba(116, 192, 252, 0.22);
  color: #74C0FC;
}

/* 二级 chip：稍微深一档让它跟群组卡区分 */
html.dark .tp-popup .tp-chip {
  background: rgba(255, 255, 255, 0.06);
  color: var(--color-text-secondary);
}

html.dark .tp-popup .tp-chip.active {
  background: rgba(116, 192, 252, 0.14);
  border-color: #74C0FC;
  color: #74C0FC;
}
</style>
