<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { templateApi, type Template } from '@shared/api/template'
import { tagApi, type Tag } from '@shared/api/tag'
import { useSmartBack } from '@shared/composables/useSmartBack'

const router = useRouter()
const { smartBack } = useSmartBack()

// 数据
const loading = ref(false)
const templates = ref<Template[]>([])
const tags = ref<Tag[]>([])
const selectedTag = ref<Tag | null>(null)
const showTagFilter = ref(false)
const expandedIds = ref<number[]>([])

// 获取收支样式类
function getActionClass(handle: number | undefined): string {
  if (handle === 0) return 'income'
  if (handle === 1) return 'expense'
  if (handle === 2) return 'transfer'
  return ''
}

// 加载模板列表
async function fetchTemplates() {
  loading.value = true
  try {
    const res = selectedTag.value
      ? await templateApi.getByTagId(selectedTag.value.id)
      : await templateApi.getAll()
    templates.value = res.data.data || []
  } catch (err) {
    console.error('获取模板列表失败', err)
  } finally {
    loading.value = false
  }
}

// 加载标签列表
async function fetchTags() {
  try {
    const res = await tagApi.getAll()
    tags.value = res.data.data || []
  } catch (err) {
    console.error('获取标签列表失败', err)
  }
}

// 选择标签筛选
function onSelectTag(tag: Tag) {
  selectedTag.value = tag
  showTagFilter.value = false
  fetchTemplates()
}

// 清除标签筛选
function onClearTag() {
  selectedTag.value = null
  fetchTemplates()
}

// 切换展开
function toggleExpand(id: number, event: Event) {
  event.stopPropagation()
  const index = expandedIds.value.indexOf(id)
  if (index > -1) {
    expandedIds.value.splice(index, 1)
  } else {
    expandedIds.value.push(id)
  }
}

// 是否有详情内容
function hasDetails(item: Template): boolean {
  return !!(
    item.account?.name ||
    item.accountTo?.name ||
    item.type?.tname ||
    (item.dateType !== undefined && item.dateType !== null)
  )
}

// 导航
function onBack() {
  smartBack('/setting')
}

function onAdd() {
  router.push('/setting/template/add')
}

function onEdit(id: number) {
  router.push(`/setting/template/edit/${id}`)
}

onMounted(() => {
  // 重置滚动位置
  window.scrollTo(0, 0)

  fetchTags()
  fetchTemplates()
})
</script>

<template>
  <div class="template-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="header-left" @click="onBack">
        <van-icon name="arrow-left" size="20" />
      </div>
      <div class="header-title">快记模板</div>
      <div class="header-right" @click="onAdd">
        <van-icon name="plus" size="20" />
      </div>
    </div>

    <!-- 页面内容 -->
    <div class="page-body">
      <!-- 标签筛选 -->
      <div class="filter-card" @click="showTagFilter = !showTagFilter">
        <div class="filter-left">
          <van-icon name="filter-o" size="18" />
          <span>标签筛选</span>
        </div>
        <div class="filter-right">
          <div
            v-if="selectedTag"
            class="selected-tag"
            :style="{ background: selectedTag.color }"
            @click.stop="onClearTag"
          >
            {{ selectedTag.name }}
            <van-icon name="cross" size="12" />
          </div>
          <van-icon v-else :name="showTagFilter ? 'arrow-up' : 'arrow-down'" size="16" />
        </div>
      </div>

      <!-- 标签选择面板 -->
      <div v-show="showTagFilter" class="tag-panel">
        <div v-if="tags.length" class="tag-list">
          <div
            v-for="tag in tags"
            :key="tag.id"
            class="tag-item"
            :style="{ background: tag.color }"
            @click="onSelectTag(tag)"
          >
            {{ tag.name }}
          </div>
        </div>
        <div v-else class="no-tags">暂无标签</div>
      </div>

      <!-- 模板列表 -->
      <div class="template-list" v-if="templates.length">
        <div
          v-for="item in templates"
          :key="item.id"
          class="template-card"
        >
          <!-- 主体区域（可点击编辑） -->
          <div class="card-main" @click="onEdit(item.id)">
            <!-- 第一行：名称 + 收支 + 标签 -->
            <div class="card-row">
              <div class="row-left">
                <span class="template-name">{{ item.name }}</span>
                <span
                  v-if="item.action"
                  class="action-tag"
                  :class="getActionClass(item.action.handle)"
                >
                  {{ item.action.hname }}
                </span>
              </div>
              <div class="row-right">
                <div
                  v-if="item.tag"
                  class="template-tag"
                  :style="{ background: item.tag.color }"
                >
                  {{ item.tag.name }}
                </div>
                <van-icon name="arrow" size="16" class="edit-arrow" />
              </div>
            </div>

            <!-- 金额（如果有） -->
            <div v-if="item.money" class="money-display">
              <span class="money-symbol">¥</span>
              <span class="money-value">{{ item.money }}</span>
            </div>
          </div>

          <!-- 抽屉展开按钮 -->
          <div
            v-if="hasDetails(item)"
            class="drawer-toggle"
            @click="toggleExpand(item.id, $event)"
          >
            <span class="toggle-text">{{ expandedIds.includes(item.id) ? '收起详情' : '展开详情' }}</span>
            <van-icon :name="expandedIds.includes(item.id) ? 'arrow-up' : 'arrow-down'" size="14" />
          </div>

          <!-- 抽屉内容 -->
          <div v-show="expandedIds.includes(item.id)" class="drawer-content">
            <!-- 账户信息 -->
            <div v-if="item.account?.name && item.accountTo?.name" class="detail-row">
              <span class="detail-label">转账</span>
              <span class="detail-value transfer">{{ item.account.name }} → {{ item.accountTo.name }}</span>
            </div>
            <div v-else-if="item.account?.name" class="detail-row">
              <span class="detail-label">账户</span>
              <span class="detail-value">{{ item.account.name }}</span>
            </div>

            <!-- 分类 -->
            <div v-if="item.type?.tname" class="detail-row">
              <span class="detail-label">分类</span>
              <span class="detail-value">{{ item.type.tname }}</span>
            </div>

            <!-- 日期类型 -->
            <div v-if="item.dateType !== undefined && item.dateType !== null" class="detail-row">
              <span class="detail-label">日期</span>
              <span class="detail-value">{{ item.dateType === 1 ? '补上月' : '记本月' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <van-empty v-if="!loading && !templates.length" description="暂无模板" />
    </div>
  </div>
</template>

<style scoped>
.template-page {
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

/* 筛选卡片 */
.filter-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: var(--color-bg-card);
  border-radius: 14px;
  margin-bottom: 16px;
}

.filter-card:active {
  opacity: 0.8;
}

.filter-left {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 15px;
  color: var(--color-text-primary);
}

.filter-right {
  display: flex;
  align-items: center;
  color: var(--color-text-tertiary);
}

.selected-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: 8px;
  font-size: 13px;
  color: #fff;
}

/* 标签面板 */
.tag-panel {
  background: var(--color-bg-card);
  border-radius: 14px;
  padding: 16px;
  margin-bottom: 16px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tag-item {
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 13px;
  color: #fff;
  font-weight: 500;
}

.tag-item:active {
  opacity: 0.8;
}

.no-tags {
  text-align: center;
  font-size: 14px;
  color: var(--color-text-tertiary);
  padding: 20px 0;
}

/* 模板列表 */
.template-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 模板卡片 */
.template-card {
  background: var(--color-bg-card);
  border-radius: 16px;
  overflow: hidden;
}

/* 卡片主体 */
.card-main {
  padding: 16px 20px;
}

.card-main:active {
  background: var(--color-bg-page);
}

.card-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.row-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.template-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.action-tag {
  flex-shrink: 0;
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

.row-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
  margin-left: 12px;
}

.template-tag {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  color: #fff;
  font-weight: 500;
}

.edit-arrow {
  color: var(--color-text-tertiary);
}

/* 金额显示 */
.money-display {
  display: flex;
  align-items: baseline;
  gap: 2px;
  margin-top: 12px;
}

.money-symbol {
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.money-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: -0.5px;
}

/* 抽屉展开按钮 */
.drawer-toggle {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 6px;
  padding: 10px;
  border-top: 1px solid var(--color-border-light);
  color: var(--color-text-tertiary);
  font-size: 13px;
}

.drawer-toggle:active {
  background: var(--color-bg-page);
}

/* 抽屉内容 */
.drawer-content {
  padding: 0 20px 16px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
}

.detail-row:not(:last-child) {
  border-bottom: 1px solid var(--color-border-light);
}

.detail-label {
  font-size: 14px;
  color: var(--color-text-tertiary);
}

.detail-value {
  font-size: 14px;
  color: var(--color-text-primary);
}

.detail-value.transfer {
  color: var(--color-transfer);
}
</style>

<!-- 非 scoped 样式 -->
<style>
.template-page .page-header {
  background: rgba(245, 245, 245, 0.8);
}

html.dark .template-page .page-header {
  background: rgba(10, 10, 10, 0.8);
}
</style>
